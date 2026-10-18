"""C31 adversarial original C21 3m BOS provenance: crossing versus close.
Public ICT examples are never valid author-labelled positive outcomes.
"""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import observe_native3m_raid_break
from c31_bos_entry_semantic_disagreement import audit_single_bos,inspect_c31_bos
from test_c21b_native_3m_vs_5m import make3

def example():
    src=make3()
    e=next(e for e in observe_native3m_raid_break(
       src,as_of_ms=src.as_of_ms).potential_breaks
       if e.pivot_center_ms==SEPT_START+3600000)
    return e,src.original_3m_closed

class C31BOSNegative(unittest.TestCase):
    def test_original_3m_research_closed_bos_case_not_author_labeled(self):
        e,rows=example()
        x=audit_single_bos(e,rows)
        self.assertTrue(x.strictly_bos_side_of_raid_fractal)
        self.assertEqual(x.lag_raid_confirmed_to_break_minutes,0)
        self.assertEqual(x.earlier_wick_cross_count,0)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
        self.assertEqual(x.academic_bos_pivot_status,"AUTHOR_SELECTED_BOS_PIVOT_UNKNOWN")
        self.assertEqual(len(x.preceding_calendar_day_hypotheses),3)
    def test_bos_pivot_future_known_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            audit_single_bos(replace(e,swing=replace(e.swing,known_ms=e.break_start_ms+THREE)),r)
    def test_raid_confirmation_after_break_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            audit_single_bos(replace(e,raid_confirmed_ms=e.break_start_ms+3600000),r)
    def test_wrong_sweep_side_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"BAD_RAID"):
            audit_single_bos(replace(e,pivot_kind="SSL"),r)
    def test_wrong_swing_pivot_kind_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"BAD_RAID"):
            audit_single_bos(replace(e,swing=replace(e.swing,kind="HIGH")),r)
    def test_break_time_not_close_plus_three_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            audit_single_bos(replace(e,break_known_ms=e.break_start_ms+1),r)
    def test_break_bar_id_mismatch_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"SOURCE_ROW_MISMATCH"):
            audit_single_bos(replace(e,source_original_3m_row_id="fake"),r)
    def test_break_bar_price_drift_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"SOURCE_ROW_MISMATCH"):
            audit_single_bos(replace(e,break_close=e.break_close-D("1")),r)
    def test_no_close_beyond_swing_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NO_STRICT_BOS"):
            audit_single_bos(replace(e,swing=replace(e.swing,level=e.break_close-D("1"))),r)
    def test_not_below_raid_level_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NO_STRICT_BOS"):
            audit_single_bos(replace(e,raid_level=e.swing.level),r)
    def test_body_beyond_raid_level_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"NO_STRICT_BOS"):
            audit_single_bos(replace(e,raid_extreme=e.raid_level),r)
    def test_invalid_decimal_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"INVALID_DECIMAL"):
            audit_single_bos(replace(e,raid_level=D("NaN")),r)
    def test_prior_wick_and_prior_close_separately_observed(self):
        e,orig=example()
        idx=next(i for i,x in enumerate(orig) if x.start_ms==e.break_start_ms)
        # Three earlier original3m bars after raid confirmed; one touches
        # selected swing by WICK ONLY, another closes beyond it, and the
        # designated delayed research close is on the fourth bar.
        assert idx+3<len(orig)
        pivot=e.swing.level
        changed=list(orig)
        changed[idx]=replace(orig[idx],open=D("100"),high=D("101"),
             low=pivot-D("1"),close=D("100"))
        changed[idx+1]=replace(orig[idx+1],open=D("100"),high=D("101"),
             low=pivot-D("2"),close=pivot-D("1"))
        changed[idx+2]=replace(orig[idx+2],open=D("100"),high=D("101"),
             low=D("98"),close=D("100"))
        changed[idx+3]=replace(orig[idx+3],open=D("100"),high=D("101"),
             low=pivot-D("3"),close=pivot-D("2"))
        delayed=replace(e,break_start_ms=orig[idx+3].start_ms,
            break_known_ms=orig[idx+3].known_ms,
            break_close=changed[idx+3].close,
            source_original_3m_row_id=orig[idx+3].raw_id)
        w=audit_single_bos(delayed,tuple(changed))
        self.assertEqual(w.earlier_wick_cross_count,2)
        self.assertEqual(w.earlier_wick_without_confirmed_bos_count,1)
        self.assertEqual(w.earlier_close_beyond_bos_level_count,1)
        self.assertEqual(w.first_earlier_wick_cross_source_row_id,orig[idx].raw_id)
        self.assertEqual(w.readiness,"NOT_TRADE_READY")
    def test_earlier_tick_order_unobservable_from_original3m_bar(self):
        e,orig=example()
        # Same candle low and close: causal bar-known-at cannot assert
        # exact market crossing/fill order.
        a=audit_single_bos(e,orig)
        self.assertEqual(a.research_break_close_known_ms,e.break_known_ms)
        self.assertEqual(a.author_entry_status,"MARKET_CROSS_VS_CLOSE_OR_LIMIT_UNKNOWN")
    def test_forged_source_approval_does_not_get_past_original_source_gate(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c31_bos(x,as_of_ms=x.as_of_ms)
    def test_untrusted_tuple_or_event_rejected(self):
        e,r=example()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            audit_single_bos(e,list(r))
    def test_original_source_tamper_rejected(self):
        src=make3()
        rows=src.original_3m_closed
        altered=replace(src,original_3m_closed=rows[:20]+(
            replace(rows[20],raw_id="bad"),)+rows[21:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c31_bos(altered,as_of_ms=altered.as_of_ms)
if __name__=="__main__":unittest.main()
