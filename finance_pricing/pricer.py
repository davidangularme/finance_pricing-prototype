"""Replayable price enclosures for a two-asset European basket call.
Fixed risk-neutral Black-Scholes model, no dividends, 0 <= correlation <= 1.
Python 3.10+ and python-flint==0.8.0. Research prototype; MIT.
"""
import argparse
from fractions import Fraction as F
import heapq
import json
import math
from statistics import NormalDist
import time
import flint
from flint import arb,ctx

FORMAT='basket-price-enclosure-0.1'
BITS=128

def rational(v):
    if type(v) not in (int,str): raise ValueError('Use rational strings or integers for model inputs')
    return F(v)
def ball(v):
    x=F(v);return arb(x.numerator)/arb(x.denominator)
def exact_endpoint(x):
    m,e=x.man_exp();m,e=int(m),int(e)
    return F(m*(1<<e)) if e>=0 else F(m,1<<(-e))
def ends(x):
    if not x.is_finite(): raise ArithmeticError('Nonfinite enclosure')
    return exact_endpoint(x.lower()),exact_endpoint(x.upper())
def outward(lo,hi):
    scale=1<<64
    return F((lo.numerator*scale)//lo.denominator,scale),F(-((-hi.numerator*scale)//hi.denominator),scale)
def cdf(x): return (-x/arb(2).sqrt()).erfc()/2

def validate(model):
    expected={'model','spot1','spot2','weight1','weight2','vol1','vol2','correlation','rate','maturity','strike'}
    if set(model)!=expected or model['model']!='two_asset_lognormal_call_no_dividends':
        raise ValueError('Unsupported model or unexpected/missing fields')
    m={k:rational(v) for k,v in model.items() if k!='model'}
    if any(m[k]<=0 for k in ('spot1','spot2','maturity','strike')): raise ValueError('Spots, maturity and strike must be positive')
    if any(m[k]<0 for k in ('vol1','vol2','weight1','weight2')): raise ValueError('Volatilities and weights must be nonnegative')
    if m['weight1']+m['weight2']!=1: raise ValueError('Weights must sum to one')
    if not 0<=m['correlation']<=1: raise ValueError('Prototype supports only nonnegative correlations')
    return m

class Model:
    def __init__(self,model):
        ctx.prec=BITS
        self.raw=validate(model);p={k:ball(v) for k,v in self.raw.items()}
        self.p=p; t=p['maturity'];self.v1=p['vol1']*t.sqrt();self.v2=p['vol2']*t.sqrt()
        self.rho=p['correlation'];self.b=self.v2*(1-self.rho**2).sqrt()
        self.a0=p['weight1']*p['spot1']*((p['rate']-p['vol1']**2/2)*t).exp()
        self.b0=p['weight2']*p['spot2']*((p['rate']-p['vol2']**2/2)*t).exp()
        self.discount=(-p['rate']*t).exp()
        self.cache={}
    def conditional(self,z):
        if z in self.cache:return self.cache[z]
        p=self.p;zball=ball(z);A=self.a0*(self.v1*zball).exp();B=self.b0*(self.v2*self.rho*zball).exp()
        H=p['strike']-A
        if self.raw['weight2']==0 or self.raw['vol2']==0 or self.raw['correlation']==1:
            lo,hi=ends((A+B-p['strike'])*self.discount);result=(max(F(0),lo),max(F(0),hi))
        else:
            forward=B*(self.b**2/2).exp()
            hlo,hhi=ends(H)
            if hhi<=0:
                value=(forward-H)*self.discount;lo,hi=ends(value)
            elif hlo>0:
                d2=(B/H).log()/self.b;d1=d2+self.b
                value=(forward*cdf(d1)-H*cdf(d2))*self.discount;lo,hi=ends(value)
            else:
                # If rounding straddles H=0, use elementary payoff bounds.
                a,b=ends(forward);lo,hi=ends((ball(max(F(0),a-hhi)).union(ball(b+max(F(0),-hlo))))*self.discount)
            result=max(F(0),lo),max(F(0),hi)
        self.cache[z]=result;return result
    def mass(self,a,b):
        x=cdf(ball(b))-cdf(ball(a));lo,hi=ends(x)
        return max(F(0),lo),max(F(0),hi)
    def block(self,a,b):
        # Conditional payoff is nondecreasing in z for nonnegative correlation and weights.
        lo=self.conditional(a)[0];hi=self.conditional(b)[1];ml,mh=self.mass(a,b)
        return outward(lo*ml,hi*mh)
    def tail(self,L):
        # Exponential tilting; both tails of the remaining standard normal factor.
        p=self.p;L=ball(L);out=arb(0)
        for w,s,v in [(p['weight1'],p['spot1'],self.v1),(p['weight2'],p['spot2'],self.v2*self.rho)]:
            out+=w*s*(cdf(-L-v)+cdf(v-L))
        return max(F(0),ends(out)[1])
    def vanilla_reference(self):
        if self.raw['weight2']!=0: raise ValueError('Reference applies only to weight1=1')
        p=self.p;v=self.v1
        if self.raw['vol1']==0: val=(p['spot1']-p['strike']*self.discount).max(0)
        else:
            d1=((p['spot1']/p['strike']).log()+p['rate']*p['maturity']+v**2/2)/v
            val=p['spot1']*cdf(d1)-p['strike']*self.discount*cdf(d1-v)
        return ends(val)

def price(model,tolerance='1/100',max_leaves=20000,truncation=6):
    tol=rational(tolerance);L=rational(truncation)
    if tol<=0 or L<=0 or type(max_leaves) is not int or max_leaves<1:raise ValueError('Invalid calculation settings')
    start=time.perf_counter();m=Model(model);tail=m.tail(L)
    lo,hi=m.block(-L,L);leaves={'':(-L,L,lo,hi)};heap=[(-(hi-lo),'')];evaluations=1
    while hi+tail-lo>2*tol and len(leaves)<max_leaves:
        if tail>2*tol: break # The chosen truncation cannot meet the requested tolerance.
        _,path=heapq.heappop(heap);a,b,oldlo,oldhi=leaves.pop(path);mid=(a+b)/2;lo-=oldlo;hi-=oldhi
        for label,(u,v) in enumerate(((a,mid),(mid,b))):
            l,h=m.block(u,v);key=path+str(label);leaves[key]=(u,v,l,h)
            lo+=l;hi+=h;heapq.heappush(heap,(-(h-l),key));evaluations+=1
    status='tolerance_met' if hi+tail-lo<=2*tol else ('truncation_too_small' if tail>2*tol else 'budget_exhausted')
    cert={'format':FORMAT,'precision_bits':BITS,'model':model,'tolerance':str(tol),'truncation':str(L),
          'leaf_paths':sorted(leaves),'interior_lower':str(lo),'interior_upper':str(hi),'tail_upper':str(tail),
          'price_lower':str(lo),'price_upper':str(hi+tail),'status':status}
    stats={'seconds':time.perf_counter()-start,'leaves':len(leaves),'block_evaluations':evaluations,
           'conditional_evaluations':len(m.cache),'midpoint_display':float((lo+hi+tail)/2),
           'error_bound_display':float((hi+tail-lo)/2),'tail_upper_display':float(tail),'status':status}
    return cert,stats

def verify(cert):
    if cert.get('format')!=FORMAT or cert.get('precision_bits')!=BITS:raise ValueError('Unsupported certificate')
    tol,L=rational(cert['tolerance']),rational(cert['truncation'])
    if tol<=0 or L<=0:raise ValueError('Invalid settings')
    raw=cert['leaf_paths']
    if not raw or len(raw)>1000000 or any(type(p) is not str or len(p)>100 or any(c not in '01' for c in p) for p in raw):raise ValueError('Invalid partition')
    paths=set(raw)
    if len(paths)!=len(raw):raise ValueError('Duplicate leaves')
    prefixes={p[:i] for p in paths for i in range(len(p))};m=Model(cert['model'])
    def visit(path,a,b):
        if path in paths:
            if path in prefixes:raise ValueError('Overlapping leaves')
            return m.block(a,b)
        if path not in prefixes:raise ValueError('Partition has a hole')
        mid=(a+b)/2;l=visit(path+'0',a,mid);r=visit(path+'1',mid,b)
        return l[0]+r[0],l[1]+r[1]
    lo,hi=visit('',-L,L);tail=m.tail(L)
    for key,value in [('interior_lower',lo),('interior_upper',hi),('tail_upper',tail),('price_lower',lo),('price_upper',hi+tail)]:
        if rational(cert[key])!=value:raise ValueError('Incorrect '+key)
    status='tolerance_met' if hi+tail-lo<=2*tol else ('truncation_too_small' if tail>2*tol else 'budget_exhausted')
    if cert['status']!=status:raise ValueError('False completion status')
    return {'verified':True,'status':status,'price_lower':str(lo),'price_upper':str(hi+tail),
            'midpoint':str((lo+hi+tail)/2),'absolute_error_bound':str((hi+tail-lo)/2)}

def check_quote(cert,quote):
    verify(cert);q=rational(quote);lo,hi=rational(cert['price_lower']),rational(cert['price_upper'])
    if q<lo:return 'below_model_interval'
    if q>hi:return 'above_model_interval'
    return 'inside_model_interval_not_proof_of_market_fairness'

def estimate(model,n=4096,method='r2'):
    p={k:float(v) for k,v in validate(model).items()};normal=NormalDist();s=0.
    rho=1.324717957244746
    def radical(i,b):
        out=0.;v=1.
        while i:i,r=divmod(i,b);v/=b;out+=v*r
        return out
    for i in range(1,n+1):
        if method=='r2':u,v=(.5+i/rho)%1,(.5+i/rho**2)%1
        elif method=='halton':u,v=radical(i,2),radical(i,3)
        else:raise ValueError('Unsupported sampler')
        z1,z2=normal.inv_cdf(u),normal.inv_cdf(v);t=p['maturity'];cor=p['correlation']
        st1=p['spot1']*math.exp((p['rate']-.5*p['vol1']**2)*t+p['vol1']*math.sqrt(t)*z1)
        st2=p['spot2']*math.exp((p['rate']-.5*p['vol2']**2)*t+p['vol2']*math.sqrt(t)*(cor*z1+math.sqrt(1-cor*cor)*z2))
        s+=max(p['weight1']*st1+p['weight2']*st2-p['strike'],0.)
    return math.exp(-p['rate']*p['maturity'])*s/n

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',nargs='?');p.add_argument('--verify');p.add_argument('--quote')
    p.add_argument('--tolerance',default='1/100');p.add_argument('--max-leaves',type=int,default=20000);p.add_argument('--truncation',default='6');p.add_argument('--output',default='price_certificate.json')
    a=p.parse_args()
    if a.verify:
        with open(a.verify) as f:c=json.load(f)
        print(json.dumps(verify(c),indent=2))
        if a.quote is not None:print(check_quote(c,a.quote))
        return
    if not a.model:p.error('Supply a model JSON or --verify certificate.json')
    with open(a.model) as f:model=json.load(f)
    c,stats=price(model,a.tolerance,a.max_leaves,a.truncation)
    with open(a.output,'w') as f:json.dump(c,f,indent=2)
    print(json.dumps(stats,indent=2))
    if c['status']!='tolerance_met':raise SystemExit(2)
if __name__=='__main__':main()
