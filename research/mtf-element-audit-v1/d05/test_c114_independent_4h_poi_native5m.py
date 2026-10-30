"""C114 independent source and no-peeking source-contract negative tests."""
import unittest
from decimal import Decimal as D
from types import SimpleNamespace as NS
from c90_structural_fta_backtest import Swing
from c89_original_native5m_adaptation_backtest import Bar
import c114_independent_poi_native5m_choch_research as x

F=x.FIVE
H=x.H
def pivot(kind,price,known):
    return Swing(F,kind,D(str(price)),known-2*F,known,2)

def sample_swings(side):
    if side=="LONG":
        return (pivot("HIGH",110,3*F),pivot("LOW",97,4*F),
                pivot("HIGH",105,6*F),pivot("LOW",93,7*F))
    return (pivot("HIGH",100,3*F),pivot("LOW",90,4*F),
            pivot("HIGH",106,6*F),pivot("LOW",96,7*F))

def candle(start,open_,high,low,close):
    return Bar(start,D(str(open_)),D(str(high)),D(str(low)),D(str(close)),D(1))

def event(symbol="BNBUSDT",kind="T_CHoCH",risk="RISK_1_TO_3_REWARD_2_TO_4",pnum=1):
    e={"symbol":symbol,"t0_touch_known_ms":pnum*F,
       "parent_id":str(pnum),"side":"LONG","range_class":"DISCOUNT",
       "risk_bin":risk,"treatment":kind,"matched_id":None}
    e["trade"]={"entry":"100","stop":"98","target":"106","net_r":1.0,
                "entry_ms":pnum*F,"exit_ms":(pnum+2)*F,
                "exit_reason":"4H_STRUCTURAL_FTA","side":"LONG","symbol":symbol,
                "parent_id":str(pnum)}
    return e

class C114NegativeContracts(unittest.TestCase):
    def test_pre_touch_downtrend_is_confirmed_2x_high_low(self):
        self.assertEqual(x.five_pre_touch_structure(sample_swings("LONG"),8*F,"LONG").price,D(105))

    def test_pre_touch_uptrend_is_confirmed_2x_high_low(self):
        self.assertEqual(x.five_pre_touch_structure(sample_swings("SHORT"),8*F,"SHORT").price,D(96))

    def test_future_confirmed_pivot_must_be_invisible_at_t0(self):
        self.assertIsNone(x.five_pre_touch_structure(sample_swings("LONG"),6*F,"LONG"))

    def test_one_pivot_not_structure(self):
        self.assertIsNone(x.five_pre_touch_structure((pivot("HIGH",100,3*F),),8*F,"LONG"))

    def test_countertrend_without_hhll_not_choch(self):
        self.assertIsNone(x.five_pre_touch_structure(sample_swings("LONG"),8*F,"SHORT"))

    def test_full_post_touch_5m_close_breach(self):
        five=[candle(i*F,103,110,99,103) for i in range(10)]
        five[9]=candle(9*F,103,109,100,108)
        t0=8*F
        signal,status=x.choch_after_t0(five,[b.open_ms for b in five],
                                      sample_swings("LONG"),t0,"LONG")
        self.assertEqual(status,"CONFIRMED")
        self.assertEqual(signal["breach_known_ms"],10*F)
        self.assertLessEqual(signal["swing_confirmed_ms"],t0)

    def test_only_wick_break_is_not_close_choch(self):
        five=[candle(i*F,103,110,99,103) for i in range(10)]
        five[9]=candle(9*F,103,120,101,104)
        z,status=x.choch_after_t0(five,[b.open_ms for b in five],
                                    sample_swings("LONG"),8*F,"LONG")
        self.assertIsNone(z)

    def test_bearish_close_required(self):
        five=[candle(i*F,103,110,99,103) for i in range(10)]
        five[9]=candle(9*F,109,112,101,108)
        z,status=x.choch_after_t0(five,[b.open_ms for b in five],
                                    sample_swings("LONG"),8*F,"LONG")
        self.assertIsNone(z)

    def test_straddling_first_touch_five_minute_is_not_choch(self):
        # t0 at 9m, qualifying candle begins at 10m; 5m bar 5..10
        # is crossing but its open preceded touch, therefore excluded.
        five=[candle(i*F,103,110,99,103) for i in range(4)]
        five[1]=candle(F,103,111,102,108)
        z,status=x.choch_after_t0(five,[b.open_ms for b in five],
                                    sample_swings("LONG"),int(1.8*F),"LONG")
        self.assertIsNone(z)

    def test_choch_no_future_5m_close_after_landmark(self):
        t0=8*F
        five=[candle(i*F,103,110,99,103) for i in range(100)]
        five[82]=candle(82*F,103,109,99,108)
        z,status=x.choch_after_t0(five,[b.open_ms for b in five],
                                    sample_swings("LONG"),t0,"LONG")
        self.assertIsNone(z)

    def test_original_3m_5m_parity_rejects_fake_sources(self):
        three=[NS(start_ms=i*180000,known_ms=(i+1)*180000,
                  open=D(100),high=D(103),low=D(98),close=D(100),volume=D(1)) for i in range(5)]
        five=[candle(i*F,100,103,98,100) for i in range(3)]
        with self.assertRaises(x.C114Error):
            x.independent_15m_parity(tuple(three),tuple(five))

    def test_exact_15m_parity_is_not_reconstructed_5m(self):
        three=[NS(start_ms=i*180000,known_ms=(i+1)*180000,
                  open=D(100),high=D(103),low=D(98),close=D(100),volume=D(1)) for i in range(5)]
        five=[candle(i*F,100,103,98,100) for i in range(3)]
        five=[Bar(b.open_ms,b.o,b.h,b.l,b.c,D(v)) for b,v in zip(five,(1,2,2))]
        self.assertTrue(x.independent_15m_parity(tuple(three),tuple(five)))

    def test_matching_without_replacement(self):
        t1=event(pnum=1);t2=event(pnum=2)
        c1=event(kind="C_NO_CHoCH",pnum=3)
        pairs=x.match_events([t1,t2,c1])
        self.assertEqual(len(pairs),1)
        self.assertEqual(t1["matched_id"],pairs[0]["id"])
        self.assertIsNone(t2["matched_id"])

    def test_matching_does_not_use_outcome(self):
        t=event(pnum=1);c=event(kind="C_NO_CHoCH",pnum=2)
        c["trade"]["net_r"]=-999
        self.assertEqual(len(x.match_events([t,c])),1)

    def test_matching_observes_risk_bin(self):
        t=event(pnum=1);c=event(kind="C_NO_CHoCH",risk="RISK_0_2_TO_1_REWARD_2_TO_4",pnum=2)
        self.assertEqual(len(x.match_events([t,c])),0)

    def test_risk_bin_cannot_claim_underrisk_stop(self):
        t=event()["trade"].copy();t["stop"]="99.99"
        with self.assertRaises(x.C114Error):
            x.risk_bin(t)

    def test_nonfilled_itt_zero_kept(self):
        self.assertEqual(x.score([{"trade":None}],25)["signals"],1)
        self.assertEqual(x.score([{"trade":None}],25)["net_total_r"],0)

    def test_fee_stress_reduces_net_r(self):
        t=event()["trade"]
        self.assertLess(x.net_r(t,40),x.net_r(t,25))
        self.assertLess(x.net_r(t,25),x.net_r(t,14))

    def test_block_bootstrap_reproducible(self):
        t=event(pnum=1);c=event(kind="C_NO_CHoCH",pnum=2)
        p={"symbol":"BNBUSDT","t0":int(x.WINDOWS[0][1].timestamp()*1000),
           "t":t,"c":c}
        self.assertEqual(x.boot_delta([p]),x.boot_delta([p]))

    def test_no_matched_events_bootstrap_is_unknown(self):
        self.assertIsNone(x.boot_delta([])["low95"])

    def test_4h_range_from_confirmed_swings_only(self):
        self.assertEqual(x.range_class((pivot("HIGH",100,3*F),
                                        pivot("LOW",90,4*F)),3*F,D(95),"LONG")[0],"NO_RANGE")
        self.assertEqual(x.range_class((pivot("HIGH",100,3*F),
                                        pivot("LOW",90,4*F)),4*F,D(95),"LONG")[0],"MIDPOINT")

    def test_d1_context_is_report_only(self):
        self.assertEqual(x.day_direction(sample_swings("LONG"),8*F),"D1_LH_LL")

    def test_frozen_windows_bootstrap_seed(self):
        self.assertEqual(x.REPS,2000)
        self.assertEqual(x.BOOT_SEED,11420261030)
        self.assertEqual((x.WINDOWS[0][2]-x.WINDOWS[0][1]).days,56)

if __name__=="__main__":unittest.main()
