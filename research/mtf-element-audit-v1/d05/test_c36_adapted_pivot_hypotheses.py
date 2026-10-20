"""C36 adapted pivot hypotheses: strict source-as-of and non-execution tests."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from dataclasses import asdict
from decimal import Decimal as D
from c36_adapted_pivot_hypotheses import (
    choose_adapted_pivot,_validate_case,chronological_partition,VARIANTS,
    START_MS,END_MS,VALIDATION_START_MS,HOLDOUT_START_MS)
from c33_preknown_competing_bos_swings import enumerate_original_competitors
from test_c33_preknown_competing_bos_swings import fixture

def sample():
    src,event,swings=fixture()
    item=enumerate_original_competitors(event,src.original_3m_closed,swings)
    return json.loads(json.dumps(asdict(item)))

def reseal(case):
    case["competing_preknown_swing_count"]=len(case["competing_swings"])
    case["alternative_preknown_swings"]=len(case["competing_swings"])-1
    case["known_eligible_swing_set_sha256"]=hashlib.sha256(
        json.dumps(case["competing_swings"],sort_keys=True,
                   separators=(",",":")).encode()).hexdigest()
    return case

class C36AdaptedSelectorSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=sample()
        cls.asof=cls.base["break_3m_bar_start_ms"]

    def fresh(self):
        return copy.deepcopy(self.base)

    def test_four_named_hypotheses_no_implicit_fifth(self):
        self.assertEqual(VARIANTS,(
            "LATEST_CONFIRMED_V1","EARLIEST_CONFIRMED_V1",
            "DEEP_RAID_SIDE_V1","NEAREST_RAID_SIDE_V1"))
    def test_c21_baseline_reproduced_by_latest(self):
        x=choose_adapted_pivot(self.fresh(),VARIANTS[0],as_of_ms=self.asof)
        self.assertFalse(x.differs_from_c21_last)
        self.assertEqual(x.selected_swing_center_ms,
                         self.base["frozen_c21_proxy_swing_center_ms"])
    def test_each_variant_only_selects_original_preknown_candidate(self):
        c=self.fresh()
        known={s["original_center3m_sha_row_id"] for s in c["competing_swings"]}
        for v in VARIANTS:
            with self.subTest(v=v):
                x=choose_adapted_pivot(c,v,as_of_ms=self.asof)
                self.assertIn(x.selected_native_center3m_sha_row_id,known)
                self.assertLessEqual(x.selected_swing_known_ms,self.asof)
    def test_hypotheses_return_no_author_bos(self):
        for v in VARIANTS:
            with self.subTest(v=v):
                self.assertFalse(choose_adapted_pivot(self.fresh(),v,as_of_ms=self.asof).author_bos_validated)
    def test_hypotheses_never_imply_c21_bar_bos_on_alt_pivot(self):
        for v in VARIANTS:
            self.assertFalse(choose_adapted_pivot(self.fresh(),v,as_of_ms=self.asof).is_bos_break_at_event)
    def test_hypotheses_never_open_orders_or_trades(self):
        for v in VARIANTS:
            x=choose_adapted_pivot(self.fresh(),v,as_of_ms=self.asof)
            self.assertEqual((x.orders,x.trades), ((),()))
            self.assertFalse(x.paper_signal_allowed)
            self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_reject_unknown_variant(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED"):
            choose_adapted_pivot(self.fresh(),"HIGHEST_WIN_RATE",as_of_ms=self.asof)
    def test_reject_future_asof(self):
        with self.assertRaisesRegex(ValueError,"ASOF_MUST"):
            choose_adapted_pivot(self.fresh(),VARIANTS[0],as_of_ms=self.asof+180000)
    def test_reject_past_asof_cannot_use_future_swings(self):
        with self.assertRaisesRegex(ValueError,"ASOF_MUST"):
            choose_adapted_pivot(self.fresh(),VARIANTS[0],as_of_ms=self.asof-180000)
    def test_reject_bool_asof(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_CASE"):
            choose_adapted_pivot(self.fresh(),VARIANTS[0],as_of_ms=True)
    def test_reject_forged_author_ready(self):
        c=self.fresh();c["readiness"]="READY"
        with self.assertRaisesRegex(ValueError,"AUTHOR_READY"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_forged_approved_order(self):
        c=self.fresh();c["order_allowed"]=True
        with self.assertRaisesRegex(ValueError,"AUTHOR_READY"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_forged_trade(self):
        c=self.fresh();c["trades"]=[{"profit":999}]
        with self.assertRaisesRegex(ValueError,"AUTHOR_READY"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_forged_author_status(self):
        c=self.fresh();c["instructor_bos_status"]="READY"
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_LABEL"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_synthetic_candidate_set_sha_mutation(self):
        c=self.fresh();c["competing_swings"][0]["level"]="99999"
        with self.assertRaisesRegex(ValueError,"CANDIDATE_SET_SHA_DRIFT"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_candidate_future_right_bar_after_resigning_hash(self):
        c=self.fresh();s=c["competing_swings"][0]
        s["known_ms"]=self.asof+180000
        reseal(c)
        with self.assertRaisesRegex(ValueError,"SWING_NOT_KNOWN"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_candidate_fake_native_center_sha_even_if_resigned(self):
        c=self.fresh();c["competing_swings"][0]["original_center3m_sha_row_id"]="FAKE"
        reseal(c)
        with self.assertRaisesRegex(ValueError,"FABRICATED_ORIGINAL"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_wrong_raid_side_even_if_resigned(self):
        c=self.fresh()
        c["competing_swings"][0]["kind"]="HIGH" if c["side"]=="SHORT" else "LOW"
        reseal(c)
        with self.assertRaisesRegex(ValueError,"WRONG_3M_SWING_KIND"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_raided_level_equality_even_if_resigned(self):
        c=self.fresh();c["competing_swings"][0]["level"]=c["raid_level"]
        reseal(c)
        with self.assertRaisesRegex(ValueError,"WRONG_SIDE_OF_RAID"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_nan_level_even_if_resigned(self):
        c=self.fresh();c["competing_swings"][0]["level"]="NaN"
        reseal(c)
        with self.assertRaisesRegex(ValueError,"INVALID_SWING_LEVEL"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_unauthorized_author_pivot_tag_even_if_resigned(self):
        c=self.fresh();c["competing_swings"][0]["chosen_by_author"]=True
        reseal(c)
        with self.assertRaisesRegex(ValueError,"AUTHOR_PIVOT_FORGERY"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_duplicate_candidate_center_even_if_resigned(self):
        c=self.fresh();c["competing_swings"].append(copy.deepcopy(c["competing_swings"][0]))
        reseal(c)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_SWING_CANDIDATE"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_two_baselines_after_resigned(self):
        c=self.fresh()
        # A second baseline may be crafted but only if two valid source pivots.
        if len(c["competing_swings"])<2:
            # Use an ORIGINAL pinned multiple-choice event; no skipped
            # negative test is allowed to count as a full test PASS.
            p=Path(__file__).resolve().parents[1]/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
            full=json.loads(p.read_text(encoding="utf8"))
            c=next(k for market in full["markets"] for k in market["source_case_competing_swings"]
                   if k["competing_preknown_swing_count"]>1)
        asof=c["break_3m_bar_start_ms"]
        c["competing_swings"][0]["selected_by_frozen_c21_proxy"]=True
        c["competing_swings"][-1]["selected_by_frozen_c21_proxy"]=True
        reseal(c)
        with self.assertRaisesRegex(ValueError,"BASELINE_NOT_UNIQUE"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=asof)
    def test_reject_invalid_close_confirm(self):
        c=self.fresh();c["break_3m_close_known_ms"]+=180000
        with self.assertRaisesRegex(ValueError,"FUTURE_BREAK"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_not_yet_confirmed_1h_raid(self):
        c=self.fresh();c["raid_confirmed_ms"]=self.asof+3600000
        with self.assertRaisesRegex(ValueError,"RAID_NOT_CONFIRMED"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_invalid_original_BOS_source_SHA(self):
        c=self.fresh();c["original_break3m_source_row_id"]="fake:1"
        with self.assertRaisesRegex(ValueError,"FABRICATED_ORIGINAL"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_reject_invalid_swing_price_decimal(self):
        c=self.fresh();c["raid_level"]="Infinity"
        with self.assertRaisesRegex(ValueError,"BAD_RAID_DECIMAL"):
            choose_adapted_pivot(c,VARIANTS[0],as_of_ms=self.asof)
    def test_chronological_boundaries_closed_open(self):
        self.assertEqual(chronological_partition(START_MS),"DEVELOPMENT")
        self.assertEqual(chronological_partition(VALIDATION_START_MS),"VALIDATION")
        self.assertEqual(chronological_partition(HOLDOUT_START_MS),"HOLDOUT")
        self.assertEqual(chronological_partition(END_MS-180000),"HOLDOUT")
    def test_reject_future_holdout_end(self):
        with self.assertRaisesRegex(ValueError,"OUTSIDE_FROZEN_SOURCE"):
            chronological_partition(END_MS)
    def test_reject_prehistory_period(self):
        with self.assertRaisesRegex(ValueError,"OUTSIDE_FROZEN_SOURCE"):
            chronological_partition(START_MS-1)
    def test_pivot_choice_deterministic_across_call_order(self):
        c=self.fresh()
        a={v:choose_adapted_pivot(c,v,as_of_ms=self.asof) for v in VARIANTS}
        b={v:choose_adapted_pivot(c,v,as_of_ms=self.asof) for v in reversed(VARIANTS)}
        self.assertEqual(a,b)
    def test_price_never_confused_with_author_selected(self):
        c=self.fresh()
        for v in VARIANTS:
            x=choose_adapted_pivot(c,v,as_of_ms=self.asof)
            self.assertEqual(x.selection_scope,"C33_PREKNOWN_SOURCE_OPTIONS_ONLY")
    def test_multiple_raid_contexts_sharing_one_3m_bar_remain_separate(self):
        from c36_adapted_pivot_hypotheses import summarize_frozen_c33
        p=Path(__file__).resolve().parents[1]/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
        result=summarize_frozen_c33(json.loads(p.read_text(encoding="utf8")))
        self.assertEqual(result["original_parent_events"],539)
        self.assertEqual(result["unique_original3m_BOS_break_bars"],390)
        self.assertEqual(result["additional_raid_contexts_sharing_original3m_bar"],149)
        self.assertFalse(result["samples_are_independent_trades"])
    def test_no_adapted_variant_has_author_goldens_or_orders(self):
        from c36_adapted_pivot_hypotheses import summarize_frozen_c33
        p=Path(__file__).resolve().parents[1]/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
        result=summarize_frozen_c33(json.loads(p.read_text(encoding="utf8")))
        self.assertEqual(result["author_selected_BOS_goldens"],0)
        self.assertEqual(result["orders_created"],0)
        self.assertEqual(result["trades_created"],0)
        self.assertEqual(result["readiness"],"NOT_TRADE_READY")
    def test_incompatible_source_rejected_without_author_status(self):
        from c36_adapted_pivot_hypotheses import summarize_frozen_c33
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_ORIGINAL_C33"):
            summarize_frozen_c33({"schema":"fake","readiness":"READY"})

if __name__=="__main__":unittest.main()
