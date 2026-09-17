from pricer import *
from pathlib import Path
BASE=Path(__file__).resolve().parent
m=json.loads((BASE/'examples/basket.json').read_text());rows=[]
for label,model in [('baseline',m),('vol1_minus_one_point',dict(m,vol1='19/100')),('vol1_plus_one_point',dict(m,vol1='21/100'))]:
    c,stats=price(model,'1/100');t=time.perf_counter();verify(c);stats['replay_seconds']=time.perf_counter()-t
    (BASE/(label+'_certificate.json')).write_text(json.dumps(c,indent=2))
    samples=[]
    for method in ('r2','halton'):
        for n in (1024,4096,16384):
            start=time.perf_counter();value=estimate(model,n,method)
            samples.append({'method':method,'n':n,'price_estimate':value,'seconds':time.perf_counter()-start,'certified':False})
    rows.append({'label':label,'model':model,'statistics':stats,'price_lower':c['price_lower'],'price_upper':c['price_upper'],'samples':samples})
(BASE/'benchmark_results.json').write_text(json.dumps({'results':rows,'scope':'Synthetic fixed models. Single-run local wall times, not a competitive benchmark. Scenario prices are not a confidence interval for market or model uncertainty.'},indent=2))
print(json.dumps([{k:r[k] for k in ('label','statistics')} for r in rows],indent=2))
