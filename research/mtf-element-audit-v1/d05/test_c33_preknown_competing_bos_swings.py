"""C33 negative source tests: no author pivot priority, no future-right candle."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import (
    observe_native3m_raid_break,_swings,ThreeSwing)
from c33_preknown_competing_bos_swings import (
    _eligible_swing,_native_provenance,
    enumerate_original_competitors,inspect_c33)
from test_c21b_native_3m_vs_5m import make3

def fixture():
    src=make3()
    e=next(e for e in observe_native3m_raid_break(
        src,as_of_ms=src.as_of_ms).potential_breaks
        if e.pivot_center_ms==SEPT_START+3600000)
    return src,e,_swings(src.original_3m_closed)

class C33OriginalPivotCompetitionNegativeTests(unittest.TestCase):
    def test_original_research_pivot_selected_among_preknown(self):
        src,e,sw=fixture()
        z=enumerate_original_competitors(e,src.original_3m_closed,sw)
        self.assertEqual(sum(p.selected_by_frozen_c21_proxy for p in z.competing_swings),1)
        self.assertGreaterEqual(z.competing_preknown_swing_count,1)
    def test_selected_proxy_is_latest_preknown(self):
        src,e,sw=fixture()
        z=enumerate_original_competitors(e,src.original_3m_closed,sw)
        self.assertTrue(z.proxy_is_latest_preknown)
    def test_none_of_competing_swings_author_certified(self):
        src,e,sw=fixture()
        z=enumerate_original_competitors(e,src.original_3m_closed,sw)
        self.assertEqual(z.instructor_bos_status,"NEEDS_AUTHOR_1H_3M_POSITIVE_NEGATIVE_GOLDENS")
        self.assertTrue(all(not p.chosen_by_author for p in z.competing_swings))
        self.assertFalse(z.order_allowed)
        self.assertEqual(z.trades,())
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_every_competitor_known_before_bos_bar_start(self):
        src,e,sw=fixture()
        z=enumerate_original_competitors(e,src.original_3m_closed,sw)
        self.assertTrue(all(p.known_ms<=e.break_start_ms and
            p.center_ms<e.break_start_ms for p in z.competing_swings))
    def test_original_source_all_three_sha_ids_preserved(self):
        src,e,sw=fixture()
        z=enumerate_original_competitors(e,src.original_3m_closed,sw)
        selected=next(x for x in z.competing_swings if x.selected_by_frozen_c21_proxy)
        self.assertEqual((selected.original_left3m_sha_row_id,
                          selected.original_center3m_sha_row_id,
                          selected.original_right3m_sha_row_id),e.swing.native3m_ids)
    def test_future_right_confirmation_is_not_eligible(self):
        src,e,sw=fixture()
        future=replace(e.swing,known_ms=e.break_start_ms+THREE)
        self.assertFalse(_eligible_swing(e,future))
    def test_future_center_is_not_eligible(self):
        src,e,sw=fixture()
        future=replace(e.swing,center_ms=e.break_start_ms)
        self.assertFalse(_eligible_swing(e,future))
    def test_pre_raid_swing_is_not_eligible(self):
        src,e,sw=fixture()
        old=replace(e.swing,center_ms=e.raid_start_ms-THREE)
        self.assertFalse(_eligible_swing(e,old))
    def test_right_confirm_before_raid_closed_not_eligible(self):
        src,e,sw=fixture()
        early=replace(e.swing,known_ms=e.raid_start_ms)
        self.assertFalse(_eligible_swing(e,early))
    def test_equal_to_raid_level_is_not_eligible(self):
        src,e,sw=fixture()
        self.assertFalse(_eligible_swing(e,replace(e.swing,level=e.raid_level)))
    def test_wrong_swing_kind_does_not_qualify(self):
        src,e,sw=fixture()
        other=replace(e.swing,kind="HIGH" if e.side=="SHORT" else "LOW")
        self.assertFalse(_eligible_swing(e,other))
    def test_nonfinite_or_negative_pivot_price_rejected(self):
        src,e,sw=fixture()
        for val in (D("NaN"),D("Infinity"),D("-0.1"),D("0")):
            with self.subTest(val=str(val)):
                with self.assertRaisesRegex(ValueError,"BAD_SWING_SOURCE_PRICE"):
                    _eligible_swing(e,replace(e.swing,level=val))
    def test_fake_original_three_source_ids_rejected(self):
        src,e,sw=fixture()
        fake=replace(e.swing,native3m_ids=("FAKE",)+e.swing.native3m_ids[1:])
        raw={x.start_ms:x for x in src.original_3m_closed}
        with self.assertRaisesRegex(ValueError,"SWING_SHA_ROW_MISMATCH"):
            _native_provenance(fake,raw)
    def test_price_fabrication_rejected_by_actual_center_ohlc(self):
        src,e,sw=fixture()
        fake=replace(e.swing,level=e.swing.level+D("0.0001"))
        raw={x.start_ms:x for x in src.original_3m_closed}
        with self.assertRaisesRegex(ValueError,"NOT_AN_ORIGINAL_STRICT"):
            _native_provenance(fake,raw)
    def test_swapped_center_time_rejected_by_native_source_id(self):
        src,e,sw=fixture()
        fake=replace(e.swing,center_ms=e.swing.center_ms+THREE)
        raw={x.start_ms:x for x in src.original_3m_closed}
        with self.assertRaisesRegex(ValueError,"SWING_SHA_ROW_MISMATCH"):
            _native_provenance(fake,raw)
    def test_wrong_right_confirmation_rejected_by_original3m(self):
        src,e,sw=fixture()
        fake=replace(e.swing,known_ms=e.swing.known_ms+THREE)
        raw={x.start_ms:x for x in src.original_3m_closed}
        with self.assertRaisesRegex(ValueError,"RIGHT_CONFIRM_TIME_DRIFT"):
            _native_provenance(fake,raw)
    def test_tampered_original_center_low_cannot_pass_3m_pivot(self):
        src,e,sw=fixture()
        rows=list(src.original_3m_closed)
        i=next(i for i,x in enumerate(rows) if x.start_ms==e.swing.center_ms)
        rows[i]=(replace(rows[i],low=rows[i].low-D("0.2")) if e.swing.kind=="LOW"\n                 else replace(rows[i],high=rows[i].high+D("0.2")))
        raw={x.start_ms:x for x in rows}
        with self.assertRaisesRegex(ValueError,"NOT_AN_ORIGINAL_STRICT"):
            _native_provenance(e.swing,raw)
    def test_duplicate_selected_swing_refused(self):
        src,e,sw=fixture()
        with self.assertRaisesRegex(ValueError,"NOT_UNIQUE"):
            enumerate_original_competitors(e,src.original_3m_closed,sw+(e.swing,))
    def test_absent_selected_swing_refused(self):
        src,e,sw=fixture()
        with self.assertRaisesRegex(ValueError,"NOT_UNIQUE"):
            enumerate_original_competitors(e,src.original_3m_closed,())
    def test_extra_future_swing_does_not_change_past_result(self):
        src,e,sw=fixture()
        old=enumerate_original_competitors(e,src.original_3m_closed,sw)
        extra=replace(e.swing,known_ms=e.break_start_ms+THREE)
        new=enumerate_original_competitors(e,src.original_3m_closed,sw+(extra,))
        self.assertEqual(old,new)
    def test_event_with_wrong_htf_raid_side_refused(self):
        src,e,sw=fixture()
        with self.assertRaisesRegex(ValueError,"BAD_RAID_OR_BOS_SIDE"):
            enumerate_original_competitors(replace(e,pivot_kind="SSL" if e.side=="SHORT" else "BSL"),
                src.original_3m_closed,sw)
    def test_prior_3m_break_bar_not_available_rejected(self):
        src,e,sw=fixture()
        old=tuple(x for x in src.original_3m_closed if x.start_ms<e.break_start_ms)
        with self.assertRaisesRegex(ValueError,"SOURCE_ROW_MISMATCH"):
            enumerate_original_competitors(e,old,sw)
    def test_forged_readiness_source_rejected(self):
        src=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c33(src,as_of_ms=src.as_of_ms)
    def test_original_3m_hash_tamper_rejected(self):
        src=make3()
        rows=src.original_3m_closed
        broken=replace(src,original_3m_closed=rows[:11]+(
            replace(rows[11],raw_id="SPOOF"),)+rows[12:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c33(broken,as_of_ms=broken.as_of_ms)
    def test_physically_truncated_asof_replay_same(self):
        src=make3()
        cut=SEPT_START+141*THREE
        short=replace(src,as_of_ms=cut,original_3m_closed=src.original_3m_closed[:141])
        self.assertEqual(inspect_c33(src,as_of_ms=cut),inspect_c33(short,as_of_ms=cut))
    def test_final_author_approval_and_orders_remain_zero(self):
        src=make3()
        r=inspect_c33(src,as_of_ms=src.as_of_ms)
        self.assertEqual(r.author_approved_bos,0)
        self.assertEqual(r.orders_created,0)
        self.assertEqual(r.trades_created,0)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
    def test_competition_counter_consistency(self):
        src=make3()
        r=inspect_c33(src,as_of_ms=src.as_of_ms)
        self.assertEqual(r.parents_with_multiple_preknown_swings+
                         r.parents_with_only_one_preknown_swing,
                         r.original_c21_parent_edges)
        self.assertGreaterEqual(r.total_competing_preknown_swings,r.original_c21_parent_edges)
if __name__=="__main__":unittest.main()
