import unittest
from ember_spares import run_binance_usdm,BinanceUSDMPublic

class DirectIntegration(unittest.TestCase):
    def test_full_source_flow(self):
        begin=1_700_000_000_000
        def fake(path,params,timeout):
            if path in ('/fapi/v1/klines','/fapi/v1/markPriceKlines'):
                return [[begin+i*60_000,'100','101','99','100','100',begin+(i+1)*60_000-1,'0',10,'42','0','0'] for i in range(30)]
            if path=='/fapi/v1/fundingRate':
                return [{'fundingTime':begin+i*60_000,'fundingRate':str(.0002+i*.000001)} for i in range(15)]
            if path=='/futures/data/openInterestHist':
                return [{'timestamp':begin+i*60_000,'sumOpenInterest':str(2000+i)} for i in range(30)]
            raise ValueError('unexpected path')
        client=BinanceUSDMPublic(transport=fake)
        result=run_binance_usdm(symbol='SOLUSDT',interval='1m',start_ms=begin,end_ms=begin+30*60_000,
                                 decision_at=(begin+31*60_000)//1000,funding_lag_ms=0,oi_lag_ms=0,
                                 client=client,lookback=20)
        self.assertEqual(result['status'],'SOURCE_COMPLETE')
        self.assertAlmostEqual(result['features']['Z22']['value']['buy_ratio'],.42)
        self.assertEqual(result['features']['Z01']['value']['oi'],2029.)
        self.assertTrue(result['no_trade_execution'])
    def test_insufficient_oi_degrades_without_spot(self):
        begin=1_700_000_000_000
        def fake(path,params,timeout):
            if path=='/fapi/v1/klines':
                return [[begin,'100','101','99','100','100',begin+59999,'0',10,'42','0','0']]
            if path=='/fapi/v1/markPriceKlines':
                return [[begin,'100','101','99','100','0',begin+59999,'0',10,'0','0','0']]
            raise OSError('geo 451')
        r=run_binance_usdm(symbol='SOLUSDT',interval='1m',start_ms=begin,end_ms=begin+60000,
                           decision_at=(begin+80000)//1000, funding_lag_ms=1000, oi_lag_ms=1000,
                           client=BinanceUSDMPublic(transport=fake))
        self.assertEqual(r['status'],'PARTIAL_SOURCE')
        self.assertIn('oi',r['missing'])
        self.assertFalse(r['features']['Z01']['value']['valid_for_oi_funding_signal'])
