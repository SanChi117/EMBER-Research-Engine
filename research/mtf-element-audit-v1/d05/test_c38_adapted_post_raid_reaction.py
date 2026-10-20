"""C38 ADAPTED-only post raid reaction: original3m source timing guards."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import _source
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c38_adapted_post_raid_reaction import (
    REACTION_VARIANTS,classify_adapted_reaction,scan_adapted_reactions)
from test_c21b_native_3m_vs_5m import make3

HOUR=3600000
def delayed():
    src=make3(size=220)
    rows=list(src.original_3m_closed)
    updates={
       140:(D("100"),D("101"),D("98"),D("99")),
       141:(D("100"),D("102"),D("98"),D("98.5")),
       142:(D("100"),D("102"),D("97"),D("97.5")),
       143:(D("100"),D("101"),D("94"),D("95")),
    }
    for i,(o,h,l,c) in updates.items():
        rows[i]=replace(rows[i],open=o,high=h,low=l,close=c)
    return replace(src,original_3m_closed=tuple(rows))
def latest_event(src):
    r=scan_original_3m_adapted(src,as_of_ms=src.as_of_ms)
    return next(e for e in r.routes[0].events
                if e.raid_fractal_center_ms==SEPT_START+HOUR)

class C38ReactionCausality(unittest.TestCase):
    def test_exactly_three_distinct_adapted_variants(self):
        self.assertEqual(len(REACTION_VARIANTS),3)
        self.assertEqual(len(set(REACTION_VARIANTS)),3)
    def test_immediate_post_confirm_bos_has_zero_prior_reaction_candles(self):
        src=make3()
        e=latest_event(src)
        r=_source(src,src.as_of_ms)
        for hypothesis in REACTION_VARIANTS:
            obs=classify_adapted_reaction(e,r,hypothesis)
            self.assertEqual(obs.eligible_prior_3m_bars,0)
            self.assertFalse(obs.condition_satisfied)
    def test_delayed_event_does_not_become_break_until_after_reaction(self):
        src=delayed()
        e=latest_event(src)
        self.assertEqual(e.break_bar_start_ms,SEPT_START+7*HOUR+3*THREE)
    def test_directional_body_reaction_uses_only_prior_closed_bar(self):
        src=delayed()
        e=latest_event(src)
        rows=_source(src,src.as_of_ms)
        obs=classify_adapted_reaction(e,rows,REACTION_VARIANTS[0])
        self.assertTrue(obs.condition_satisfied)
        self.assertEqual(obs.first_confirmed_reaction_bar_start_ms,SEPT_START+7*HOUR)
        self.assertLessEqual(obs.first_confirmed_reaction_bar_closed_ms,e.break_bar_start_ms)
    def test_three_progressive_closes_classifies_by_third_confirmed(self):
        src=delayed()
        e=latest_event(src)
        obs=classify_adapted_reaction(e,_source(src,src.as_of_ms),REACTION_VARIANTS[1])
        self.assertTrue(obs.condition_satisfied)
        self.assertEqual(obs.first_confirmed_reaction_bar_start_ms,
                         SEPT_START+7*HOUR+2*THREE)
    def test_half_sweep_relative_to_confirmation_close(self):
        src=delayed()
        e=latest_event(src)
        obs=classify_adapted_reaction(e,_source(src,src.as_of_ms),REACTION_VARIANTS[2])
        self.assertTrue(obs.condition_satisfied)
        self.assertEqual(obs.first_confirmed_reaction_bar_start_ms,
                         SEPT_START+7*HOUR)
    def test_bos_break_candle_never_counts_as_prior_reaction(self):
        src=delayed()
        e=latest_event(src)
        rows=_source(src,src.as_of_ms)
        for variant in REACTION_VARIANTS:
            z=classify_adapted_reaction(e,rows,variant)
            self.assertNotEqual(z.first_confirmed_native3m_row_id,e.break_original_native3m_row_id)
    def test_all_reaction_witnesses_source_bars(self):
        src=delayed()
        rows=_source(src,src.as_of_ms)
        ids={b.raw_id for b in rows}
        e=latest_event(src)
        for variant in REACTION_VARIANTS:
            z=classify_adapted_reaction(e,rows,variant)
            self.assertIn(z.first_confirmed_native3m_row_id,ids)
    def test_missing_unknown_reaction_variant_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"UNKNOWN_ADAPTED_REACTION"):
            classify_adapted_reaction(latest_event(src),
                 _source(src,src.as_of_ms),"OPTIMIZED_RETURN")
    def test_fake_author_approval_forbidden(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_READY"):
            classify_adapted_reaction(replace(latest_event(src),author_bos_approved=True),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_fake_trade_flag_forbidden(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_READY"):
            classify_adapted_reaction(replace(latest_event(src),paper_trade_allowed=True),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_fake_order_forbidden(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_READY"):
            classify_adapted_reaction(replace(latest_event(src),orders=("fake",)),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_forged_break_bar_sha_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BREAK_OR_SWING_ROW_SHA_DRIFT"):
            classify_adapted_reaction(replace(latest_event(src),break_original_native3m_row_id="fake"),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_forged_break_price_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BREAK_OR_SWING_ROW_SHA_DRIFT"):
            classify_adapted_reaction(replace(latest_event(src),break_close="0.123"),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_forged_swing_native_sha_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BREAK_OR_SWING_ROW_SHA_DRIFT"):
            classify_adapted_reaction(replace(latest_event(src),swing_center_native3m_row_id="forged"),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_forged_swing_right_confirm_time_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BREAK_OR_SWING_ROW_SHA_DRIFT"):
            classify_adapted_reaction(replace(latest_event(src),swing_confirmed_ms=0),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_wrong_side_raid_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_READY"):
            classify_adapted_reaction(replace(latest_event(src),side="LONG"),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_wrong_symbol_source_rejected(self):
        src=delayed()
        with self.assertRaisesRegex(ValueError,"WRONG_NATIVE_PRICE_SOURCE_SYMBOL"):
            classify_adapted_reaction(replace(latest_event(src),symbol="FAKE"),
               _source(src,src.as_of_ms),REACTION_VARIANTS[0])
    def test_pre_break_asof_has_no_early_BOS_reaction_output(self):
        src=delayed()
        at=SEPT_START+7*HOUR+3*THREE
        r=scan_adapted_reactions(src,as_of_ms=at)
        self.assertEqual(sum(x.total_bos_parent_contexts for x in r.routes),0)
    def test_after_break_asof_has_reaction_proof(self):
        src=delayed()
        cut=SEPT_START+7*HOUR+4*THREE
        r=scan_adapted_reactions(src,as_of_ms=cut)
        self.assertGreater(sum(x.observed_with_prior_reaction for x in r.routes),0)
    def test_physical_prefix_does_not_change_past_reaction(self):
        src=delayed()
        at=SEPT_START+7*HOUR+4*THREE
        n=(at-SEPT_START)//THREE
        prefix=replace(src,as_of_ms=at,original_3m_closed=src.original_3m_closed[:n])
        self.assertEqual(scan_adapted_reactions(src,as_of_ms=at),
                         scan_adapted_reactions(prefix,as_of_ms=at))
    def test_no_intrabar_future_return_can_be_observed(self):
        src=delayed()
        at=SEPT_START+7*HOUR+4*THREE
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            scan_adapted_reactions(src,as_of_ms=at-1)
    def test_forged_ready_source_rejected(self):
        src=replace(delayed(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            scan_adapted_reactions(src,as_of_ms=src.as_of_ms)
    def test_wrong_native_row_hash_source_rejected(self):
        src=delayed()
        bars=list(src.original_3m_closed)
        bars[120]=replace(bars[120],raw_id="forged")
        bad=replace(src,original_3m_closed=tuple(bars))
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            scan_adapted_reactions(bad,as_of_ms=bad.as_of_ms)
    def test_reaction_matrix_has_all_four_bos_and_three_reaction_slots(self):
        src=delayed()
        r=scan_adapted_reactions(src,as_of_ms=src.as_of_ms)
        self.assertEqual(len(r.routes),12)
        self.assertEqual(len(r.bos_hypotheses),4)
        self.assertEqual(len(r.reaction_hypotheses),3)
    def test_route_reaction_sum_always_equals_route_bos_events(self):
        src=delayed()
        r=scan_adapted_reactions(src,as_of_ms=src.as_of_ms)
        self.assertTrue(all(x.observed_with_prior_reaction+
                x.observed_without_prior_reaction==x.total_bos_parent_contexts
                for x in r.routes))
    def test_post_reaction_zero_author_goldens_and_no_trade(self):
        src=delayed()
        r=scan_adapted_reactions(src,as_of_ms=src.as_of_ms)
        self.assertEqual(r.author_reaction_goldens,0)
        self.assertEqual(r.author_bos_goldens,0)
        self.assertEqual(r.orders,())
        self.assertEqual(r.trades,())
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        for x in r.routes:
            for w in x.observations:
                self.assertFalse(w.paper_signal_allowed)
                self.assertFalse(w.author_reaction_verified)
                self.assertFalse(w.author_bos_verified)
                self.assertEqual((w.orders,w.trades),((),()))

if __name__=="__main__":unittest.main()
