"""C57 fail-closed Route A original15m chronology negative unit tests.

These are synthetics, never market case goldens, trades, author POI or VC.
"""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import NativeKline,SEPT_START
from c47_post_4h_contact_1h_imb_source_link import (
    C47SourceJoin,FourToOneSourceObservation,OneHourImbSource)
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c57_route_a_original15m_first_imb_after_1h_source import (
    FIFTEEN,HOUR,WINDOW,STATUS,SOURCE_SCOPE,FifteenMinuteImb,
    validate_native15m,observed_15m_gaps,first_any_after_parent,
    scan_c57_original_route_a)

O=SEPT_START
T=180000
S=O+12*HOUR
SHA3="a"*64
SHA15="b"*64
def rid(t,sha=SHA3):return sha+":"+str(t)
def native(*,asof=S,mode="LONG",index=34):
    rows=[]
    n=(asof-O)//FIFTEEN
    for i in range(n):
        t=O+i*FIFTEEN
        op=cl=D("100");hi=D("101");lo=D("99")
        if i==index and mode=="LONG":
            op=cl=D("103");hi=D("104");lo=D("102")
        if i==index and mode=="SHORT":
            op=cl=D("97");hi=D("98");lo=D("96")
        rows.append(NativeKline("BTCUSDT","15m",t,t+FIFTEEN,
            op,hi,lo,cl,D("10"),rid(t,SHA15),SHA15))
    return tuple(rows)
def hourly(*,side="LONG",when=O+5*HOUR):
    return OneHourImbSource(side,"100","102",when,when+HOUR,
        when+2*HOUR,when+3*HOUR,
        tuple(rid(when+i*HOUR) for i in range(3)),
        tuple(rid(when+(i+1)*HOUR-T) for i in range(3)))
def parent(*,side="LONG",contact=True,one=True):
    return FourToOneSourceObservation("BTCUSDT",side,O+4*HOUR,
        tuple(rid(O+i*4*HOUR) for i in range(3)),
        rid(O+4*HOUR) if contact else None,
        O+4*HOUR+T if contact else None,
        1 if contact and one else 0,
        hourly(side=side) if contact and one else None)
def c47(par=None,*,asof=S):
    p=par or parent()
    contact=p.original4h_first_contact_native3m_id is not None
    one=p.first_post_contact_1h_imb_source is not None
    return C47SourceJoin("BTCUSDT",asof,240,(asof-O)//HOUR,
        1,int(contact),int(one),int(contact and not one),
        ACADEMIC_CORE_ID,(p,))

class C57RouteAFirstAnyNative15mSourceTests(unittest.TestCase):
    def review(self,par=None,rows=None,asof=S):
        return scan_c57_original_route_a(c47(par,asof=asof),
            native(asof=asof) if rows is None else rows,as_of_ms=asof)
    def refuse(self,code,par=None,rows=None,asof=S):
        with self.assertRaisesRegex(ValueError,code):
            self.review(par,rows,asof)

    def test_positive_synthetic_first_any_is_same_side_not_academic(self):
        x=self.review();o=x.observations[0]
        self.assertEqual(o.source_status,STATUS[3])
        self.assertEqual(x.route_mode,SOURCE_SCOPE)
        self.assertEqual(o.first_any_15m_imb.first_start_ms,O+32*FIFTEEN)
        self.assertFalse(o.course_author_15m_VC_verified)
        self.assertEqual((o.orders,o.trades,o.readiness),((),(),"NOT_TRADE_READY"))
    def test_synthetic_first_opposite_not_rerouted_to_favorable(self):
        x=self.review(rows=native(mode="SHORT"))
        self.assertEqual(x.observations[0].source_status,STATUS[4])
        self.assertEqual(x.observations[0].first_any_15m_imb.side,"SHORT")
    def test_synthetic_no_native15m_source_first_in_window(self):
        x=self.review(rows=native(mode="NO_GAP"))
        self.assertEqual(x.observations[0].source_status,STATUS[2])
    def test_missing_original_3m_first_contact(self):
        x=self.review(par=parent(contact=False))
        self.assertEqual(x.observations[0].source_status,STATUS[0])
    def test_no_later_1h_imb_source(self):
        x=self.review(par=parent(one=False))
        self.assertEqual(x.observations[0].source_status,STATUS[1])
    def test_six_hour_limit_is_fixed_not_posthoc_favorability(self):
        asof=O+17*HOUR
        x=self.review(rows=native(asof=asof,index=58),asof=asof)
        self.assertEqual(x.observations[0].source_status,STATUS[2])
    def test_native_15m_price_gap_not_conflated_with_volume_confirmation(self):
        q=observed_15m_gaps(native())
        self.assertTrue(q)
        self.assertTrue(all(not z.academic_vc_certified and not z.orders and not z.trades for z in q))
    def test_only_first_any_source_used_never_select_later_favorable(self):
        rows=list(native(mode="SHORT"))
        i=39;t=O+i*FIFTEEN
        rows[i]=replace(rows[i],open=D("103"),high=D("104"),low=D("102"),close=D("103"))
        x=self.review(rows=tuple(rows))
        self.assertEqual(x.observations[0].source_status,STATUS[4])
    def test_reject_untrusted_bar_type(self):
        x=list(native());x[0]={"open":100}
        self.refuse("INVALID_ORIGINAL_NATIVE15M_PRICE_ROW",rows=tuple(x))
    def test_reject_missing_middle_15m_bar(self):
        x=native()
        self.refuse("NOT_COMPLETE_CLOSED_PREFIX",rows=x[:2]+x[3:])
    def test_reject_future_asof_bar(self):
        x=native()
        self.refuse("NOT_COMPLETE_CLOSED_PREFIX",rows=x[:-1],asof=S)
    def test_reject_uncut_native_prefix_for_earlier_asof(self):
        self.refuse("NOT_COMPLETE_CLOSED_PREFIX",rows=native(),asof=S-FIFTEEN)
    def test_reject_non_15m_asof(self):
        self.refuse("NOT_COMPLETE_CLOSED_PREFIX",asof=S-T)
    def test_reject_wrong_source_symbol(self):
        q=list(native());q[0]=replace(q[0],symbol="ETHUSDT")
        self.refuse("INVALID_ORIGINAL_NATIVE15M_PRICE_ROW",rows=tuple(q))
    def test_reject_wrong_source_tf(self):
        q=list(native());q[0]=replace(q[0],tf="5m")
        self.refuse("INVALID_ORIGINAL_NATIVE15M_PRICE_ROW",rows=tuple(q))
    def test_reject_invalid_source_checksum_row_id(self):
        q=list(native());q[0]=replace(q[0],origin_raw_row_id=rid(O+FIFTEEN,SHA15))
        self.refuse("INVALID_ORIGINAL_NATIVE15M_PRICE_ROW",rows=tuple(q))
    def test_reject_nonfinite_native_price(self):
        q=list(native());q[0]=replace(q[0],high=D("NaN"))
        self.refuse("NOT_FINITE_POSITIVE_NATIVE_PRICE",rows=tuple(q))
    def test_reject_unrealistic_ohlc(self):
        q=list(native());q[0]=replace(q[0],low=D("101.5"))
        self.refuse("NATIVE15M_IMPOSSIBLE_OHLC",rows=tuple(q))
    def test_reject_negative_native_volume(self):
        q=list(native());q[0]=replace(q[0],volume=D("-1"))
        self.refuse("INVALID_ORIGINAL_NATIVE15M_PRICE_ROW",rows=tuple(q))
    def test_reject_forged_original_c47_parent_type(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_C47"):
            scan_c57_original_route_a({},native(),as_of_ms=S)
    def test_reject_c47_parent_future_asof(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_C47"):
            scan_c57_original_route_a(c47(asof=S+FIFTEEN),native(),as_of_ms=S)
    def test_reject_inconsistent_c47_parent_contact_count(self):
        q=replace(c47(),original_source4h_first_contacts=0)
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_C47"):
            scan_c57_original_route_a(q,native(),as_of_ms=S)
    def test_reject_author_original_poi_upgrade(self):
        self.refuse("FORGED_AUTHOR_POI",par=replace(parent(),course_typed_poi_approved=True))
    def test_reject_author_first_valid_touch_upgrade(self):
        self.refuse("FORGED_AUTHOR_POI",par=replace(parent(),course_first_valid_test_approved=True))
    def test_reject_author_volume_upgrade(self):
        self.refuse("FORGED_AUTHOR_POI",par=replace(parent(),course_volume_confirmation_approved=True))
    def test_reject_author_1h_vc_forgery(self):
        p=parent()
        self.refuse("1H_C47_GEOMETRY",par=replace(p,first_post_contact_1h_imb_source=replace(p.first_post_contact_1h_imb_source,academic_vc_certified=True)))
    def test_reject_1h_source_known_after_asof(self):
        p=parent()
        self.refuse("1H_C47_GEOMETRY",par=replace(p,first_post_contact_1h_imb_source=hourly(when=O+11*HOUR)))
    def test_reject_1h_first_hour_before_first_contact_close(self):
        p=parent()
        self.refuse("1H_C47_GEOMETRY",par=replace(p,first_post_contact_1h_imb_source=hourly(when=O+4*HOUR)))
    def test_reject_1h_mismatched_source_candle_hash_time(self):
        p=parent();v=p.first_post_contact_1h_imb_source
        self.refuse("1H_C47_GEOMETRY",par=replace(p,first_post_contact_1h_imb_source=replace(v,first_raw_native3m_ids=(rid(O),)+v.first_raw_native3m_ids[1:])))
    def test_reject_1h_side_mismatch(self):
        p=parent();v=p.first_post_contact_1h_imb_source
        self.refuse("1H_C47_GEOMETRY",par=replace(p,first_post_contact_1h_imb_source=replace(v,side="SHORT")))
    def test_reject_contact_original3m_wrong_row_id(self):
        self.refuse("INVALID_FIRST_NATIVE3M_CONTACT",par=replace(parent(),original4h_first_contact_native3m_id=rid(O+5*HOUR)))
    def test_reject_partial_first_contact(self):
        self.refuse("PARTIAL_FIRST_CONTACT",par=replace(parent(),original4h_first_contact_native3m_id=None))
    def test_reject_fake_1h_without_original_3m_first_contact(self):
        p=parent()
        bad=replace(p,original4h_first_contact_native3m_id=None,original4h_first_contact_closed_known_ms=None)
        self.refuse("1H_WITHOUT_4H_FIRST_CONTACT",par=bad)
    def test_reject_1h_missing_with_nonzero_source_candidates(self):
        p=parent()
        bad=replace(p,first_post_contact_1h_imb_source=None,post_contact_same_side_1h_candidate_count=1)
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_C47"):
            self.review(bad)
    def test_reject_borrowed_fake_15m_imb_event(self):
        gs=observed_15m_gaps(native()); p=parent()
        self.assertTrue(gs)
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED_15M"):
            first_any_after_parent(p,(replace(gs[0],academic_vc_certified=True),),symbol="BTCUSDT",as_of_ms=S)
    def test_reject_fabricated_future_15m_gap(self):
        gs=observed_15m_gaps(native()); p=parent()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED_15M"):
            first_any_after_parent(p,(replace(gs[0],fully_known_ms=S+FIFTEEN),),symbol="BTCUSDT",as_of_ms=S)
    def test_reject_fake_15m_gap_raw_row_id_time(self):
        gs=observed_15m_gaps(native()); p=parent()
        z=replace(gs[0],original_native15m_ids=(rid(O,SHA15),)+gs[0].original_native15m_ids[1:])
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED_15M"):
            first_any_after_parent(p,(z,),symbol="BTCUSDT",as_of_ms=S)
    def test_reject_mixed_15m_gap_source_order(self):
        gs=observed_15m_gaps(native()); p=parent()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED_15M"):
            first_any_after_parent(p,(gs[-1],gs[0]),symbol="BTCUSDT",as_of_ms=S)
    def test_reject_course_parent_author_trade_approval(self):
        self.refuse("FORGED_AUTHOR_POI",par=replace(parent(),orders=("fake",)))
    def test_reject_source_1h_post_first_contact_zero_not_compatible(self):
        p=parent()
        self.refuse("1H_C47_GEOMETRY",par=replace(p,post_contact_same_side_1h_candidate_count=0))
    def test_no_live_or_paper_trades_even_with_matching_15m_source(self):
        q=self.review()
        self.assertEqual((q.author_POI_goldens,q.author_15m_VC_goldens,q.orders,q.trades,q.readiness),(0,0,(),(),"NOT_TRADE_READY"))

if __name__=="__main__":unittest.main()
