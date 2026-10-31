import json
import hashlib
import unittest
from ember_spares.extra import detect_patterns,ott_line,efficiency_weighted_ema,predict_verified_linear,check_train_holdout
from ember_spares.signals import ModelContract
from ember_spares.types import Candle


def c(i, low, high, close=100):
    openp=100
    if close>high or close<low:raise ValueError('bad test')
    return Candle(i*60,(i+1)*60,openp,high,low,close,10,(i+1)*60)

class ExtraTests(unittest.TestCase):
    def test_ott_offline(self):
        values=[100+i*.5 for i in range(40)]
        result=ott_line(values,period=9)
        self.assertEqual(len(result),40)
        self.assertTrue(all(v is None for v in result[:9]))
        self.assertTrue(all(v>0 for v in result[9:]))
        with self.assertRaises(ValueError):ott_line(values,percent=-1)

    def test_patterns_do_not_use_future(self):
        candles=[c(i,95,105) for i in range(20)]
        self.assertEqual(detect_patterns(candles,decision_at=100),[])
        self.assertEqual(detect_patterns(candles,decision_at=1200),[])
        with self.assertRaises(ValueError):detect_patterns(candles,decision_at=1200,tolerance=-1)
        with self.assertRaises(ValueError):detect_patterns(candles+[candles[-1]],decision_at=99999)

    def test_linear_model_verified(self):
        payload=json.dumps({'version':1,'weights':{'a':.3,'b':.2},'intercept':-.1},sort_keys=True).encode()
        contract=ModelContract('example',hashlib.sha256(payload).hexdigest(),100,('a','b'),.6)
        score=predict_verified_linear(contract,payload,{'a':1.,'b':2.},at=101)
        self.assertGreater(score,.6)
        with self.assertRaises(ValueError):predict_verified_linear(contract,payload,{'a':1.,'b':2.},at=100)
        with self.assertRaises(ValueError):predict_verified_linear(contract,payload+b' ',{'a':1.,'b':2.},at=101)
        with self.assertRaises(ValueError):predict_verified_linear(contract,payload,{'a':1.,'b':2.,'c':3.},at=101)

    def test_embargo(self):
        check_train_holdout(100,120,19)
        with self.assertRaises(ValueError):check_train_holdout(100,120,20)

if __name__=='__main__':unittest.main()
