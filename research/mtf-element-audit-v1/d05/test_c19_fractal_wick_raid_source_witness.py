"""C19 synthetic adversarial source geometries, never author market goldens."""
from __future__ import annotations
from dataclasses import replace
from decimal import Decimal as D
import unittest
from test_c18_native_15m_child_witness_graph import source,synth,native,STEP,SHA,SYM
from c16_c08_monthly_daily_htf_lineage import SEPT_START
from c19_fractal_wick_raid_source_witness import (
    observe_fractal_first_breaches,build_c19_fractal_wick_witness,C19Rejected)

def bars(patterns):
    return tuple(source(i,*p) for i,p in enumerate(patterns))

def upper_raid(*,kind="wick",next_bar=True):
    # Pivot BSL center bar 1 (high 110), known after bar 2 closes.
    p=[(100,108,99,104),(105,110,100,105),(105,108,100,105),
       (105,109,101,106)]
    if kind=="wick":
        p.append((107,111,105,108))
    elif kind=="body":
        p.append((107,111,105,111))
    elif kind=="no":
        p.append((107,109,105,108))
    else:
        raise AssertionError
    if next_bar:p.append((106,108,104,106))
    return bars(p)

def lower_raid(*,kind="wick",next_bar=True):
    p=[(105,110,100,105),(105,111,95,104),(105,109,101,106),
       (105,109,98,104)]
    p.append((100,103,94,100) if kind=="wick" else
             (100,103,94,93) if kind=="body" else (100,103,96,100))
    if next_bar:p.append((102,106,97,102))
    return bars(p)

def target_fixture():
    p=[(100,102,98,100)]*16+[(103,105,99,103)]*16+[(106,108,104,106)]*16
    p[44]=(106,108,103,106) # strict SSL center: 43,44,45; known after 45 closes
    p[48]=(104,105,102,104) # HTF first gap contact, first strict SSL wick breach
    p[49]=(104,105,104,104) # confirms raid fractal; no premature signal
    p[50]=(107,109,105,107)
    p[51]=(108,110,107,109)
    p[52]=(111,112,110,111) # closes 15m IMB after raid confirmation
    return synth(bars(p))

def ssl_raid(q):
    r=build_c19_fractal_wick_witness(q,as_of_ms=q.as_of_ms)
    return r,next(x for x in r.first_breaches if x.kind=="SSL" and x.breach_start_ms==SEPT_START+48*STEP)

class C19SourceWitnessTest(unittest.TestCase):
    def test_bsl_pivot_three_bar_known_only_at_right_close(self):
        f,b=observe_fractal_first_breaches(upper_raid(),SYM)
        x=next(x for x in f if x.kind=="BSL" and x.center_start_ms==SEPT_START+STEP)
        self.assertEqual(x.known_at_ms,SEPT_START+3*STEP)
        self.assertEqual(len(x.original_15m_rows),3)
    def test_bsl_first_clean_wick_raid_is_confirmed_next_close(self):
        _,bs=observe_fractal_first_breaches(upper_raid(),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="BSL")
        self.assertEqual(x.verdict,"FIRST_WICK_BREACH_CONFIRMED_FRACTAL_GEOMETRY")
        self.assertEqual(x.raid_confirmed_at_ms,SEPT_START+6*STEP)
        self.assertEqual(x.breach_bar_native_row_id,SHA+":"+str(SEPT_START+4*STEP))
        self.assertEqual(x.next_confirm_native_row_id,SHA+":"+str(SEPT_START+5*STEP))
        self.assertEqual(x.author_status,"AUTHOR_GOLDEN_SOURCE_UNAVAILABLE")
    def test_bsl_open_body_over_level_not_clean(self):
        _,bs=observe_fractal_first_breaches(upper_raid(kind="body"),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="BSL")
        self.assertEqual(x.verdict,"FIRST_BREACH_BODY_NOT_CLEAN_RAID")
        self.assertIsNone(x.raid_confirmed_at_ms)
    def test_bsl_unfinished_next_candle_marks_pending(self):
        _,bs=observe_fractal_first_breaches(upper_raid(next_bar=False),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="BSL")
        self.assertEqual(x.verdict,"FIRST_WICK_BREACH_AWAIT_NEXT_BAR")
        self.assertIsNone(x.raid_confirmed_at_ms)
    def test_bsl_no_breach_in_closed_prefix(self):
        _,bs=observe_fractal_first_breaches(upper_raid(kind="no"),SYM)
        x=next(x for x in bs if x.kind=="BSL" and x.pivot_known_at_ms==SEPT_START+3*STEP)
        self.assertEqual(x.verdict,"NO_FIRST_BREACH_IN_PREFIX")
    def test_bsl_wick_but_raid_not_fractal(self):
        p=[(100,108,99,104),(105,110,100,105),(105,108,100,105),
           (105,109,101,106),(107,111,105,108),(110,112,104,111)]
        _,bs=observe_fractal_first_breaches(bars(p),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="BSL")
        self.assertEqual(x.verdict,"FIRST_WICK_BREACH_NOT_CONFIRMED_FRACTAL")
    def test_ssl_first_wick_raid_geometry(self):
        _,bs=observe_fractal_first_breaches(lower_raid(),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="SSL")
        self.assertEqual(x.verdict,"FIRST_WICK_BREACH_CONFIRMED_FRACTAL_GEOMETRY")
    def test_ssl_body_breach_not_clean_raid(self):
        _,bs=observe_fractal_first_breaches(lower_raid(kind="body"),SYM)
        x=next(x for x in bs if x.breach_start_ms==SEPT_START+4*STEP and x.kind=="SSL")
        self.assertEqual(x.verdict,"FIRST_BREACH_BODY_NOT_CLEAN_RAID")
    def test_equal_highs_not_fake_three_bar_fractal(self):
        p=bars([(100,110,99,103),(100,110,99,103),(100,109,99,103)])
        a,_=observe_fractal_first_breaches(p,SYM)
        self.assertFalse(any(x.kind=="BSL" for x in a))
    def test_author_contact_level_and_fractal_raid_observed_separately(self):
        g,raid=ssl_raid(target_fixture())
        self.assertEqual(raid.raid_confirmed_at_ms,SEPT_START+50*STEP)
        associations=[x for x in g.first_contact_raid_coobservations if x.pivot_id==raid.pivot_id]
        self.assertGreaterEqual(len(associations),1)
        self.assertTrue(all(x.breach_start_ms==SEPT_START+48*STEP for x in associations))
        self.assertTrue(all(x.later_15m_gap_geometry_count>0 for x in associations))
        self.assertTrue(all(x.interpretation.endswith("NOT_CAUSALLY_AUTHOR_ATTRIBUTED") for x in associations))
    def test_higher_level_contact_is_not_approved_stronghl(self):
        g,_=ssl_raid(target_fixture())
        self.assertEqual(g.author_approved_stronghl,0)
        self.assertEqual(g.author_approved_vc,0)
        self.assertEqual(g.candidate_bos_3m5m,0)
        self.assertEqual(g.readiness,"NOT_TRADE_READY")
    def test_15m_gap_from_raid_candle_itself_must_not_be_later_confirmation(self):
        g,_=ssl_raid(target_fixture())
        a=next(x for x in g.first_contact_raid_coobservations if x.breach_start_ms==SEPT_START+48*STEP)
        self.assertGreaterEqual(a.later_15m_gap_geometry_count,1)
        self.assertEqual(a.aligned_direction_gap_count+a.opposite_direction_gap_count,
                         a.later_15m_gap_geometry_count+a.later_1h_gap_geometry_count)
    def test_suffix_does_not_change_past_complete_prefix(self):
        full=target_fixture()
        past=synth(full.native_15m_closed[:50])
        a=build_c19_fractal_wick_witness(past,as_of_ms=past.as_of_ms)
        b=build_c19_fractal_wick_witness(full,as_of_ms=past.as_of_ms)
        self.assertEqual(a,b)
    def test_raid_unconfirmed_until_following_candle(self):
        q=target_fixture()
        earlier=synth(q.native_15m_closed[:49])
        _,b=ssl_raid(earlier)
        self.assertEqual(b.verdict,"FIRST_WICK_BREACH_AWAIT_NEXT_BAR")
        self.assertIsNone(b.raid_confirmed_at_ms)
        g=build_c19_fractal_wick_witness(earlier,as_of_ms=earlier.as_of_ms)
        self.assertEqual(len(g.first_contact_raid_coobservations),0)
    def test_zero_future_asof(self):
        q=target_fixture()
        with self.assertRaisesRegex(C19Rejected,"INVALID_FUTURE_15M_ASOF"):
            build_c19_fractal_wick_witness(q,as_of_ms=q.as_of_ms+STEP)
    def test_subbar_lookahead(self):
        q=target_fixture()
        with self.assertRaisesRegex(C19Rejected,"INVALID_FUTURE_15M_ASOF"):
            build_c19_fractal_wick_witness(q,as_of_ms=q.as_of_ms-1)
    def test_no_self_claimed_ready(self):
        q=target_fixture()
        with self.assertRaisesRegex(C19Rejected,"INVALID_C18_PRICE_LINEAGE"):
            build_c19_fractal_wick_witness(replace(q,readiness="READY"),as_of_ms=q.as_of_ms)
    def test_tampered_native_15m_source_price_rejected(self):
        q=target_fixture()
        src=q.native_15m_closed
        corrupt=replace(src[44],high=D(0))
        with self.assertRaisesRegex(C19Rejected,"INVALID_C18_PRICE_LINEAGE"):
            build_c19_fractal_wick_witness(replace(q,native_15m_closed=src[:44]+(corrupt,)+src[45:]),as_of_ms=q.as_of_ms)
    def test_tampered_1h_aggregation_rejected(self):
        q=target_fixture()
        h=q.derived_1h_closed
        with self.assertRaisesRegex(C19Rejected,"INVALID_C18_PRICE_LINEAGE"):
            build_c19_fractal_wick_witness(replace(q,derived_1h_closed=h[:-1]),as_of_ms=q.as_of_ms)
    def test_not_a_review(self):
        with self.assertRaisesRegex(C19Rejected,"NOT_A_C16_REVIEW"):
            build_c19_fractal_wick_witness(None,as_of_ms=SEPT_START)
    def test_time_ordering_and_no_3m_5m_author_bos(self):
        q=target_fixture()
        g,_=ssl_raid(q)
        self.assertTrue(all(x.raid_known_at_ms>x.first_ltf_contact_known_at_ms
                            for x in g.first_contact_raid_coobservations))
        self.assertIn("NO_32DAY_NATIVE_3M5M",g.limitations)
        self.assertEqual(g.candidate_bos_3m5m,0)

if __name__=="__main__":unittest.main()
