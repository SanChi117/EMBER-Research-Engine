"""C60 source-only episode tests, synthetic no trading or author POI labels."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c46_original_4h_classic_imb_first_contact import FourHourImbCandidate
from c21_native3m_source_bridge import Original3mRow
from c16_c08_monthly_daily_htf_lineage import SEPT_START
from c60_original_4h_imb_3m_contact_episode_lifecycle import observe_original3m_zone_visits,THREE
O=SEPT_START+12*3600000
H="c"*64
def rid(t):return H+":"+str(t)
def candle(i,in_zone=False):
    t=O+i*THREE
    low,high=(D("103"),D("105")) if in_zone else (D("120"),D("122"))
    return Original3mRow("BTCUSDT",t,t+THREE,
        low,high,low,high,D("10"),rid(t),H)
def source(*pattern):
    return tuple(candle(i,flag) for i,flag in enumerate(pattern))
def gap(**kw):
    x=FourHourImbCandidate("LONG","100","110",O,
        O-12*3600000,O-8*3600000,O-4*3600000,
        (rid(O-12*3600000),rid(O-8*3600000),rid(O-4*3600000)),
        (rid(O-8*3600000-THREE),rid(O-4*3600000-THREE),rid(O-THREE)))
    return replace(x,**kw)

class SourceEpisodeGuards(unittest.TestCase):
    pattern=(False,True,True,False,True,False,True,True)
    def scan(self,rows=None,g=None,asof=None):
        q=source(*self.pattern) if rows is None else rows
        return observe_original3m_zone_visits(q,gap() if g is None else g,
            as_of_ms=q[-1].known_ms if asof is None else asof)
    def reject(self,phrase,rows=None,g=None,asof=None):
        with self.assertRaisesRegex(ValueError,phrase):
            self.scan(rows,g,asof)
    def test_three_source_visits_after_closed_departure(self):
        x=self.scan()
        self.assertEqual(len(x),3)
        self.assertEqual([z.kind for z in x],
            ["FIRST_SOURCE_WICK_VISIT","REPEATED_SOURCE_WICK_RETURN","REPEATED_SOURCE_WICK_RETURN"])
        self.assertEqual([z.candle_count for z in x],[2,1,2])
        self.assertEqual([z.first_bar_start_ms for z in x],[O+THREE,O+4*THREE,O+6*THREE])
        self.assertEqual([z.still_inside_at_source_end for z in x],[False,False,True])
        self.assertFalse(any(z.author_valid_poi_test_verified or z.orders or z.trades for z in x))
    def test_8_adjacent_touch_bars_only_one_source_episode(self):
        x=self.scan(rows=source(*([True]*8)))
        self.assertEqual(len(x),1)
        self.assertEqual(x[0].candle_count,8)
        self.assertTrue(x[0].still_inside_at_source_end)
    def test_outside_before_first_visit_not_retest(self):
        x=self.scan(rows=source(False,False,False,True,True,False,False))
        self.assertEqual(len(x),1)
        self.assertEqual(x[0].kind,"FIRST_SOURCE_WICK_VISIT")
    def test_departure_one_full_closed_bar_then_return(self):
        x=self.scan(rows=source(False,True,False,True,False))
        self.assertEqual(len(x),2)
        self.assertTrue(x[1].separated_from_prior_by_fully_closed_outside_3m)
    def test_departure_last_source_bar_closes_episode(self):
        x=self.scan(rows=source(False,True,False))
        self.assertEqual(len(x),1)
        self.assertFalse(x[0].still_inside_at_source_end)
    def test_never_contacted_source_zone_no_episodes(self):
        self.assertEqual(self.scan(rows=source(False,False,False)),())
    def test_any_wick_intersection_even_bar_close_outside(self):
        q=list(source(False,False,False))
        q[1]=replace(q[1],low=D("109"),high=D("125"))
        self.assertEqual(len(self.scan(rows=tuple(q))),1)
    def test_source_boundary_high_equal_bottom_is_intersection(self):
        q=list(source(False,False))
        q[0]=replace(q[0],low=D("90"),high=D("100"))
        self.assertEqual(len(self.scan(rows=tuple(q))),1)
    def test_source_boundary_low_equal_top_is_intersection(self):
        q=list(source(False,False))
        q[0]=replace(q[0],low=D("110"),high=D("125"))
        self.assertEqual(len(self.scan(rows=tuple(q))),1)
    def test_no_future_source_suffix_allowed_before_asof(self):
        self.reject("INVALID_CLOSED_SOURCE_3M_GRID",asof=O+5*THREE)
    def test_reject_partial_final_asof(self):
        self.reject("FORGED_AUTHOR_OR_UNCLOSED_PARENT_4H",asof=O+8*THREE-1)
    def test_reject_missing_middle_candle(self):
        q=source(*self.pattern)
        self.reject("INVALID_CLOSED_SOURCE_3M_GRID",rows=q[:2]+q[3:])
    def test_reject_incomplete_original_prefix(self):
        q=source(*self.pattern)
        self.reject("INCOMPLETE_OR_FUTURE_SOURCE_PREFIX",rows=q[:-1],asof=q[-1].known_ms)
    def test_reject_gap_right_after_parent_known(self):
        q=source(*self.pattern)
        self.reject("GAPPED_AFTER_KNOWN_4H_SOURCE",rows=q[1:])
    def test_reject_source_timestamp_row_id_forgery(self):
        q=list(source(*self.pattern));q[0]=replace(q[0],raw_id=rid(O+THREE))
        self.reject("INVALID_CLOSED_SOURCE_3M_GRID",rows=tuple(q))
    def test_reject_nan_candle(self):
        q=list(source(*self.pattern));q[1]=replace(q[1],high=D("NaN"))
        self.reject("INVALID_CLOSED_SOURCE_3M_GRID",rows=tuple(q))
    def test_reject_author_poi_upgrade(self):
        self.reject("FORGED_AUTHOR_OR_UNCLOSED_PARENT_4H",g=gap(author_poi_certified=True))
    def test_reject_orders_on_parent(self):
        self.reject("FORGED_AUTHOR_OR_UNCLOSED_PARENT_4H",g=gap(orders=("fake",)))
    def test_reject_nonfinite_parent_zone(self):
        self.reject("INVALID_ORIGINAL_4H_ZONE",g=gap(bottom="NaN"))
    def test_reject_reversed_parent_zone(self):
        self.reject("INVALID_ORIGINAL_4H_ZONE",g=gap(bottom="120"))
    def test_reject_future_parent_4h(self):
        self.reject("FORGED_AUTHOR_OR_UNCLOSED_PARENT_4H",g=gap(fully_known_ms=O+4*3600000))
    def test_no_independently_tradable_source_signal(self):
        x=self.scan()
        self.assertTrue(all(not v.author_valid_poi_test_verified and
            not v.orders and not v.trades for v in x))

if __name__=="__main__":unittest.main()
