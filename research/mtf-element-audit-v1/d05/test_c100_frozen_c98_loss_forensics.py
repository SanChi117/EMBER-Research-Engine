#!/usr/bin/env python3
"""C100 adversarial tests: no strategy tuning and no claims beyond frozen C98."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c100_frozen_c98_loss_forensics as m

def fixture(route="C"):
    at = m.START_MS + 2_000_000
    data = {
        "symbol": "SOLUSDT",
        "route": {"A": "A_4H_POI_1H_RAID_15M_VC",
                  "B": "B_1H_NEW_VC_TO_15M_IDM_LIMIT",
                  "C": "C_1H_WICK_RAID_NATIVE3M_BOS"}[route],
        "entry_ms": at,
        "exit_ms": at + 600_000,
        "entry": "100", "stop": "99", "target": "102", "fta": "103",
        "fta_confirmed_ms": at - 600_000,
        "derived_rr": 2.0, "net_r": 1.8,
        "exit_reason": "1H_FTA",
        "fee_slip_roundtrip_bps": 14,
    }
    if route == "B":
        data.update(source_tf="NATIVE_5M", limit_filled=True,
                    side="LONG", signal_ms=at-300_000)
    if route == "C":
        data.update(source_tf="NATIVE_3M", side="LONG",
                    raid_closed_ms=at-180_000, bos_close_ms=at)
    return data

class C100NegativeTests(unittest.TestCase):
    def reject(self, field, value, reason, route="C"):
        trade = fixture(route)
        trade[field] = value
        with self.assertRaisesRegex(m.DiagnosticError, reason):
            m.inspect_trade(trade, route)

    def test_valid_native_3m_bos(self):
        self.assertEqual(m.inspect_trade(fixture("C"), "C")["side"], "LONG")

    def test_valid_idm_limit(self):
        self.assertEqual(m.inspect_trade(fixture("B"), "B")["side"], "LONG")

    def test_a_direction_inferred_not_invented(self):
        self.assertEqual(m.inspect_trade(fixture("A"), "A")["side_source"],
                         "INFERRED_STOP_TARGET_GEOMETRY")

    def test_stop_wrong_side(self):
        self.reject("stop", "101", "STRUCTURAL_TARGET")

    def test_target_wrong_side(self):
        self.reject("target", "98", "STRUCTURAL_TARGET")

    def test_target_beyond_structural_fta(self):
        self.reject("target", "104", "STRUCTURAL_TARGET")

    def test_future_fta(self):
        t=fixture()
        self.reject("fta_confirmed_ms", t["entry_ms"]+1, "FUTURE_FTA")

    def test_future_signal(self):
        t=fixture()
        self.reject("vc_close_ms", t["entry_ms"]+1, "FUTURE_SIGNAL")

    def test_future_poi_first_test(self):
        t=fixture("A")
        self.reject("poi_first_test_ms", t["entry_ms"]+1, "FUTURE_SIGNAL", "A")

    def test_nonfinite_entry(self):
        self.reject("entry", "NaN", "NONFINITE_DECIMAL")

    def test_zero_risk(self):
        self.reject("stop", "100", "INVALID_RISK")

    def test_derived_rr_forgery(self):
        self.reject("derived_rr", 5.5, "INCORRECT_DERIVED_RR")

    def test_wrong_source_three_minutes(self):
        self.reject("source_tf", "NATIVE_5M", "NATIVE_3M_REQUIRED")

    def test_dishonest_explicit_side(self):
        self.reject("side", "SHORT", "EXPLICIT_SIDE_MISMATCH")

    def test_forbidden_fixed_rr(self):
        self.reject("fixed_rr", 2, "FORBIDDEN_LEGACY_FIXED_RR")

    def test_noncausal_exit(self):
        t=fixture()
        self.reject("exit_ms", t["entry_ms"], "NONCAUSAL_EXIT")

    def test_future_bos_relative_to_raid(self):
        t=fixture()
        self.reject("bos_close_ms", t["raid_closed_ms"]-1, "RAID_BOS_SEQUENCE")

    def test_b_missing_limit_touch(self):
        self.reject("limit_filled", False, "B_UNFILLED", "B")

    def test_forged_cost_basis(self):
        self.reject("fee_slip_roundtrip_bps", 0, "14BPS_BASIS")

    def test_profitable_stop_label_rejected(self):
        self.reject("exit_reason", "STOP_FIRST_SAME_3M", "STOP_AS_PROFIT")

    def test_reject_boolean_numeric(self):
        self.reject("entry", True, "BOOLEAN_NOT_DECIMAL")

    def test_original_frozen_48_trade_diagnostic(self):
        doc=json.loads(m.SOURCE.read_text(encoding="utf-8"))
        summary=m.summarize(doc)
        self.assertEqual({k:v["n"] for k,v in summary["routes"].items()},
                         {"A":7, "B":3, "C":38})
        self.assertEqual(summary["routes"]["C"]["by_reason"]["STOP_FIRST_SAME_3M"],21)
        self.assertEqual(summary["routes"]["B"]["positive_net14_n"],0)
        self.assertEqual(summary["real_orders"],0)
        self.assertEqual(summary["trade_rules_changed"],False)

    def test_frozen_cost_replay_detects_forgery(self):
        doc=json.loads(m.SOURCE.read_text(encoding="utf-8"))
        doc["research_models"]["C"]["cost_sensitivity"]["25"]["sum_r"]=5000
        with self.assertRaisesRegex(m.DiagnosticError, "COST_REPLAY"):
            m.summarize(doc)

    def test_real_orders_guard(self):
        doc=json.loads(m.SOURCE.read_text(encoding="utf-8"))
        doc["orders"]=[{"danger":"real"}]
        with self.assertRaisesRegex(m.DiagnosticError,"REAL_EXECUTION"):
            m.summarize(doc)

    def test_window_guard(self):
        doc=json.loads(m.SOURCE.read_text(encoding="utf-8"))
        doc["period_start_ms"] += 1
        with self.assertRaisesRegex(m.DiagnosticError,"UNREGISTERED"):
            m.summarize(doc)

if __name__=="__main__":
    unittest.main()
