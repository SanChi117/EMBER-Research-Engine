from __future__ import annotations
import copy
import unittest

from iso03_adapted_route_c_backtest import (
    BacktestConfig, Bar, Signal, TF, run_backtest, signals_from_iso01,
)

O = 1_788_220_800_000


def bars(count=30, price=100.0):
    return [Bar(O + i * TF, price, price + 1, price - 1, price) for i in range(count)]


def one(known=None, direction=1, symbol="X", parent="p"):
    return Signal(parent, symbol, O + 20 * TF if known is None else known, direction, "3m")


def run(custom=None, signals=None, config=None):
    market = {"X": bars() if custom is None else custom}
    return run_backtest(market, [one()] if signals is None else signals,
                        BacktestConfig(fee_rate=0, slippage_rate=0) if config is None else config)


class ISO03BacktestTests(unittest.TestCase):
    def test_01_entry_not_before_signal_knowledge(self):
        t = run()["trades_detail"][0]
        self.assertEqual(t["entry_ms"], O + 20 * TF)
        self.assertGreaterEqual(t["entry_ms"], t["signal_known_ms"])

    def test_02_future_signal_outside_source_no_trade(self):
        result = run(signals=[one(O + 100 * TF)])
        self.assertEqual(result["metrics"]["trades"], 0)

    def test_03_insufficient_atr_history_skips(self):
        result = run(signals=[one(O + 5 * TF)])
        self.assertEqual(result["metrics"]["trades"], 0)
        self.assertEqual(result["metrics"]["skipped_signals"], 1)

    def test_04_long_target(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 107, 99, 106)
        t = run(b)["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "TARGET")
        self.assertGreater(t["net_pnl"], 0)

    def test_05_long_stop(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 101, 96, 97)
        t = run(b)["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "STOP")
        self.assertLess(t["net_pnl"], 0)

    def test_06_short_target(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 101, 93, 94)
        t = run(b, signals=[one(direction=-1)])["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "TARGET")
        self.assertGreater(t["net_pnl"], 0)

    def test_07_short_stop(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 104, 99, 103)
        t = run(b, signals=[one(direction=-1)])["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "STOP")
        self.assertLess(t["net_pnl"], 0)

    def test_08_same_bar_stop_target_conservative(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 110, 90, 100)
        t = run(b)["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "STOP_SAME_BAR_PRIORITY")

    def test_09_gap_stop_uses_open_not_better_stop(self):
        b = bars(); b[21] = Bar(b[21].open_ms, 90, 91, 89, 90)
        t = run(b)["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "STOP")
        self.assertEqual(t["exit"], 90)

    def test_10_time_stop(self):
        t = run(config=BacktestConfig(fee_rate=0, slippage_rate=0, time_stop_bars=2))["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "TIME_STOP")
        self.assertEqual(t["bars_held"], 2)

    def test_11_source_end_close(self):
        t = run(signals=[one(O + 29 * TF)])["trades_detail"][0]
        self.assertEqual(t["exit_reason"], "SOURCE_END")
        self.assertEqual(t["exit_ms"], O + 30 * TF)

    def test_12_entry_fee_deducted_once(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 107, 99, 106)
        r = run(b, config=BacktestConfig(fee_rate=0.001, slippage_rate=0))
        t = r["trades_detail"][0]
        self.assertAlmostEqual(t["net_pnl"], t["gross_pnl_after_slippage"] - t["entry_fee"] - t["exit_fee"])
        self.assertAlmostEqual(r["metrics"]["fees"], t["entry_fee"] + t["exit_fee"])

    def test_13_adverse_entry_and_exit_slippage(self):
        b = bars(); b[20] = Bar(b[20].open_ms, 100, 108, 99, 106)
        r = run(b, config=BacktestConfig(fee_rate=0, slippage_rate=0.001))
        t = r["trades_detail"][0]
        self.assertGreater(t["entry"], 100)
        self.assertLess(t["exit"], t["target"])

    def test_14_occupied_symbol_skips_not_queues(self):
        s1 = one(O + 20 * TF, parent="p1"); s2 = one(O + 21 * TF, parent="p2")
        r = run(signals=[s1, s2])
        self.assertEqual(r["metrics"]["trades"], 1)
        self.assertEqual(r["metrics"]["skipped_signals"], 1)

    def test_15_conflicting_duplicate_parent_rejected(self):
        with self.assertRaisesRegex(ValueError, "CONFLICTING_PARENT"):
            run(signals=[one(parent="p"), one(parent="p", direction=-1)])

    def test_16_identical_duplicate_parent_deduplicated(self):
        r = run(signals=[one(), one()])
        self.assertEqual(r["metrics"]["signals"], 1)

    def test_17_duplicate_bar_rejected(self):
        b = bars(); b.append(b[-1])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_BAR"):
            run_backtest({"X": b}, [one()])

    def test_18_noncontiguous_market_rejected(self):
        b = bars(); b.pop(5)
        with self.assertRaisesRegex(ValueError, "NONCONTIGUOUS"):
            run(b)

    def test_19_bad_bar_rejected(self):
        with self.assertRaisesRegex(ValueError, "INCONSISTENT"):
            Bar(O, 100, 99, 98, 100)

    def test_20_bad_risk_rejected(self):
        with self.assertRaisesRegex(ValueError, "EQUITY_OR_RISK"):
            BacktestConfig(risk_fraction=0)

    def test_21_bad_cost_rejected(self):
        with self.assertRaisesRegex(ValueError, "COSTS"):
            BacktestConfig(fee_rate=-0.1)

    def test_22_leverage_cap_applied(self):
        t = run()["trades_detail"][0]
        self.assertLessEqual(t["entry"] * t["quantity"], 300000.000001)

    def test_23_equity_curve_complete(self):
        r = run()
        self.assertEqual(len(r["equity_curve"]), 30)
        self.assertEqual(r["metrics"]["final_equity"], r["equity_curve"][-1]["equity"])

    def test_24_deterministic(self):
        self.assertEqual(run(), run())

    def test_25_signal_permutation_invariant(self):
        s = [one(O + 20 * TF, parent="a"), one(O + 22 * TF, parent="b"), one(O + 24 * TF, parent="c")]
        self.assertEqual(run(signals=s), run(signals=list(reversed(s))))

    def test_26_no_live_order_or_author_promotion(self):
        r = run()
        self.assertEqual(r["orders_live"], 0)
        self.assertFalse(r["author_strategy_certified"])
        self.assertEqual(r["readiness"], "NOT_TRADE_READY")

    def test_27_signal_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, "ISO01_SCHEMA"):
            signals_from_iso01({})

    def test_28_iso01_direction_and_earliest_child(self):
        doc = {"schema": "EMBER_ISO01_FROZEN_C56_PARENT_OBJECT_STATE_REGISTRY_V1",
               "parent_states": [{"parent_id": "p", "parent": {"symbol": "X", "raid_type": "BSL",
                 "original_3m_bos_known_ms": 30, "original_5m_bos_known_ms": 20}}]}
        s = signals_from_iso01(doc)[0]
        self.assertEqual((s.known_ms, s.child_timeframe, s.direction), (20, "5m", -1))

    def test_29_signal_market_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "MARKET_MISMATCH"):
            run(signals=[one(symbol="Y")])

    def test_30_empty_market_rejected(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_MARKET"):
            run_backtest({}, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
