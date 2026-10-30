"""C117 adverse tests for randomized time not future outcome / no cherry pick."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS
from decimal import Decimal as D
import c117_random_clock_4h_parent_canonical1m as c

THREE=c.engine.THREE
START=20*c.h4.H4
def parent():
    return {"symbol":"BNBUSDT","parent_id":"LONG:H4:STAMP",
            "parent_low":"90","parent_high":"100",
            "parent_created_ms":START-8*c.h4.H4,
            "t0_touch_known_ms":START,
            "landmark_ms":START+6*c.engine.H,
            "side":"LONG","treatment":"T_CHoCH","trade":None}
def price_source():
    # 121 3m bars with a closed first-touch immediately before t0.
    rows=[NS(start_ms=START+(i-1)*THREE,known_ms=START+i*THREE,
             open=D(99),high=D(100),low=D(98),close=D(99))
          for i in range(122)]
    four=[NS(close_ms=(i+1)*c.h4.H4,c=D(100)) for i in range(25)]
    return tuple(rows),[z.start_ms for z in rows],tuple(four),[z.close_ms for z in four]
def fauxplan():
    return {"entry":"99","stop":"89","target":"110",
            "parent_id":"LONG:H4:STAMP","parent_tf":"4H",
            "stop_source_tf":"4H","target_source_tf":"4H"}
def fauxtrade():
    return {**fauxplan(),"entry_ms":START+THREE,
            "exit_ms":START+2*THREE,"side":"LONG",
            "net_r":0.8,"exit_reason":"4H_STRUCTURAL_FTA"}

class C117RandomAdversarial(unittest.TestCase):
    def test_original_engine_and_new_dates_frozen(self):
        self.assertTrue(c.frozen())
        self.assertEqual(c.WINDOWS[0][1].strftime("%Y-%m-%d"),"2025-05-05")
        self.assertEqual(c.WINDOWS[1][2].strftime("%Y-%m-%d"),"2026-10-27")
    def test_eight_random_offsets_causal_deterministic(self):
        x=c.random_offsets("BNBUSDT","PARENT:4H",START)
        self.assertEqual(x,c.random_offsets("BNBUSDT","PARENT:4H",START))
        self.assertEqual(len(x),8)
        self.assertEqual(len(set(x)),8)
        self.assertTrue(all(1<=k<=120 for k in x))
        self.assertNotEqual(x,c.random_offsets("BNBUSDT","PARENT:4H",START+THREE))
    def test_no_zero_and_no_over_six_hours(self):
        for offset in (0,121,-1):
            rows,starts,four,closed=price_source()
            with self.assertRaises(c.C117Error):
                c.random_on_same_parent(parent(),rows,starts,four,closed,[],offset)
    def test_missing_parent_rejected_before_random_sampling(self):
        with self.assertRaises(c.C117Error):c.random_offsets("BNBUSDT","",START)
    def test_random_entry_is_same_parent_4h_and_real_3m_open(self):
        rows,starts,four,closed=price_source()
        with patch.object(c.engine,"early_competing",return_value={"status":"SURVIVED_6H_LANDMARK"}),\
             patch.object(c.h4,"parent_plan",return_value=(fauxplan(),"OK")) as plan,\
             patch.object(c.h4,"simulate",return_value=fauxtrade()):
            trade,status=c.random_on_same_parent(parent(),rows,starts,four,closed,[],1)
        self.assertEqual(status,"FILLED")
        self.assertEqual(trade["symbol"],"BNBUSDT")
        self.assertEqual(trade["parent_id"],parent()["parent_id"])
        self.assertEqual(plan.call_args.args[1],START+THREE)
        self.assertLessEqual(plan.call_args.args[3][-1].close_ms,START+THREE)
    def test_preentry_stop_is_not_omitted_as_winning_random(self):
        rows,starts,four,closed=price_source()
        with patch.object(c.engine,"early_competing",return_value={"status":"EARLY_COMPETING_STOP"}),\
             patch.object(c.h4,"parent_plan") as plan:
            trade,why=c.random_on_same_parent(parent(),rows,starts,four,closed,[],1)
        self.assertIsNone(trade)
        self.assertEqual(why,"EARLY_COMPETING_STOP")
        plan.assert_not_called()
    def test_parent_4h_invalidation_before_random_open_rejected(self):
        rows,starts,four,closed=price_source()
        four2=[NS(close_ms=t,c=D(80) if t==START+c.h4.H4 else D(100))
               for t in closed]
        with patch.object(c.engine,"early_competing",return_value={"status":"SURVIVED_6H_LANDMARK"}),\
             patch.object(c.h4,"parent_plan") as plan:
            trade,why=c.random_on_same_parent(parent(),rows,starts,tuple(four2),closed,[],120)
        self.assertIsNone(trade)
        self.assertEqual(why,"PARENT_4H_INVALIDATED_BEFORE_RANDOM_OPEN")
        plan.assert_not_called()
    def test_random_does_not_depend_on_future_choch_label(self):
        rows,starts,four,closed=price_source()
        no=parent();no["treatment"]="C_NO_CHoCH"
        with patch.object(c.engine,"early_competing",return_value={"status":"SURVIVED_6H_LANDMARK"}),\
             patch.object(c.h4,"parent_plan",return_value=(fauxplan(),"OK")) as plan,\
             patch.object(c.h4,"simulate",return_value=fauxtrade()):
            a=c.random_on_same_parent(parent(),rows,starts,four,closed,[],1)
            b=c.random_on_same_parent(no,rows,starts,four,closed,[],1)
        self.assertEqual(a,b)
    def test_cluster_bootstrap_deterministic(self):
        rows=[]
        for i in range(14):
            rows.append({"symbol":"BNBUSDT" if i%2 else "LINKUSDT",
                "t0_touch_known_ms":START+i*7*c.h4.D1,
                "delta_T_minus_R_25":1.0 if i%2 else -0.3})
        x=c.cluster_test(rows)
        self.assertEqual(x,c.cluster_test(rows))
        self.assertEqual(x["n_events"],14)
        self.assertEqual(x["bootstrap_reps"],2000)
    def test_cluster_positive_effect_signflip_more_significant(self):
        dates=[]
        for i in range(40):
            dates.append({"symbol":("BNBUSDT" if i%2 else "LINKUSDT"),
                  "t0_touch_known_ms":START+i*2*c.h4.D1,
                  "delta_T_minus_R_25":2.0})
        good=c.cluster_test(dates)
        bad=c.cluster_test([{**e,"delta_T_minus_R_25":-2.0} for e in dates])
        self.assertGreater(good["mean_delta_25"],0)
        self.assertLess(good["signflip_p_one_sided"],bad["signflip_p_one_sided"])
    def test_empty_unfilled_policy_no_fake_profit(self):
        x=c.cluster_test([])
        self.assertEqual(x["state"],"NO_POWER")
        self.assertIsNone(x["bootstrap_low95"])
    def test_scope_restores_unmodified_original_engine(self):
        old=(c.engine.WINDOWS,c.engine.download,c.engine.per_symbol,c.engine.PRECOMMIT)
        with c.c117_scope():
            self.assertEqual(c.engine.WINDOWS,c.WINDOWS)
            self.assertIs(c.engine.download,c.canonical.canonical_download)
        self.assertEqual((c.engine.WINDOWS,c.engine.download,c.engine.per_symbol,c.engine.PRECOMMIT),old)
if __name__=="__main__":unittest.main()
