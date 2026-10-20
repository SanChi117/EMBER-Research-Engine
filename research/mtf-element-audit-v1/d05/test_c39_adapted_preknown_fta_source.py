"""C39 source-preknown FTA-family hypotheses: no TARGET/ORDER inference."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import SEPT_START,THREE
from c21b_original_3m_raid_break_geometry import _source,_hours
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c28_source_fta_inventory import classic_1h_imb,Gap
from c39_adapted_preknown_fta_source import (
    FTA_VARIANTS,confirmed_1h_fractal_obstacles,
    source_preknown_potential_obstacles,classify_potential_fta,
    scan_original_preknown_fta)
from test_c21b_native_3m_vs_5m import make3

def fixture():
    src=make3(size=220)
    event=scan_original_3m_adapted(src,as_of_ms=src.as_of_ms).routes[0].events[0]
    rows=_source(src,src.as_of_ms)
    return src,event,rows

def synthetic_gap(e,rows,offset,*,early=True):
    px=D(e.break_close)
    if e.side=="LONG":bottom,top=px+D(str(offset)),px+D(str(offset+1))
    else:bottom,top=px-D(str(offset+1)),px-D(str(offset))
    when=e.break_bar_start_ms-THREE if early else e.break_bar_start_ms+THREE
    return Gap("BULL_CLASSIC_IMB",bottom,top,
       when-3*3600000,when-3600000,when,
       (rows[0].raw_id,rows[20].raw_id,rows[40].raw_id))

def fake_fractal(e,rows,offset,*,early=True):
    level=D(e.break_close)+(D(str(offset)) if e.side=="LONG" else -D(str(offset)))
    known=e.break_bar_start_ms-THREE if early else e.break_bar_start_ms+THREE
    return (("BSL_1H_FRACTAL" if e.side=="LONG" else "SSL_1H_FRACTAL",
             level,known,rows[0].raw_id,rows[19].raw_id),)

class C39PotentialFTAControl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src,cls.event,cls.rows=fixture()

    def test_three_explicit_fta_hypotheses(self):
        self.assertEqual(len(FTA_VARIANTS),3)
        self.assertEqual(len(set(FTA_VARIANTS)),3)
    def test_fully_source_no_instructor_fta(self):
        for v in FTA_VARIANTS:
            r=classify_potential_fta(self.event,self.rows,(),(),v)
            self.assertFalse(r.author_selected_FTA)
            self.assertFalse(r.paper_signal_allowed)
            self.assertEqual((r.orders,r.trades,r.target_orders),((),(),()))
            self.assertEqual(r.readiness,"NOT_TRADE_READY")
    def test_empty_obstacles_do_not_invent_a_target(self):
        r=classify_potential_fta(self.event,self.rows,(),(),FTA_VARIANTS[0])
        self.assertIsNone(r.selected_potential_obstacle)
        self.assertEqual(r.source_preknown_candidate_count,0)
    def test_fractal_only_ahead_may_be_potential_not_author_FTA(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,fake_fractal(e,self.rows,4),(),FTA_VARIANTS[0])
        self.assertIsNotNone(r.selected_potential_obstacle)
        self.assertFalse(r.selected_potential_obstacle.author_priority_attested)
        self.assertFalse(r.selected_potential_obstacle.mitigation_or_freshness_attested)
    def test_prior_classic_IMB_only_is_potential_obstacle(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,(),(synthetic_gap(e,self.rows,3),),FTA_VARIANTS[2])
        self.assertEqual(r.selected_potential_obstacle.kind,"BULL_CLASSIC_IMB")
    def test_closest_all_chooses_nearest_ahead_regardless_family(self):
        e=self.event
        f=fake_fractal(e,self.rows,5)
        g=synthetic_gap(e,self.rows,2)
        r=classify_potential_fta(e,self.rows,f,(g,),FTA_VARIANTS[0])
        self.assertEqual(r.selected_potential_obstacle.kind,"BULL_CLASSIC_IMB")
    def test_fractal_priority_not_pretending_global_nearest(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,fake_fractal(e,self.rows,5),
             (synthetic_gap(e,self.rows,2),),FTA_VARIANTS[1])
        self.assertIn("FRACTAL",r.selected_potential_obstacle.kind)
    def test_imb_priority_not_pretending_global_nearest(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,fake_fractal(e,self.rows,2),
             (synthetic_gap(e,self.rows,5),),FTA_VARIANTS[2])
        self.assertIn("IMB",r.selected_potential_obstacle.kind)
    def test_fractal_priority_fallback_to_classic_gap(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,(),(synthetic_gap(e,self.rows,3),),FTA_VARIANTS[1])
        self.assertIn("IMB",r.selected_potential_obstacle.kind)
    def test_imb_priority_fallback_to_fractal(self):
        e=self.event
        r=classify_potential_fta(e,self.rows,fake_fractal(e,self.rows,3),(),FTA_VARIANTS[2])
        self.assertIn("FRACTAL",r.selected_potential_obstacle.kind)
    def test_future_fractal_rejected_from_obstacle_source_set(self):
        e=self.event
        r=source_preknown_potential_obstacles(e,self.rows,
             fake_fractal(e,self.rows,3,early=False),())
        self.assertEqual(r,())
    def test_future_gap_rejected_from_source_set(self):
        e=self.event
        self.assertEqual(source_preknown_potential_obstacles(e,self.rows,(),
           (synthetic_gap(e,self.rows,3,early=False),)),())
    def test_obstacle_distance_strictly_positive(self):
        e=self.event
        a=source_preknown_potential_obstacles(e,self.rows,fake_fractal(e,self.rows,2),
                          (synthetic_gap(e,self.rows,3),))
        self.assertTrue(a and all(D(x.distance_from_retrospective_break_close)>0 for x in a))
    def test_gap_containing_BOS_price_is_not_assumed_future_fta(self):
        e=self.event;px=D(e.break_close)
        g=Gap("BULL_CLASSIC_IMB",px-D("1"),px+D("1"),
            0,0,e.break_bar_start_ms-THREE,("a","b","c"))
        self.assertEqual(source_preknown_potential_obstacles(e,self.rows,(),(g,)),())
    def test_gap_equality_to_entry_is_not_forward_obstacle(self):
        e=self.event;px=D(e.break_close)
        g=Gap("BULL_CLASSIC_IMB",px,px+D("1"),0,0,
            e.break_bar_start_ms-THREE,("a","b","c")) if e.side=="LONG" else (
            Gap("BULL_CLASSIC_IMB",px-D("1"),px,0,0,
             e.break_bar_start_ms-THREE,("a","b","c")))
        self.assertEqual(source_preknown_potential_obstacles(e,self.rows,(),(g,)),())
    def test_not_count_wrong_fractal_side_as_forward_target(self):
        e=self.event
        wrong_kind="SSL_1H_FRACTAL" if e.side=="LONG" else "BSL_1H_FRACTAL"
        f=(wrong_kind,D(e.break_close)+D("2"),e.break_bar_start_ms-THREE,
           self.rows[0].raw_id,self.rows[19].raw_id)
        self.assertEqual(source_preknown_potential_obstacles(e,self.rows,(f,),()),())
    def test_unknown_selector_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_ADAPTED_FTA"):
            classify_potential_fta(self.event,self.rows,(),(),"PERFECT_WIN_RATE")
    def test_forged_author_bos_refused(self):
        with self.assertRaisesRegex(ValueError,"FORGED_BOS_READY"):
            source_preknown_potential_obstacles(replace(self.event,author_bos_approved=True),
                 self.rows,(),())
    def test_forged_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_BOS_READY"):
            source_preknown_potential_obstacles(replace(self.event,orders=("live",)),
                 self.rows,(),())
    def test_forged_paper_trade_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_BOS_READY"):
            source_preknown_potential_obstacles(replace(self.event,paper_trade_allowed=True),
                 self.rows,(),())
    def test_wrong_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_SYMBOL_MISMATCH"):
            source_preknown_potential_obstacles(replace(self.event,symbol="ETHUSDT"),
                 self.rows,(),())
    def test_bad_bos_original_row_SHA_rejected(self):
        with self.assertRaisesRegex(ValueError,"BAR_SHA_PRICE_DRIFT"):
            source_preknown_potential_obstacles(replace(self.event,break_original_native3m_row_id="fake"),
                 self.rows,(),())
    def test_bad_bos_close_source_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"BAR_SHA_PRICE_DRIFT"):
            source_preknown_potential_obstacles(replace(self.event,break_close="NaN"),
                 self.rows,(),())
    def test_bad_fractal_price_in_relevant_side_rejected(self):
        e=self.event
        f=fake_fractal(e,self.rows,3)
        forged=(f[0][0],D("NaN"),f[0][2],f[0][3],f[0][4])
        with self.assertRaisesRegex(ValueError,"INVALID_1H_SOURCE_FRACTAL"):
            source_preknown_potential_obstacles(e,self.rows,(forged,),())
    def test_bad_classic_gap_kind_rejected(self):
        e=self.event
        g=replace(synthetic_gap(e,self.rows,3),kind="FAKE_GAP")
        with self.assertRaisesRegex(ValueError,"INVALID_PRIOR_CLASSIC_IMB"):
            source_preknown_potential_obstacles(e,self.rows,(),(g,))
    def test_bad_classic_gap_negative_width_rejected(self):
        e=self.event
        g=synthetic_gap(e,self.rows,3)
        g=replace(g,top=g.bottom)
        with self.assertRaisesRegex(ValueError,"INVALID_PRIOR_CLASSIC_IMB"):
            source_preknown_potential_obstacles(e,self.rows,(),(g,))
    def test_obstacles_in_test_from_real_hour_fvg_source(self):
        h=_hours(self.rows)
        f=confirmed_1h_fractal_obstacles(h)
        g=classic_1h_imb(h)
        result=source_preknown_potential_obstacles(self.event,self.rows,f,g)
        self.assertTrue(all(x.source_known_ms<=self.event.break_bar_start_ms for x in result))
    def test_fractal_native_hour_count_is_exact(self):
        h=_hours(self.rows)
        self.assertTrue(all(len(x.native_rows)==20 for x in h))
        self.assertIsInstance(confirmed_1h_fractal_obstacles(h),tuple)
    def test_asof_source_prefix_does_not_change_past(self):
        src=self.src
        end=self.event.break_bar_closed_known_ms
        n=(end-SEPT_START)//THREE
        physically=replace(src,as_of_ms=end,original_3m_closed=src.original_3m_closed[:n])
        a=scan_original_preknown_fta(src,as_of_ms=end)
        b=scan_original_preknown_fta(physically,as_of_ms=end)
        self.assertEqual(a,b)
    def test_after_BOS_potential_FTA_matrix_4_by_3(self):
        r=scan_original_preknown_fta(self.src,as_of_ms=self.src.as_of_ms)
        self.assertEqual(len(r.routes),12)
        self.assertEqual(len(r.bos_hypotheses),4)
        self.assertEqual(len(r.fta_hypotheses),3)
    def test_no_source_fta_promoted_author_ready(self):
        r=scan_original_preknown_fta(self.src,as_of_ms=self.src.as_of_ms)
        self.assertEqual(r.author_fta_goldens,0)
        self.assertEqual(r.author_approved_targets,0)
        self.assertEqual(r.orders,())
        self.assertEqual(r.trades,())
        self.assertTrue(all(not w.author_selected_FTA and not w.target_orders
           for route in r.routes for w in route.observations))
    def test_forged_source_ready_rejected(self):
        s=replace(self.src,readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            scan_original_preknown_fta(s,as_of_ms=s.as_of_ms)
    def test_forged_native_original3m_SHA_rejected(self):
        bars=list(self.src.original_3m_closed)
        bars[22]=replace(bars[22],raw_id="FORGED")
        s=replace(self.src,original_3m_closed=tuple(bars))
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            scan_original_preknown_fta(s,as_of_ms=s.as_of_ms)

if __name__=="__main__":unittest.main()
