"""C40 source-only prior 1H obstacle contact, before BOS bar start."""
import unittest
from dataclasses import replace
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import _source,_hours
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c39_adapted_preknown_fta_source import (
    scan_original_preknown_fta,confirmed_1h_fractal_obstacles,PotentialObstacle)
from c28_source_fta_inventory import classic_1h_imb
from c40_pre_bos_fta_touch_state import (
    STATES,classify_pre_bos_obstacle_touch,inspect_original_fta_prior_touch)
from test_c21b_native_3m_vs_5m import make3

def setup():
    source=make3(size=220)
    rows=_source(source,source.as_of_ms)
    bos=scan_original_3m_adapted(source,as_of_ms=source.as_of_ms)
    fta=scan_original_preknown_fta(source,as_of_ms=source.as_of_ms)
    event=bos.routes[0].events[0]
    fragments=_hours(rows)
    return (source,rows,event,
            confirmed_1h_fractal_obstacles(fragments),classic_1h_imb(fragments),fta)

class C40PriorObstacleTouchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src,cls.rows,cls.event,cls.fractals,cls.gaps,cls.fta=setup()
    def case(self,selected=None):
        return classify_pre_bos_obstacle_touch(self.event,selected,self.rows,
                       self.fractals,self.gaps,"CLOSEST_PRIOR_1H_OBSTACLE_V1")
    def test_four_explicit_states(self):
        self.assertEqual(len(STATES),4)
        self.assertEqual(len(set(STATES)),4)
    def test_no_candidate_stays_no_candidate_not_target(self):
        w=self.case()
        self.assertEqual(w.classification,"NO_PREKNOWN_FTA_CANDIDATE")
        self.assertIsNone(w.source_potential_fta)
    def test_empty_approval_always(self):
        w=self.case()
        self.assertEqual((w.orders,w.trades),((),()))
        self.assertFalse(w.order_approval)
        self.assertFalse(w.author_freshness_certified)
        self.assertFalse(w.author_target_certified)
    def test_forged_1h_potential_obstacle_ready_refused(self):
        e=self.event
        forged=PotentialObstacle("BSL_1H_FRACTAL",e.break_bar_start_ms-THREE,
                      "123",self.rows[0].raw_id,self.rows[19].raw_id,"1",
                      author_priority_attested=True)
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_FTA"):
            self.case(forged)
    def test_forged_source_freshness_flag_refused(self):
        e=self.event
        forged=PotentialObstacle("BSL_1H_FRACTAL",e.break_bar_start_ms-THREE,
                  "123",self.rows[0].raw_id,self.rows[19].raw_id,"1",
                  mitigation_or_freshness_attested=True)
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_FTA"):
            self.case(forged)
    def test_future_1h_fta_cannot_influence_existing_bos(self):
        e=self.event
        f=PotentialObstacle("BSL_1H_FRACTAL",e.break_bar_start_ms+THREE,
                "123",self.rows[0].raw_id,self.rows[19].raw_id,"1")
        with self.assertRaisesRegex(ValueError,"FUTURE_1H_OBSTACLE"):
            self.case(f)
    def test_unmatched_1h_fractal_price_or_SHA_rejected(self):
        e=self.event
        f=PotentialObstacle("BSL_1H_FRACTAL" if e.side=="LONG" else "SSL_1H_FRACTAL",
                    e.break_bar_start_ms-THREE,"99999999",
                    self.rows[0].raw_id,self.rows[19].raw_id,"1")
        with self.assertRaisesRegex(ValueError,"UNMATCHED_ORIGINAL_1H_FRACTAL"):
            self.case(f)
    def test_unmatched_original_classic_IMB_rejected(self):
        e=self.event
        f=PotentialObstacle("BULL_CLASSIC_IMB",
                    e.break_bar_start_ms-THREE,"99999999",
                    self.rows[0].raw_id,self.rows[19].raw_id,"1")
        with self.assertRaisesRegex(ValueError,"UNMATCHED_ORIGINAL_CLASSIC_IMB"):
            self.case(f)
    def test_unregistered_fta_family_rejected(self):
        e=self.event
        f=PotentialObstacle("PROFIT_TARGET",e.break_bar_start_ms-THREE,
                   "123",self.rows[0].raw_id,self.rows[19].raw_id,"1")
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_FTA_FAMILY"):
            self.case(f)
    def test_nan_source_price_rejected(self):
        e=self.event
        f=PotentialObstacle("BULL_CLASSIC_IMB",e.break_bar_start_ms-THREE,
                    "NaN",self.rows[0].raw_id,self.rows[19].raw_id,"1")
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_OBSTACLE_LEVEL"):
            self.case(f)
    def test_forged_original_bos_ready_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_BOS_OR_TRADE"):
            classify_pre_bos_obstacle_touch(replace(self.event,author_bos_approved=True),
                   None,self.rows,self.fractals,self.gaps,"CLOSEST_PRIOR_1H_OBSTACLE_V1")
    def test_forged_source_bos_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_BOS_OR_TRADE"):
            classify_pre_bos_obstacle_touch(replace(self.event,orders=("fake",)),
                  None,self.rows,self.fractals,self.gaps,"CLOSEST_PRIOR_1H_OBSTACLE_V1")
    def test_original_source_12_route_touch_matrix(self):
        r=inspect_original_fta_prior_touch(self.src,as_of_ms=self.src.as_of_ms)
        self.assertEqual(r["route_count"],12)
        self.assertEqual(r["readiness"],"NOT_TRADE_READY")
    def test_source_12_routes_each_states_add_up(self):
        r=inspect_original_fta_prior_touch(self.src,as_of_ms=self.src.as_of_ms)
        self.assertTrue(all(sum(x["states"].values())==x["contexts"] for x in r["routes"]))
    def test_no_author_freshness_or_orders_in_any_source_route(self):
        r=inspect_original_fta_prior_touch(self.src,as_of_ms=self.src.as_of_ms)
        self.assertEqual((r["author_fta_freshness_goldens"],r["orders"],r["trades"]),(0,(),()))
        for route in r["routes"]:
            for x in route["observations"]:
                self.assertFalse(x.author_freshness_certified)
                self.assertFalse(x.author_target_certified)
                self.assertFalse(x.order_approval)
    def test_full_source_asof_equals_physically_cut_original3m(self):
        end=self.event.break_bar_closed_known_ms
        n=(end-SEPT_START)//THREE
        prefix=replace(self.src,as_of_ms=end,original_3m_closed=self.src.original_3m_closed[:n])
        self.assertEqual(inspect_original_fta_prior_touch(self.src,as_of_ms=end),
                         inspect_original_fta_prior_touch(prefix,as_of_ms=end))
    def test_forged_raw_3m_SHA_source_rejected(self):
        bars=list(self.src.original_3m_closed)
        bars[41]=replace(bars[41],raw_id="FAKE")
        source=replace(self.src,original_3m_closed=tuple(bars))
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_original_fta_prior_touch(source,as_of_ms=source.as_of_ms)
    def test_forged_source_ready_rejected(self):
        source=replace(self.src,readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_original_fta_prior_touch(source,as_of_ms=source.as_of_ms)
    def test_prior_1h_obstacles_are_not_claimed_new_pnl(self):
        r=inspect_original_fta_prior_touch(self.src,as_of_ms=self.src.as_of_ms)
        self.assertNotIn("win_rate",r)
        self.assertNotIn("profit",r)
if __name__=="__main__":unittest.main()
