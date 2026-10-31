import unittest
from ember_spares.types import Candle
from ember_spares.structure import (
    Zone, advance_zone, Rule, evaluate_rules, CompressionState, advance_compression,
    confirmed_pivots, double_top, fvg_channel, failed_breakout,
    HysteresisRegime, advance_regime, weighted_ma, hull_ma, supertrend, fibonacci_retracement,
)


def candle(o=100,h=105,l=95,c=100,t=0):
    return Candle(t,t+60,o,h,l,c,10,t+60)


class StructureTests(unittest.TestCase):
    def test_zone_visits_and_break(self):
        z=Zone('d','demand',90,100,0)
        z=advance_zone(z,candle(t=61))
        self.assertEqual((z.phase,z.touches),('TESTED',1))
        z=advance_zone(z,candle(t=121))
        self.assertEqual(z.touches,1)
        z=advance_zone(z,candle(110,120,105,115,181))
        z=advance_zone(z,candle(t=241))
        self.assertEqual(z.touches,2)
        z=advance_zone(z,candle(91,93,80,85,301))
        self.assertEqual(z.phase,'BROKEN')
        z=advance_zone(z,candle(85,98,83,94,361))
        self.assertEqual(z.phase,'FLIPPED')

    def test_rule_future_is_not_visible(self):
        candles=[candle(t=0),candle(102,104,101,103,t=60)]
        rule=Rule('close','>=',101)
        self.assertFalse(evaluate_rules(candles,[rule],60))
        self.assertTrue(evaluate_rules(candles,[rule],120))
        self.assertFalse(evaluate_rules(candles,[Rule('close','>=',101,offset=1)],120))
        with self.assertRaises(ValueError): Rule('close','>',0,offset=-1)

    def test_compression_restart(self):
        s=CompressionState()
        s=advance_compression(s,candle(t=0),is_compressed=True,compressed_range=(95,105))
        self.assertEqual(s.phase,'COMPRESSED')
        s=advance_compression(s,candle(105,110,104,108,60))
        self.assertEqual((s.phase,s.direction),('BREAKOUT','long'))
        s=advance_compression(s,candle(107,109,98,100,120))
        self.assertEqual(s.phase,'FAILED')
        s=advance_compression(s,candle(103,110,102,109,180))
        self.assertEqual(s.phase,'RESTART')

    def test_confirmed_pivot_does_not_anticipate(self):
        highs=[100,102,104,101,99]
        candles=[candle(o=95,h=h,l=90,c=95,t=i*60) for i,h in enumerate(highs)]
        p=confirmed_pivots(candles,2,2)
        self.assertEqual(len([x for x in p if x.kind=='high']),1)
        self.assertEqual([x for x in p if x.kind=='high'][0].confirmed_at,300)
        self.assertFalse(confirmed_pivots(candles,2,2,decision_at=299))

    def test_fvg_midpoints_no_future(self):
        rows=[candle(100,102,99,101,t=0),candle(103,105,102,104,t=60),candle(108,111,107,110,t=120)]
        f=fvg_channel(rows)
        self.assertEqual(f.bull_count,1)
        self.assertAlmostEqual(f.bull_mid,104.5)
        self.assertIsNone(f.bear_mid)

    def test_failed_break(self):
        self.assertTrue(failed_breakout(candle(100,111,99,108,t=0),candle(108,109,99,100,t=60),105,'long'))
        self.assertFalse(failed_breakout(candle(100,111,99,108,t=0),candle(108,112,107,110,t=60),105,'long'))
        with self.assertRaises(ValueError): failed_breakout(candle(t=60),candle(t=0),105,'long')

    def test_regime_persistence(self):
        r=HysteresisRegime()
        r=advance_regime(r,1,persistence=3)
        self.assertEqual(r.state,'range')
        r=advance_regime(r,1,persistence=3)
        self.assertEqual(r.state,'range')
        r=advance_regime(r,1,persistence=3)
        self.assertEqual(r.state,'up')
        r=advance_regime(r,.5,persistence=3)
        self.assertEqual(r.state,'up')
        for _ in range(3): r=advance_regime(r,.2,persistence=3)
        self.assertEqual(r.state,'range')
        with self.assertRaises(ValueError): advance_regime(r,1,enter_threshold=.2,exit_threshold=.4)

    def test_hma_and_supertrend_warmup(self):
        values=list(range(1,51))
        h=hull_ma(values,9)
        self.assertEqual(len(h),len(values))
        self.assertIsNone(h[4])
        self.assertIsNotNone(h[-1])
        rows=[candle(100+i,105+i,95+i,101+i,t=i*60) for i in range(15)]
        st=supertrend(rows,period=5)
        self.assertEqual(len(st),15)
        self.assertEqual(st[0],(None,0))
        self.assertNotEqual(st[-1][0],None)
        with self.assertRaises(ValueError): hull_ma(values,1)

    def test_fib_geometry(self):
        p=fibonacci_retracement(100,200,'long',atr=2)
        self.assertAlmostEqual(p.entry1,121)
        self.assertAlmostEqual(p.entry2,112)
        self.assertAlmostEqual(p.stop,98)
        s=fibonacci_retracement(100,200,'short',atr=2)
        self.assertAlmostEqual(s.entry1,179)
        self.assertAlmostEqual(s.stop,202)
        with self.assertRaises(ValueError): fibonacci_retracement(200,100,'long')

if __name__=='__main__': unittest.main()
