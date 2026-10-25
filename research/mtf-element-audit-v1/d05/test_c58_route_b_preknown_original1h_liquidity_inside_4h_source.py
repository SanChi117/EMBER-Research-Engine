"""C58 source-level IDM-prerequisite negative tests. Synthetic only."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c46_original_4h_classic_imb_first_contact import FourHourImbCandidate,PoiContactObservation
from c20b_hourly_fractal_source_observer import HourFractal
from c21_native3m_source_bridge import Original3mRow
from c16_c08_monthly_daily_htf_lineage import SEPT_START
from c58_route_b_preknown_original1h_liquidity_inside_4h_source import (
    HOUR,THREE,STATUS,ROUTE,evaluate_preknown_original_pivot,
    source_inside_first_contact)
O=SEPT_START
SHA="d"*64
def rid(t):return SHA+":"+str(t)
CONTACT=O+16*HOUR
ASOF=O+17*HOUR
def rows(*,break_at=None):
    z=[]
    for i in range((CONTACT-O)//THREE):
        t=O+i*THREE
        hi=D("111") if break_at==t else D("108")
        z.append(Original3mRow("BTCUSDT",t,t+THREE,
             D("105"),hi,D("102"),D("105"),D("1"),rid(t),SHA))
    return tuple(z)
def piv(*,kind="BSL",level="110",center=O+11*HOUR):
    source=tuple(rid(center-HOUR+i*THREE) for i in range(60))
    return HourFractal(kind,D(level),center,center+2*HOUR,source)
def original_parent(*,contact=True,side="LONG"):
    c=FourHourImbCandidate(side,"100","120",O+12*HOUR,
          O,O+4*HOUR,O+8*HOUR,
          (rid(O),rid(O+4*HOUR),rid(O+8*HOUR)),
          (rid(O+4*HOUR-THREE),rid(O+8*HOUR-THREE),rid(O+12*HOUR-THREE)))
    return PoiContactObservation(c,CONTACT if contact else None,
           CONTACT+THREE if contact else None,rid(CONTACT) if contact else None,
           True,"FIRST_NATIVE3M_SOURCE_CONTACT_OBSERVED_NOT_ACADEMIC_TEST"
           if contact else "UNTOUCHED_IN_COMPLETE_OBSERVED_NATIVE3M_PREFIX")
class C58CryptoOnlyUnsweptPreknownSourceTests(unittest.TestCase):
    def calc(self,parent=None,pivots=None,bars=None):
        return source_inside_first_contact(original_parent() if parent is None else parent,
                (piv(),) if pivots is None else pivots,
                rows() if bars is None else bars,symbol="BTCUSDT",as_of_ms=ASOF)
    def refuse(self,code,*,parent=None,pivots=None,bars=None):
        with self.assertRaisesRegex(ValueError,code):
            self.calc(parent,pivots,bars)
    def test_source_inside_preknown_unswept_is_not_idm(self):
        z=self.calc()
        self.assertEqual(z.source_state,STATUS[3])
        self.assertEqual(len(z.preknown_inside_1h_liquidity),1)
        self.assertTrue(z.preknown_inside_1h_liquidity[0].unswept_until_contact_bar_start)
        self.assertFalse(z.academic_idm_approved or z.author_stronghl_verified)
        self.assertEqual((z.orders,z.trades,z.readiness),((),(),"NOT_TRADE_READY"))
    def test_source_inside_preknown_but_strict_breached_is_not_unswept(self):
        z=self.calc(bars=rows(break_at=O+14*HOUR))
        self.assertEqual(z.source_state,STATUS[2])
        self.assertEqual(z.preknown_inside_1h_liquidity[0].first_original3m_strict_breach_id,
                         rid(O+14*HOUR))
    def test_first_native3m_contact_absent(self):
        z=self.calc(parent=original_parent(contact=False))
        self.assertEqual(z.source_state,STATUS[0])
        self.assertEqual(z.preknown_inside_1h_liquidity,())
    def test_no_level_inside_4h_zone(self):
        z=self.calc(pivots=(piv(level="130"),))
        self.assertEqual(z.source_state,STATUS[1])
    def test_liquidity_known_after_contact_is_not_preknown(self):
        z=self.calc(pivots=(piv(center=O+15*HOUR),))
        self.assertEqual(z.source_state,STATUS[1])
    def test_liquidity_known_before_gap_created_is_excluded(self):
        z=self.calc(pivots=(piv(center=O+8*HOUR),))
        self.assertEqual(z.source_state,STATUS[1])
    def test_both_BSL_and_SSL_observed_without_picking_winner(self):
        z=self.calc(pivots=(piv(kind="BSL"),piv(kind="SSL",level="107")))
        self.assertEqual(len(z.preknown_inside_1h_liquidity),2)
        self.assertEqual(z.source_state,STATUS[2])
    def test_duplicate_same_liquidity_is_kept_not_fake_distinct_trades(self):
        z=self.calc(pivots=(piv(),piv()))
        self.assertEqual(len(z.preknown_inside_1h_liquidity),2)
        self.assertEqual(z.orders,())
    def test_unit_does_not_emit_course_order_or_RR(self):
        z=self.calc();q=z.preknown_inside_1h_liquidity[0]
        self.assertFalse(q.author_idm_certified or q.strong_high_low_author_certified)
        self.assertFalse(q.orders or q.trades or z.orders or z.trades)
    def test_prefix_closes_before_first_contact_source_bar(self):
        q=self.calc().preknown_inside_1h_liquidity[0]
        self.assertEqual(q.inspected_original3m_closed_count,(CONTACT-(O+13*HOUR))//THREE)
    def test_reject_forged_author_POI(self):
        o=original_parent()
        self.refuse("FORGED_AUTHOR_POI",parent=replace(o,candidate=replace(o.candidate,author_poi_certified=True)))
    def test_reject_forged_course_first_test(self):
        self.refuse("FORGED_AUTHOR_POI",parent=replace(original_parent(),academic_poi_test_certified=True))
    def test_reject_fake_contact_when_none_claimed(self):
        q=original_parent(contact=False)
        self.refuse("FICTITIOUS_FIRST_CONTACT",parent=replace(q,first_contact_original3m_id=rid(CONTACT)))
    def test_reject_missing_contact_original_bar_ID(self):
        self.refuse("INVALID_ORIGINAL_FIRST_CONTACT",parent=replace(original_parent(),first_contact_original3m_id=rid(CONTACT-THREE)))
    def test_reject_contact_after_asof(self):
        q=original_parent()
        self.refuse("INVALID_ORIGINAL_FIRST_CONTACT",parent=replace(q,first_contact_bar_start_ms=ASOF,
                      first_contact_closed_known_ms=ASOF+THREE,first_contact_original3m_id=rid(ASOF)))
    def test_reject_invalid_zone_side(self):
        q=original_parent()
        self.refuse("FORGED_AUTHOR_POI",parent=replace(q,candidate=replace(q.candidate,side="FLAT")))
    def test_reject_bad_4h_imb_price(self):
        q=original_parent()
        self.refuse("INVALID_4H_GAP_PRICE",parent=replace(q,candidate=replace(q.candidate,bottom="130")))
    def test_reject_4h_zone_future(self):
        q=original_parent()
        self.refuse("FORGED_AUTHOR_POI",parent=replace(q,candidate=replace(q.candidate,fully_known_ms=O+20*HOUR)))
    def test_reject_fake_source_parent_dict(self):
        self.refuse("NOT_FROZEN_C46_PARENT",parent={"gap":"100"})
    def test_reject_source_pivot_wrong_kind(self):
        self.refuse("FORGED_1H_LIQUIDITY_KIND",pivots=(piv(kind="IDM"),))
    def test_reject_pivot_known_time_fake(self):
        x=piv()
        self.refuse("FUTURE_OR_UNPROVEN_1H_FRACTAL",pivots=(replace(x,known_ms=x.known_ms-HOUR),))
    def test_reject_pivot_center_raw3m_id_mismatch(self):
        x=piv()
        wrong=x.source_rows[:20]+(rid(O),)+x.source_rows[21:]
        self.refuse("FUTURE_OR_UNPROVEN_1H_FRACTAL",pivots=(replace(x,source_rows=wrong),))
    def test_reject_fake_pivot_price_negative(self):
        self.refuse("FUTURE_OR_UNPROVEN_1H_FRACTAL",pivots=(piv(level="-1"),))
    def test_reject_unsorted_original_pivots(self):
        self.refuse("UNORDERED_OR_UNTRUSTED_1H_PIVOT_SOURCE",pivots=(
           piv(center=O+12*HOUR),piv(center=O+11*HOUR)))
    def test_reject_future_native3m_candle_in_precontact_slice(self):
        seg=rows()[((O+13*HOUR)-O)//THREE:]
        z=list(seg)
        z[-1]=replace(z[-1],known_ms=CONTACT+THREE)
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_FORGED_PRECONTACT_3M_PRICE"):
            evaluate_preknown_original_pivot(piv(),tuple(z),gap_known_ms=O+12*HOUR,contact_start_ms=CONTACT)
    def test_reject_native3m_price_high_below_low(self):
        seg=rows()[((O+13*HOUR)-O)//THREE:]
        z=list(seg);z[0]=replace(z[0],high=D("90"))
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_FORGED_PRECONTACT_3M_PRICE"):
            evaluate_preknown_original_pivot(piv(),tuple(z),gap_known_ms=O+12*HOUR,contact_start_ms=CONTACT)
    def test_reject_missing_middle_native3m_row(self):
        seg=rows()[((O+13*HOUR)-O)//THREE:]
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_FORGED_PRECONTACT_3M_PRICE"):
            evaluate_preknown_original_pivot(piv(),seg[:1]+seg[2:],gap_known_ms=O+12*HOUR,contact_start_ms=CONTACT)
    def test_no_volume_based_1h_pivot_promotion(self):
        self.assertEqual(self.calc().source_state,STATUS[3])
        self.assertEqual(ROUTE,"B_4H_VC_1H_IDM")

if __name__=="__main__": unittest.main()
