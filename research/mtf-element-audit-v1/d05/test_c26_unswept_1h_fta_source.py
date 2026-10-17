"""C26 adversarial test controls: original history never creates trade approval."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace as NS
from c20b_hourly_fractal_source_observer import HourFractal
from c21_native3m_source_bridge import SEPT_START, THREE
from c26_unswept_1h_fta_source import (
    inspect_c26,level_history,_opposing_candidates,_intervening,
    _same_bar_unknown)
from test_c21b_native_3m_vs_5m import make3

def pivot(kind="BSL",level="100",center=1,known=10):
    return HourFractal(kind,D(level),center,known,("verified-row-a","b","c"))

def bar(start,high="99",low="90",close="95"):
    return NS(start_ms=start,known_ms=start+3,high=D(high),
              low=D(low),close=D(close),raw_id="source-"+str(start))

class C26ReadOnlyControls(unittest.TestCase):
    def test_wick_cross_previously_removes_target(self):
        a=level_history(pivot(),(bar(10,high="101",close="99"),),break_start_ms=20)
        self.assertEqual(a.state,"WICK_CROSS")
        self.assertEqual(a.first_wick_cross_ms,10)
        self.assertIsNone(a.first_body_close_through_ms)
    def test_body_close_through_supersedes_earlier_wick(self):
        x=(bar(10,high="102",close="99"),bar(13,high="103",close="101"))
        a=level_history(pivot(),x,break_start_ms=20)
        self.assertEqual(a.state,"BODY_CLOSE_THROUGH")
        self.assertEqual(a.first_wick_cross_ms,10)
        self.assertEqual(a.first_body_close_through_ms,13)
    def test_equal_price_is_not_wick_cross(self):
        a=level_history(pivot(),(bar(10,high="100",close="99"),),break_start_ms=20)
        self.assertEqual(a.state,"EQUALITY_TOUCH_UNRESOLVED")
        self.assertIsNone(a.first_wick_cross_ms)
    def test_no_3m_cross_means_intact_in_source_window_only(self):
        a=level_history(pivot(),(bar(10),bar(13)),break_start_ms=20)
        self.assertEqual(a.state,"NO_CROSS_OBSERVED")
    def test_bos_bar_and_future_are_never_checked(self):
        a=level_history(pivot(),(bar(10),bar(13,high="104"),
              bar(16,high="120")),break_start_ms=13)
        self.assertEqual(a.state,"NO_CROSS_OBSERVED")
    def test_unknown_1h_fractal_before_confirmation_rejected(self):
        with self.assertRaisesRegex(ValueError,"TARGET_NOT_PREKNOWN"):
            level_history(pivot(known=25),(bar(25),),break_start_ms=20)
    def test_wrong_side_equal_and_future_target_excluded(self):
        pp=(pivot("BSL","100",1,10),pivot("BSL","110",2,30),
            pivot("SSL","90",3,10))
        self.assertEqual(_opposing_candidates(pp,"LONG",D("100"),20),[])
        self.assertEqual([x.level for x in _opposing_candidates(pp,"SHORT",D("100"),20)],[D("90")])
        self.assertEqual(_opposing_candidates(pp,"LONG",D("100"),40)[0].level,D("110"))
    def test_multiple_preknown_obstacles_and_future_excluded(self):
        pp=(pivot("BSL","96",1,10),pivot("SSL","94",2,10),
            pivot("BSL","91",3,25),pivot("BSL","101",4,10))
        self.assertEqual(len(_intervening(pp,D("100"),D("90"),"SHORT",20)),2)
        self.assertEqual(_intervening(pp,D("100"),None,"SHORT",20),())
        self.assertEqual(len(_intervening(pp,D("90"),D("100"),"LONG",20)),2)
    def test_missing_target_returns_empty(self):
        self.assertEqual(_opposing_candidates((pivot("BSL","99"),),
                     "LONG",D("100"),30),[])
    def test_ssl_wick_and_close_direction(self):
        a=level_history(pivot("SSL","90"),(bar(10,high="97",low="89",close="91"),),
                        break_start_ms=20)
        self.assertEqual(a.state,"WICK_CROSS")
        b=level_history(pivot("SSL","90"),(bar(10,high="97",low="89",close="89.5"),),
                        break_start_ms=20)
        self.assertEqual(b.state,"BODY_CLOSE_THROUGH")
    def test_bad_source_price_and_unsupported_pivot_refused(self):
        with self.assertRaisesRegex(ValueError,"BAD_ORIGINAL_PRICE"):
            level_history(pivot(),(bar(10,high="NaN"),),break_start_ms=20)
        with self.assertRaisesRegex(ValueError,"INVALID_1H_FRACTAL"):
            level_history(pivot("EQH"),(),break_start_ms=20)
    def test_same_bar_both_bounds_do_not_prove_order(self):
        x=bar(10,high="105",low="88",close="99")
        self.assertTrue(_same_bar_unknown("SHORT",x,D("103"),D("90")))
        self.assertTrue(_same_bar_unknown("LONG",x,D("90"),D("103")))
        self.assertFalse(_same_bar_unknown("SHORT",x,D("110"),D("90")))
    def test_source_cannot_approve_any_entry(self):
        x=make3()
        r=inspect_c26(x,as_of_ms=x.as_of_ms)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        self.assertEqual(r.author_approved_trades,0)
        self.assertEqual(r.research_single_cases,len(r.cases))
        self.assertTrue(all(not c.author_approved and c.readiness=="NOT_TRADE_READY"
                            and "UNKNOWN_AUTHOR_SL_BUFFER" in c.reasons for c in r.cases))
    def test_independent_asof_prefix_equals_truncated_3m_source(self):
        x=make3()
        cut=SEPT_START+141*THREE
        y=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        self.assertEqual(inspect_c26(x,as_of_ms=cut),inspect_c26(y,as_of_ms=cut))
    def test_forged_ready_and_row_id_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c26(replace(x,readiness="READY"),as_of_ms=x.as_of_ms)
        rows=x.original_3m_closed
        wrong=replace(x,original_3m_closed=rows[:100]+
                      (replace(rows[100],raw_id="tampered"),)+rows[101:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c26(wrong,as_of_ms=wrong.as_of_ms)
    def test_original_zip_sha_tampering_rejected(self):
        x=make3()
        shas=("0"*64,)+x.original_zip_shas[1:]
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c26(replace(x,original_zip_shas=shas),as_of_ms=x.as_of_ms)
    def test_unordered_source_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNORDERED_OR_UNCLOSED_ROW"):
            level_history(pivot(),(bar(13),bar(10)),break_start_ms=25)
    def test_author_session_and_fta_status_remain_unknown(self):
        x=make3()
        r=inspect_c26(x,as_of_ms=x.as_of_ms)
        for c in r.cases:
            self.assertIn("UNKNOWN_AUTHOR_SESSION_DST",c.reasons)
            self.assertIn("UNKNOWN_AUTHOR_BOS_GOLDENS",c.reasons)
            self.assertTrue(any("FTA" in v for v in c.reasons))
if __name__=="__main__": unittest.main()
