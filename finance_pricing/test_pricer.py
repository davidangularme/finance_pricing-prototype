from pricer import *
from pathlib import Path
import copy
import unittest
BASE=Path(__file__).resolve().parent
BASE_MODEL=json.loads((BASE/'examples/basket.json').read_text())
class Tests(unittest.TestCase):
    def test_vanilla_closed_form(self):
        m=dict(BASE_MODEL,weight1='1',weight2='0')
        c,_=price(m,'1/100');verify(c);lo,hi=Model(m).vanilla_reference()
        self.assertLessEqual(F(c['price_lower']),lo)
        self.assertGreaterEqual(F(c['price_upper']),hi)
    def test_deterministic_case(self):
        m=dict(BASE_MODEL,vol1='0',vol2='0')
        c,_=price(m,'1/100000');verify(c)
        reference=arb(100)-arb(100)*(-arb(3)/100).exp()
        lo,hi=ends(reference)
        self.assertLessEqual(F(c['price_lower']),lo);self.assertGreaterEqual(F(c['price_upper']),hi)
    def test_perfect_correlation_equal_vols(self):
        m=dict(BASE_MODEL,correlation='1',vol2=BASE_MODEL['vol1'])
        c,_=price(m,'1/100');verify(c)
        lo,hi=Model(dict(m,weight1='1',weight2='0')).vanilla_reference()
        self.assertLessEqual(F(c['price_lower']),lo);self.assertGreaterEqual(F(c['price_upper']),hi)
    def test_second_asset_only(self):
        m=dict(BASE_MODEL,weight1='0',weight2='1')
        c,_=price(m,'1/100');verify(c)
        lo,hi=Model(dict(m,weight1='1',weight2='0',vol1=m['vol2'])).vanilla_reference()
        self.assertLessEqual(F(c['price_lower']),lo);self.assertGreaterEqual(F(c['price_upper']),hi)
    def test_tampering(self):
        c,_=price(BASE_MODEL,'1/10',2000)
        for key,val in [('price_upper','0'),('tail_upper','0'),('interior_lower','100')]:
            d=copy.deepcopy(c);d[key]=val
            with self.assertRaises(ValueError):verify(d)
        d=copy.deepcopy(c);d['leaf_paths'].pop()
        with self.assertRaises(ValueError):verify(d)
        d=copy.deepcopy(c);d['leaf_paths'].append(d['leaf_paths'][0])
        with self.assertRaises(ValueError):verify(d)
        d=copy.deepcopy(c);d['leaf_paths'].append('')
        with self.assertRaises(ValueError):verify(d)
    def test_failures(self):
        c,_=price(BASE_MODEL,'1/10000',1);self.assertEqual(c['status'],'budget_exhausted');verify(c)
        d=copy.deepcopy(c);d['status']='tolerance_met'
        with self.assertRaises(ValueError):verify(d)
        c,_=price(BASE_MODEL,'1/100',100,1);self.assertEqual(c['status'],'truncation_too_small');verify(c)
    def test_model_validation(self):
        for key,val in [('correlation','-1/2'),('weight1','2'),('vol1','-1'),('maturity','0'),('spot1',100.0)]:
            with self.assertRaises(ValueError):price(dict(BASE_MODEL,**{key:val}))
    def test_tail_and_monotonicity(self):
        m=Model(BASE_MODEL);self.assertLess(m.tail(7),m.tail(6))
        for z in range(-5,5):self.assertLessEqual(m.conditional(F(z))[1],m.conditional(F(z+1))[0])
    def test_quote_check(self):
        c,_=price(BASE_MODEL,'1/10',2000)
        self.assertEqual(check_quote(c,'0'),'below_model_interval')
        self.assertEqual(check_quote(c,'100'),'above_model_interval')
        self.assertTrue(check_quote(c,str((F(c['price_lower'])+F(c['price_upper']))/2)).startswith('inside'))
if __name__=='__main__':unittest.main(verbosity=2)
