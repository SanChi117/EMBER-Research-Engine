import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ember_spares import invoke, manifest, SpareInputError
from ember_spares.accounting import RiskState, save_risk_state
from ember_spares.plugin import main
from ember_spares.binance import parse_book_ticker, parse_funding, parse_kline, parse_klines, parse_oi


def bar(t=0, o=100., h=105., l=95., c=102., v=100.):
    return dict(open_time=t, close_time=t+60, open=o, high=h, low=l, close=c, volume=v, available_at=t+60)


def flat_bars(n=20):
    return [bar(i*60, o=100+(i%3), h=103+(i%3), l=97+(i%3), c=100.5+(i%3)) for i in range(n)]


def basic():
    return [bar(0, h=105, l=98, c=102), bar(60, h=104, l=95, c=97), bar(120, h=102, l=96, c=100)]


class PlugAndPlay(unittest.TestCase):
    def test_manifest_complete(self):
        items = manifest()
        self.assertEqual(len(items), 42)
        self.assertEqual(len({x["id"] for x in items}),42)
        self.assertNotIn('Z12', {x['id'] for x in items})
        self.assertTrue(all(x in {y['id'] for y in items} for x in ('Z15.patterns','Z19.ott','Z27.predict_linear')))

    def test_all_components_resolve_and_have_exact_signature(self):
        from ember_spares.plugin import _resolve
        for item in manifest():
            with self.subTest(id=item['id']):
                self.assertTrue(callable(_resolve(item['id'])))
        with self.assertRaises(SpareInputError):
            invoke('Z12', {})

    def test_real_market_ambiguity(self):
        self.assertEqual(invoke('Z09', {'bar':bar(), 'side':'long','stop':96,'target':104}), 'AMBIGUOUS')
        with self.assertRaises(SpareInputError):
            invoke('Z09', {'bar':bar(), 'side':'long','stop':96,'target':104}, decision_at=59)
        self.assertEqual(invoke('Z09', {'bar':bar(), 'side':'long','stop':96,'target':104}, decision_at=60), 'AMBIGUOUS')
        with self.assertRaises(SpareInputError):
            invoke('Z09', {'bar':bar(), 'side':'long','stop':96,'target':104,'weird_extra':True})

    def test_book_and_taker(self):
        self.assertEqual(invoke('Z03', {'book':{'bid':100,'ask':102,'bid_quantity':30,
                                    'ask_quantity':10,'exchange_time':10,'available_at':11}}),101.5)
        self.assertEqual(invoke('Z22', {'buy_volume':[1,3],'total_volume':[2,4]}), 2/3)
        with self.assertRaises(SpareInputError):
            invoke('Z03', {'book':{'bid':100,'ask':102,'bid_quantity':30,
                                    'ask_quantity':10,'exchange_time':10,'available_at':11}},decision_at=10)

    def test_traces_and_research(self):
        orig=[{'decision_at':60, 'symbol':'BTC','side':'long','entry':100.,'stop':90.,'target':120.,'source':'original'}]
        copy=[{'decision_at':60, 'symbol':'BTC','side':'long','entry':100.,'stop':90.,'target':121.,'source':'replica'}]
        r=invoke('Z04',{'original':orig,'challenger':copy})
        self.assertEqual(r[0]['difference'],'target')
        self.assertEqual(invoke('Z30',{'raw_pvalue':0.01,'trial_count':5}),.05)

    def test_funding_point_in_time(self):
        x={'funding':[{'event_time':100,'available_at':150,'value':.01,'source':'Binance'},
                      {'event_time':200,'available_at':250,'value':.02,'source':'Binance'}]}
        result=invoke('Z01',{'streams':x},decision_at=170)
        self.assertEqual(result['funding']['value'],.01)
        self.assertEqual(invoke('Z01',{'streams':x},decision_at=120)['funding'],None)

    def test_structural(self):
        v=invoke('Z16',{'candles':flat_bars(12), 'lookback':12})
        self.assertIn('bull_count',v)
        self.assertIn('bear_count',v)
        self.assertIsInstance(invoke('Z19',{'values':list(range(1,35)),'window':10}),list)
        self.assertTrue(invoke('Z17',{'previous':bar(0,c=102),'current':bar(60,c=99),'level':100,'side':'long'}))

    def test_cash_and_risk(self):
        events=[{'event_id':'1','sequence':1,'action':'OPEN','quantity':2.,'price':100.,'fee':.1},
                {'event_id':'2','sequence':2,'action':'REDUCE','quantity':1.,'price':110.,'fee':.1}]
        p=invoke('Z06',{'symbol':'BTC','side':'long','events':events})
        self.assertEqual(p['quantity'],1)
        self.assertEqual(p['realised_pnl'],10)
        z=invoke('Z07',{'exposures':[],'new':{'strategy':'x','symbol':'BTC','direction':'long',
              'stop_risk_usdt':10.,'notional_usdt':500.},'max_total_stop_risk':100.,'max_symbol_notional':1000.})
        self.assertEqual(z,[True,'OK'])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'risk.json'
            save_risk_state(path,RiskState('2026-11-01','2026-W44',0.,0.,0,True))
            r=invoke('Z08',{'path':str(path)})
            self.assertTrue(r['halted'])

    def test_binance_ms_parser(self):
        epoch=1761955200000
        k=[epoch,'100','105','95','102','300',epoch+59999,'','', '', '', '']
        c=parse_kline(k)
        self.assertEqual(c.close_time,c.open_time+60)
        self.assertEqual(c.available_at,c.close_time)
        self.assertEqual(invoke('Z09',{'bar':k,'side':'long','stop':96.,'target':104.}), 'AMBIGUOUS')
        self.assertEqual(len(parse_klines([k])),1)
        with self.assertRaises(ValueError):parse_klines([k,k])
        with self.assertRaises(ValueError):parse_kline({'k':{'x':False}})
        funding=parse_funding({'fundingTime':epoch,'fundingRate':'0.0001'},publication_lag_ms=500)
        self.assertEqual(funding.value,.0001)
        self.assertEqual(funding.available_at,funding.event_time+1)
        oi=parse_oi({'timestamp':epoch,'sumOpenInterest':'135.3'},publication_lag_ms=1000)
        self.assertEqual(oi.value,135.3)
        bk=parse_book_ticker({'T':epoch,'a':'102','b':'100','A':'10','B':'30'}, receive_ms=epoch+50)
        self.assertEqual(bk.available_at,bk.exchange_time+1)

    def test_native_cli_without_broker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json'
            path.write_text(json.dumps({'buy_volume':[1,3],'total_volume':[2,4]}))
            out=StringIO()
            with redirect_stdout(out):
                code=main(['Z22',str(path)])
            self.assertEqual(code,0)
            result=json.loads(out.getvalue())
            self.assertEqual(result['result'],2/3)
            self.assertTrue(result['ok'])
            with redirect_stdout(StringIO()):
                self.assertEqual(main(['list']),0)

    def test_unicode_and_nonfinite_handling(self):
        with self.assertRaises(SpareInputError):
            invoke('Z22',{'buy_volume':['wat'],'total_volume':[2.]})
        with self.assertRaises(SpareInputError):
            invoke('Z30',{'raw_pvalue':float('nan'),'trial_count':1})
        with self.assertRaises(SpareInputError):
            invoke('Z30',{'raw_pvalue':.1,'trial_count':1},decision_at=-1)


if __name__=='__main__':unittest.main()
