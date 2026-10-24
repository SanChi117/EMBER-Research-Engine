"""C47 adversarial provenance tests. All passed positives SOURCE-ONLY, zero trades."""
from dataclasses import replace
from decimal import Decimal as D
import unittest
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c20b_hourly_fractal_source_observer import HourSource
from c46_original_4h_classic_imb_first_contact import FourHourImbCandidate,PoiContactObservation,FOUR
from c47_post_4h_contact_1h_imb_source_link import (
 OneHourImbSource,independently_original_1h_imb,
 match_later_closed_source,scan_original_4h_first_contact_to_later_1h_source
)
from test_c21b_native_3m_vs_5m import make3

ANCHOR=FOUR*10000

def zone(side="LONG"):
    return FourHourImbCandidate(side,"103","105",ANCHOR,
       ANCHOR-3*FOUR,ANCHOR-2*FOUR,ANCHOR-FOUR,
       ("4H-0-A","4H-1-A","4H-2-A"),("4H-0-Z","4H-1-Z","4H-2-Z"))

def contact(side="LONG",hit=True):
    return PoiContactObservation(zone(side),
       ANCHOR+THREE if hit else None,
       ANCHOR+2*THREE if hit else None,
       "3M-FIRST-CONTACT" if hit else None,
       True,"FIRST_NATIVE3M_SOURCE_CONTACT_OBSERVED_NOT_ACADEMIC_TEST"
       if hit else "UNTOUCHED_IN_COMPLETE_OBSERVED_NATIVE3M_PREFIX")

def hours(side="LONG",start=ANCHOR+HOUR):
    if side=="LONG":
        price=(("100","103","99","101"),("101","105","100","104"),("107","110","106","109"))
    else:
        price=(("109","110","107","108"),("107","108","103","104"),("99","101","98","100"))
    return tuple(HourSource(start+k*HOUR,start+(k+1)*HOUR,
       D(a),D(h),D(l),D(c),tuple(f"source-{k}-{i}" for i in range(20)))
       for k,(a,h,l,c) in enumerate(price))

def candidate(side="LONG"):
    return independently_original_1h_imb(hours(side))[0]

class C47SourceOnlyCausalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=500)
        cls.out=scan_original_4h_first_contact_to_later_1h_source(cls.src,
            as_of_ms=cls.src.as_of_ms)

    def blocked(self,ob,hs,part):
        with self.assertRaisesRegex(ValueError,part):
            match_later_closed_source(ob,hs,as_of_ms=ANCHOR+4*HOUR)

    def test_long_original1h_classic_gap_three_complete_hours(self):
        x=candidate("LONG")
        self.assertEqual((x.side,x.bottom,x.top),("LONG","103","106"))
        self.assertEqual(x.fully_known_ms,ANCHOR+4*HOUR)
    def test_short_original1h_classic_gap_three_complete_hours(self):
        x=candidate("SHORT")
        self.assertEqual((x.side,x.bottom,x.top),("SHORT","101","107"))
    def test_wrong_1h_no_strict_gap_no_source(self):
        h=list(hours("LONG"))
        h[2]=replace(h[2],low=D("103"))
        self.assertEqual(independently_original_1h_imb(tuple(h)),())
    def test_exact_1h_source_carries_all_raw_three_source_ids(self):
        x=candidate()
        self.assertEqual(len(x.first_raw_native3m_ids),3)
        self.assertEqual(len(x.last_raw_native3m_ids),3)
        self.assertEqual(x.first_raw_native3m_ids,("source-0-0","source-1-0","source-2-0"))
    def test_positive_same_side_long_link_later_than_first_3m_contact(self):
        ls=match_later_closed_source(contact(),(candidate(),),as_of_ms=ANCHOR+4*HOUR)
        self.assertEqual(len(ls),1)
        self.assertGreater(ls[0].first_hour_start_ms,contact().first_contact_closed_known_ms)
    def test_positive_same_side_short_link(self):
        ls=match_later_closed_source(contact("SHORT"),(candidate("SHORT"),),as_of_ms=ANCHOR+4*HOUR)
        self.assertEqual(len(ls),1)
    def test_opposite_side_1h_not_linked(self):
        self.assertEqual(match_later_closed_source(contact(),(candidate("SHORT"),),
            as_of_ms=ANCHOR+4*HOUR),())
    def test_no_parent_contact_cannot_generate_1h_link(self):
        self.assertEqual(match_later_closed_source(contact(hit=False),(candidate(),),
            as_of_ms=ANCHOR+4*HOUR),())
    def test_source_1h_started_before_3m_contact_cannot_link(self):
        hs=hours("LONG",start=ANCHOR-2*HOUR)
        ls=match_later_closed_source(contact(),independently_original_1h_imb(hs),
            as_of_ms=ANCHOR+4*HOUR)
        self.assertEqual(ls,())
    def test_first_1h_bar_start_equal_3m_close_is_allowed(self):
        shifted=replace(candidate(),first_hour_start_ms=ANCHOR+2*THREE,
            second_hour_start_ms=ANCHOR+2*THREE+HOUR,
            third_hour_start_ms=ANCHOR+2*THREE+2*HOUR,
            fully_known_ms=ANCHOR+2*THREE+3*HOUR)
        self.blocked(contact(),(shifted,),"MALFORMED_1H_SOURCE_PROVENANCE")
    def test_no_parent_contact_still_rejects_forged_1h_author_label(self):
        self.blocked(contact(hit=False),(replace(candidate(),academic_vc_certified=True),),
            "FORGED_AUTHOR_1H_VC")
    def test_raw_source_forged_author_vc_fails(self):
        self.blocked(contact(),(replace(candidate(),academic_vc_certified=True),),
            "FORGED_AUTHOR_1H_VC")
    def test_raw_source_forged_orders_fails(self):
        self.blocked(contact(),(replace(candidate(),orders=("order",)),),
            "FORGED_AUTHOR_1H_VC")
    def test_raw_parent_forged_poi_fails(self):
        self.blocked(replace(contact(),academic_poi_test_certified=True),
            (candidate(),),"FORGED_AUTHOR_POI_SOURCE")
    def test_raw_parent_forged_trades_fails(self):
        self.blocked(replace(contact(),trades=("trade",)),
            (candidate(),),"FORGED_AUTHOR_POI_SOURCE")
    def test_bad_unknown_parent_prefix_fails(self):
        self.blocked(replace(contact(),has_complete_original3m_prefix_after_known=False),
            (candidate(),),"FORGED_AUTHOR_POI_SOURCE")
    def test_future_1h_source_fails_even_if_wrong_side(self):
        later=replace(candidate("SHORT"),fully_known_ms=ANCHOR+5*HOUR,
            first_hour_start_ms=ANCHOR+2*HOUR,
            second_hour_start_ms=ANCHOR+3*HOUR,
            third_hour_start_ms=ANCHOR+4*HOUR)
        self.blocked(contact(),(later,),"FUTURE_1H_SOURCE_LEAK")
    def test_unclosed_1h_source_candidate_fails(self):
        self.blocked(contact(),(replace(candidate(),fully_known_ms=ANCHOR+4*HOUR-THREE),),
            "MALFORMED_1H_SOURCE_PROVENANCE")
    def test_1h_missing_raw_source_id_rejected(self):
        self.blocked(contact(),(replace(candidate(),first_raw_native3m_ids=("","x","y")),),
            "MALFORMED_1H_SOURCE_PROVENANCE")
    def test_1h_invalid_nan_bounds_rejected(self):
        self.blocked(contact(),(replace(candidate(),bottom="NaN"),),
            "MALFORMED_1H_SOURCE_PROVENANCE")
    def test_1h_invalid_inverted_bounds_rejected(self):
        self.blocked(contact(),(replace(candidate(),bottom="99999"),),
            "MALFORMED_1H_SOURCE_PROVENANCE")
    def test_1h_source_duplicate_time_rejected(self):
        self.blocked(contact(),(candidate(),candidate()),"1H_SOURCE_GAP_ORDER_DRIFT")
    def test_1h_source_wrong_side_invalid_rejected(self):
        self.blocked(contact(),(replace(candidate(),side="PROFIT"),),"FORGED_1H_SOURCE_DIRECTION")
    def test_1h_bars_noncontiguous_rejected(self):
        h=list(hours());h[1]=replace(h[1],start_ms=h[1].start_ms+THREE)
        with self.assertRaisesRegex(ValueError,"INVALID_HOUR_NATIVE3M_OR_TIME"):
            independently_original_1h_imb(tuple(h))
    def test_1h_bars_missing_raw_rows_rejected(self):
        h=list(hours());h[1]=replace(h[1],native_rows=("missing",))
        with self.assertRaisesRegex(ValueError,"INVALID_HOUR_NATIVE3M_OR_TIME"):
            independently_original_1h_imb(tuple(h))
    def test_unknown_4h_parent_source_status_rejected(self):
        fake=replace(contact(),candidate=replace(zone(),source_status="C44_CLOSED_RANGE_PROXY"))
        self.blocked(fake,(candidate(),),"INVALID_PARENT_4H_KNOWN")
    def test_invalid_contact_timestamp_rejected(self):
        self.blocked(replace(contact(),first_contact_closed_known_ms=ANCHOR+THREE),
            (candidate(),),"INVALID_SOURCE_FIRST_CONTACT_CHRONOLOGY")
    def test_fictitious_contact_without_time_rejected(self):
        self.blocked(replace(contact(hit=False),first_contact_original3m_id="FAKE"),
            (candidate(),),"FICTITIOUS_FIRST_CONTACT")
    def test_integration_has_original_source_all_closed(self):
        self.assertEqual(self.out.original_native3m_closed,len(_source(self.src,self.src.as_of_ms)))
        self.assertEqual(self.out.original_native1h_closed,len(_hours(_source(self.src,self.src.as_of_ms))))
    def test_integration_never_promotes_academic_vc(self):
        self.assertEqual(self.out.author_vc_goldens,0)
        self.assertEqual(self.out.author_poi_goldens,0)
        self.assertTrue(all(not x.course_volume_confirmation_approved
            and not x.course_typed_poi_approved and not x.course_first_valid_test_approved
            for x in self.out.observations))
    def test_integration_no_trades_and_parent_counts(self):
        self.assertEqual((self.out.orders,self.out.trades,self.out.readiness),
            ((),(),"NOT_TRADE_READY"))
        self.assertEqual(self.out.original_source4h_first_contacts,
            self.out.matched_later_technical1h_imb_count+
            self.out.unmatched_after_first_contact_count)
    def test_deterministic_source_scan(self):
        self.assertEqual(scan_original_4h_first_contact_to_later_1h_source(
            self.src,as_of_ms=self.src.as_of_ms),self.out)
    def test_earlier_asof_has_no_future_1h(self):
        t=self.src.as_of_ms-FOUR
        x=scan_original_4h_first_contact_to_later_1h_source(self.src,as_of_ms=t)
        self.assertTrue(all(ob.first_post_contact_1h_imb_source is None or
            ob.first_post_contact_1h_imb_source.fully_known_ms<=t for ob in x.observations))
    def test_partial_last_1h_bar_not_promoted(self):
        t=self.src.as_of_ms-THREE
        x=scan_original_4h_first_contact_to_later_1h_source(self.src,as_of_ms=t)
        self.assertEqual(x.original_native1h_closed,len(_hours(_source(self.src,t))))
    def test_invalid_asof_source_future_fails(self):
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED_3M_OR_GAPPED_ASOF"):
            scan_original_4h_first_contact_to_later_1h_source(
                self.src,as_of_ms=self.src.as_of_ms+THREE)
if __name__=="__main__":unittest.main()
