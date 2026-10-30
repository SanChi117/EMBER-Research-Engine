"""Adversarial C113 execution tests on fake candles; never market assertions."""
import hashlib
import unittest
from decimal import Decimal as D
from types import SimpleNamespace as NS
from unittest.mock import patch

import c113_final_execution_geometry_research as c113

M = 180000

def candle(ms, o, h, l, c):
    return NS(start_ms=ms, known_ms=ms+M, open=D(str(o)), high=D(str(h)),
              low=D(str(l)), close=D(str(c)))

def parent(side="LONG"):
    if side == "LONG":
        return {"side": "LONG", "entry_ms": 0, "zone_lower": "95",
                "zone_upper": "100", "stop": "94.25", "target": "110",
                "atr4h": "5", "symbol": "BNBUSDT",
                "parent_id": "LONG:CLOSED_H4", "net_r": 0.0}
    return {"side": "SHORT", "entry_ms": 0, "zone_lower": "100",
            "zone_upper": "105", "stop": "105.75", "target": "90",
            "atr4h": "5", "symbol": "BNBUSDT", "parent_id": "SHORT:CLOSED_H4",
            "net_r": 0.0}

def run(t, candles, arm=c113.ARM_LIMIT_WIDE, completed=None, horizon=20*c113.DAY):
    starts=[x.start_ms for x in candles]
    with patch.object(c113.core, "END_MS", horizon):
        return c113.simulate_limit(t, tuple(candles), starts, completed or {}, arm,
                                   last_fill_ms=horizon-7*c113.DAY)

class C113ExecutionTests(unittest.TestCase):
    def test_frozen_source_sha_reference(self):
        self.assertEqual(len(c113.ORIGINAL_C109_SHA), 64)

    def test_original_stop_is_unchanged(self):
        p, reason=c113.basis(parent(), c113.ARM_LIMIT_ORIG)
        self.assertEqual(reason, "OK")
        self.assertEqual(p["stop"], D("94.25"))
        self.assertEqual(p["limit"], D("100"))

    def test_wider_stop_is_h4_atr_only(self):
        p, reason=c113.basis(parent(), c113.ARM_LIMIT_WIDE)
        self.assertEqual(reason, "OK")
        self.assertEqual(p["stop"], D("93.25"))
        self.assertEqual(p["target"], D("110"))

    def test_short_structure_is_symmetric(self):
        p,reason=c113.basis(parent("SHORT"), c113.ARM_LIMIT_WIDE)
        self.assertEqual(reason, "OK")
        self.assertEqual(p["limit"], D("100"))
        self.assertEqual(p["stop"], D("106.75"))

    def test_no_fill_before_actual_native3m_touch(self):
        xs=[candle(0,105,106,101,105),
            candle(M,104,105,99,102),
            candle(2*M,102,111,99.5,110)]
        z=run(parent(),xs)
        self.assertEqual(z["status"], "FILLED")
        self.assertEqual(z["trade"]["entry_ms"],M)
        self.assertEqual(z["trade"]["exit_reason"],"4H_FTA_TARGET")

    def test_filled_bar_target_without_stop_is_not_pre_fill_tp(self):
        xs=[candle(0,104,111,99,101),
            candle(M,101,111,100,110)]
        z=run(parent(),xs)
        self.assertEqual(z["trade"]["entry_ms"],0)
        self.assertEqual(z["trade"]["exit_ms"],2*M)

    def test_stop_first_on_ambiguous_fill_bar(self):
        xs=[candle(0,104,112,92,96)]
        z=run(parent(),xs)
        self.assertEqual(z["status"],"FILLED")
        self.assertEqual(z["trade"]["exit_reason"],"STOP_FIRST_NATIVE3M")
        self.assertTrue(z["trade"]["net_r"] < -1.0)

    def test_gap_through_stop_does_not_vanish(self):
        xs=[candle(0,90,101,89,95)]
        z=run(parent(),xs)
        self.assertEqual(z["status"],"FILLED")
        self.assertEqual(z["trade"]["exit_reason"],"STOP_GAP")
        self.assertLess(z["trade"]["net_r"],-1)

    def test_h4_invalidation_before_limit_retest_cancels(self):
        xs=[candle(0,105,106,101,105),candle(M,102,104,99,100)]
        z=run(parent(),xs,completed={M:D("94")})
        self.assertEqual(z["status"],"CANCELLED_PARENT_INVALIDATION")
        self.assertIsNone(z["trade"])

    def test_no_cancel_with_future_h4_close(self):
        xs=[candle(0,104,106,99,100),candle(M,101,111,100,110)]
        z=run(parent(),xs,completed={2*M:D("94")})
        self.assertEqual(z["status"],"FILLED")

    def test_missed_limit_kept_at_zero(self):
        xs=[candle(k*M,104,108,101,105) for k in range(480)]
        z=run(parent(),xs)
        self.assertEqual(z["status"],"UNFILLED_EXPIRED")
        self.assertIsNone(z["trade"])

    def test_limit_expiry_is_strict_24h(self):
        xs=[candle(k*M,104,108,101,105) for k in range(480)]
        xs.append(candle(480*M,104,109,99,102))
        z=run(parent(),xs)
        self.assertEqual(z["status"],"UNFILLED_EXPIRED")

    def test_rr_gate_is_causal_and_preadmitted(self):
        t=parent()
        t["target"]="106"
        p,reason=c113.basis(t,c113.ARM_LIMIT_WIDE)
        self.assertIsNone(p)
        self.assertEqual(reason,"STRUCTURE_RR_BELOW_1_25")

    def test_pre_signal_4h_looking_forward_not_allowed(self):
        xs=[candle(0,105,108,101,104),
            candle(M,104,106,99,101),
            candle(2*M,101,111,99,110)]
        z=run(parent(),xs,completed={-M:D("94")})
        self.assertEqual(z["status"],"FILLED")

    def test_short_same_bar_stop_first(self):
        xs=[candle(0,98,107,89,101)]
        z=run(parent("SHORT"),xs)
        self.assertEqual(z["status"],"FILLED")
        self.assertEqual(z["trade"]["exit_reason"],"STOP_FIRST_NATIVE3M")

    def test_nonfinite_source_rejected_by_geometry(self):
        t=parent()
        t["zone_upper"]="99"
        self.assertEqual(c113.basis(t,c113.ARM_LIMIT_ORIG)[1],"STRUCTURE_WRONG_SIDE")

    def test_original_market_cost_stress_uses_14bps(self):
        t={"entry":"100","stop":"90","net_r":1.0}
        self.assertAlmostEqual(float(c113.costs(t,25)),.989)
        self.assertAlmostEqual(float(c113.costs(t,14)),1.0)

    def test_b2_friction_increases_with_stress(self):
        t={"entry":"100","stop":"90","gross_r":1.0}
        self.assertGreater(c113.costs(t,25),c113.costs(t,40))

    def test_pf_empty_is_none_and_nonfills_not_cherrypicked(self):
        z=c113.report_score([],25,7,50)
        self.assertEqual(z["fills"],0)
        self.assertEqual(z["signals"],7)
        self.assertIsNone(z["pf"])
        self.assertEqual(z["avg_r_per_signal"],0)

    def test_end_and_not_higher_tf_close_bar_open(self):
        xs=[candle(0,105,106,101,105),candle(M,104,105,99,101),
            candle(2*M,101,110,99,109)]
        z=run(parent(),xs,completed={2*M:D("94")})
        self.assertEqual(z["status"],"FILLED")
        self.assertEqual(z["trade"]["entry_ms"], M)

    def test_precommitted_horizon_constants(self):
        self.assertEqual(c113.HOLD[c113.ARM_LIMIT_WIDE],7*24*c113.h4.H)
        self.assertEqual(c113.LIMIT_TTL,24*c113.h4.H)
        self.assertEqual(c113.SEVEN_DAY_EMBARGO,7*24*c113.h4.H)

if __name__=="__main__":
    unittest.main()
