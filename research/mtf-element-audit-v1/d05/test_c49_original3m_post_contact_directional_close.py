"""C49 negative source-only contact reaction: CLOSED 3m after first touch, never VC."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import Original3mRow
from c21b_original_3m_raid_break_geometry import THREE,HOUR,_source
from c46_original_4h_classic_imb_first_contact import FourHourImbCandidate,PoiContactObservation
from c49_original3m_post_contact_directional_close import (
    HORIZONS,observe_post_contact_directional_close,
    inspect_original_source_4h_contact_directional_close,VALID_STATES)
from test_c21b_native_3m_vs_5m import make3

ANCHOR=4*HOUR*9000
W1=HORIZONS[0][0];W4=HORIZONS[1][0];W12=HORIZONS[2][0]

def row(i,close="102",open="102",high="104",low="101"):
    start=ANCHOR+i*THREE
    return Original3mRow("BTCUSDT",start,start+THREE,D(open),D(high),D(low),
        D(close),D("10"),"FAKE-SYNTHETIC-3M-ID:"+str(start),"0"*64)
def zone(side="LONG"):
    return FourHourImbCandidate(side,"101","104",ANCHOR,
       ANCHOR-12*HOUR,ANCHOR-8*HOUR,ANCHOR-4*HOUR,
       ("P0","P1","P2"),("Z0","Z1","Z2"))
def first(side="LONG",touched=True):
    return PoiContactObservation(zone(side),
        ANCHOR if touched else None,
        ANCHOR+THREE if touched else None,
        "FAKE-SYNTHETIC-3M-ID:"+str(ANCHOR) if touched else None,
        True,"FIRST_NATIVE3M_SOURCE_CONTACT_OBSERVED_NOT_ACADEMIC_TEST" if touched
        else "UNTOUCHED_IN_COMPLETE_OBSERVED_NATIVE3M_PREFIX")
def bars(n=5,*,change=None):
    rows=[row(i) for i in range(n)]
    for i,patch in (change or {}).items():
        rows[i]=replace(rows[i],**{k:D(v) if k in ("open","high","low","close") else v
                                  for k,v in patch.items()})
    return tuple(rows)

def classify(rows=None,po=None,policy=W1):
    rr=bars() if rows is None else rows
    return observe_post_contact_directional_close(rr,first() if po is None else po,
        as_of_ms=rr[-1].known_ms,horizon_id=policy)

class C49Original3mDirectionalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=500)
        cls.out=inspect_original_source_4h_contact_directional_close(
            cls.src,as_of_ms=cls.src.as_of_ms)
    def test_exactly_one_four_twelve_hour_policies(self):
        self.assertEqual([h//HOUR for _,h in HORIZONS],[1,4,12])
    def test_positive_long_favorable_later_3m_close(self):
        rr=bars(change={1:{"open":"105","high":"107","low":"104","close":"106"}})
        x=classify(rr)
        self.assertEqual(x.status,"FIRST_LATER_FAVORABLE_3M_CLOSE")
        self.assertTrue(x.favorable_3m_close)
        self.assertFalse(x.adverse_3m_close)
        self.assertEqual(x.first_later_event_close_known_ms,ANCHOR+2*THREE)
    def test_positive_long_adverse_later_3m_close(self):
        rr=bars(change={1:{"open":"100","high":"102","low":"99","close":"100"}})
        x=classify(rr)
        self.assertEqual(x.status,"FIRST_LATER_ADVERSE_3M_CLOSE")
        self.assertTrue(x.adverse_3m_close)
    def test_positive_short_favorable_later_3m_close(self):
        rr=bars(change={1:{"open":"100","high":"102","low":"99","close":"100"}})
        x=classify(rr,po=first("SHORT"))
        self.assertEqual(x.status,"FIRST_LATER_FAVORABLE_3M_CLOSE")
    def test_positive_short_adverse_later_3m_close(self):
        rr=bars(change={1:{"open":"105","high":"107","low":"104","close":"106"}})
        x=classify(rr,po=first("SHORT"))
        self.assertEqual(x.status,"FIRST_LATER_ADVERSE_3M_CLOSE")
    def test_same_first_contact_bar_close_not_falsely_used_as_reaction(self):
        rr=bars(change={0:{"open":"105","high":"107","low":"101","close":"105"}})
        self.assertEqual(classify(rr).status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
    def test_first_event_priority_favorable_then_later_adverse(self):
        rr=bars(change={1:{"open":"105","high":"107","low":"104","close":"106"},
                        2:{"open":"100","high":"102","low":"99","close":"100"}})
        self.assertEqual(classify(rr).status,"FIRST_LATER_FAVORABLE_3M_CLOSE")
    def test_first_event_priority_adverse_then_later_favorable(self):
        rr=bars(change={1:{"open":"100","high":"102","low":"99","close":"100"},
                        2:{"open":"105","high":"107","low":"104","close":"106"}})
        self.assertEqual(classify(rr).status,"FIRST_LATER_ADVERSE_3M_CLOSE")
    def test_touch_without_later_exit_is_censored_before_1h_complete(self):
        self.assertEqual(classify().status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
    def test_touch_without_later_exit_is_completed_after_1h(self):
        x=classify(bars(25))
        self.assertEqual(x.status,"NO_LATER_DIRECTIONAL_CLOSE_HORIZON_COMPLETE")
    def test_touch_without_later_exit_4h_stays_right_censored(self):
        self.assertEqual(classify(bars(25),policy=W4).status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
    def test_no_original_first_contact_requires_no_source_id(self):
        x=classify(po=first(touched=False))
        self.assertEqual(x.status,"NO_PARENT_4H_FIRST_CONTACT_AS_OF")
    def test_exact_zone_top_equality_not_favorable(self):
        rr=bars(change={1:{"open":"104","high":"105","low":"102","close":"104"}})
        self.assertEqual(classify(rr).status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
    def test_exact_zone_bottom_equality_not_adverse(self):
        rr=bars(change={1:{"open":"101","high":"104","low":"100","close":"101"}})
        self.assertEqual(classify(rr).status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
    def test_cross_both_wicks_but_inside_close_not_intrabar_fill(self):
        rr=bars(change={1:{"open":"102","high":"108","low":"95","close":"102"}})
        x=classify(rr)
        self.assertEqual(x.status,"NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN")
        self.assertFalse(x.author_volume_confirmation_certified)
    def test_no_author_trades_when_favorable_close_seen(self):
        rr=bars(change={1:{"open":"105","high":"107","low":"104","close":"106"}})
        x=classify(rr)
        self.assertEqual((x.orders,x.trades,x.readiness),((),(),"NOT_TRADE_READY"))
        self.assertFalse(x.author_reaction_certified or x.author_volume_confirmation_certified)
    def test_unknown_horizon_fails(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_SOURCE_HORIZON"):
            classify(policy="OPTIMIZED_ON_PNL")
    def test_bad_unclosed_snapshot_fails(self):
        rr=bars()
        with self.assertRaisesRegex(ValueError,"INVALID_ZONE_DIRECTION_OR_ASOF"):
            observe_post_contact_directional_close(rr,first(),as_of_ms=rr[-1].known_ms+1,horizon_id=W1)
    def test_missing_complete_last_candle_fails(self):
        rr=bars()
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_3M_CLOSED_SOURCE_PREFIX"):
            observe_post_contact_directional_close(rr,first(),as_of_ms=rr[-1].known_ms-THREE,horizon_id=W1)
    def test_noncontiguous_3m_rows_rejected(self):
        rr=list(bars());rr[2]=replace(rr[2],start_ms=rr[2].start_ms+THREE)
        with self.assertRaisesRegex(ValueError,"MALFORMED_OR_NONCONTIGUOUS"):
            classify(tuple(rr))
    def test_malformed_ohlc_rejected(self):
        rr=list(bars());rr[1]=replace(rr[1],low=D("105"))
        with self.assertRaisesRegex(ValueError,"MALFORMED_OR_NONCONTIGUOUS"):
            classify(tuple(rr))
    def test_nan_ohlc_rejected(self):
        rr=list(bars());rr[1]=replace(rr[1],close=D("NaN"))
        with self.assertRaisesRegex(ValueError,"MALFORMED_OR_NONCONTIGUOUS"):
            classify(tuple(rr))
    def test_first_contact_id_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"FIRST_CONTACT_NOT_IN_ORIGINAL"):
            classify(po=replace(first(),first_contact_original3m_id="WRONG"))
    def test_first_contact_zone_no_longer_touched_rejected(self):
        rr=list(bars());rr[0]=replace(rr[0],low=D("105"),open=D("105"),close=D("105"),high=D("106"))
        with self.assertRaisesRegex(ValueError,"FIRST_CONTACT_NOT_IN_ORIGINAL"):
            classify(tuple(rr))
    def test_fictitious_contact_rejected(self):
        with self.assertRaisesRegex(ValueError,"FICTITIOUS_3M_CONTACT_ID"):
            classify(po=replace(first(touched=False),first_contact_original3m_id="FAKE"))
    def test_contact_source_certification_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_POI_OR_TRADE"):
            classify(po=replace(first(),academic_poi_test_certified=True))
    def test_contact_trade_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_POI_OR_TRADE"):
            classify(po=replace(first(),trades=("TRADE",)))
    def test_parent_4h_author_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_POI_OR_TRADE"):
            classify(po=replace(first(),candidate=replace(zone(),author_poi_certified=True)))
    def test_wrong_candidate_side_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_ZONE_DIRECTION_OR_ASOF"):
            classify(po=replace(first(),candidate=replace(zone(),side="BOTH")))
    def test_wrong_zone_bound_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_4H_SOURCE_WICK_GAP"):
            classify(po=replace(first(),candidate=replace(zone(),bottom="999")))
    def test_original_source_integration_parent_counts(self):
        self.assertEqual(self.out.original_4h_source_candidates,len(self.out.observations))
        self.assertEqual(self.out.original_native3m_closed,len(_source(self.src,self.src.as_of_ms)))
    def test_original_source_integration_first_contact_count(self):
        self.assertEqual(self.out.native3m_first_contact_count,
            sum(x.source_original3m_first_contact_id is not None for x in self.out.observations))
    def test_original_source_integration_never_author_reaction(self):
        self.assertEqual((self.out.course_reaction_goldens,self.out.course_volume_confirmation_goldens),(0,0))
        self.assertTrue(all(not x.academic_valid_first_test and not x.academic_valid_reaction for x in self.out.observations))
    def test_original_source_integration_never_author_fills(self):
        self.assertEqual((self.out.trades,self.out.orders,self.out.readiness),((),(),"NOT_TRADE_READY"))
    def test_original_source_integration_policy_count(self):
        self.assertEqual(self.out.window_count,3)
        self.assertTrue(all(len(x.window_observations)==3 for x in self.out.observations))
    def test_original_source_integration_determinism(self):
        self.assertEqual(inspect_original_source_4h_contact_directional_close(
            self.src,as_of_ms=self.src.as_of_ms),self.out)
    def test_source_prefix_earlier_has_no_future_3m_exit(self):
        cut=self.src.as_of_ms-THREE*80
        x=inspect_original_source_4h_contact_directional_close(self.src,as_of_ms=cut)
        self.assertTrue(all(e.first_later_event_close_known_ms is None or
            e.first_later_event_close_known_ms<=cut
            for v in x.observations for e in v.window_observations))
    def test_original_source_invalid_future_asof_rejected(self):
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            inspect_original_source_4h_contact_directional_close(
                self.src,as_of_ms=self.src.as_of_ms+THREE)
    def test_all_statuses_are_explicit_and_no_ready(self):
        self.assertTrue(all(z.status in VALID_STATES and z.readiness=="NOT_TRADE_READY"
            for x in self.out.observations for z in x.window_observations))
if __name__=="__main__":unittest.main()
