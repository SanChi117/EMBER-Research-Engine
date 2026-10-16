"""B1/C18: synthetic adversarial geometry tests, never historical market goldens."""
from __future__ import annotations
from dataclasses import replace
from decimal import Decimal as D
import unittest
from c16_c08_monthly_daily_htf_lineage import (
    NativeKline, ExtendedHTFReview, SEPT_START, TF_MS, _combine)
from c18_native_15m_child_witness_graph import (
    build_lower_tf_witness_graph,C18Rejected,AUTHOR_UNKNOWN)

STEP=TF_MS["15m"]
SHA="a"*64
SYM="BTCUSDT"

def source(i,o,h,l,c):
    t=SEPT_START+i*STEP
    return NativeKline(SYM,"15m",t,t+STEP,D(o),D(h),D(l),D(c),D(1),
                       SHA+":"+str(t),SHA)

def native(with_touch=True):
    patterns=[(100,102,98,100)]*16+[(103,105,99,103)]*16+[(106,108,104,106)]*16
    if with_touch:
        patterns += [(103,105,101,103),(104,105,103,104),
                     (104,108,104,107),(107,109,106,108)]
        patterns += [(110,115,109,112)]*12
    else:
        patterns += [(110,115,109,112)]*16
    return tuple(source(i,*p) for i,p in enumerate(patterns))

def synth(rows=None,asof=None):
    rows=native() if rows is None else tuple(rows)
    if asof is None:asof=rows[-1].known_at_ms
    h=tuple(_combine(rows[i:i+4],"1h") for i in range(0,len(rows)//4*4,4))
    f=tuple(_combine(rows[i:i+16],"4h") for i in range(0,len(rows)//16*16,16))
    return ExtendedHTFReview(SYM,asof,rows,(),h,f,0)
def run(q=None,cutoff=None):
    if q is None:q=synth()
    return build_lower_tf_witness_graph(q,as_of_ms=q.as_of_ms if cutoff is None else cutoff)
def parent(g):
    return tuple(p for p in g.parents if p.parent_tf=="4h" and p.parent_side=="LONG")

class C18NativeChildWitness(unittest.TestCase):
    def test_parent_4h_remains_unapproved(self):
        g=run()
        self.assertEqual(len(parent(g)),1)
        self.assertEqual(g.author_status,AUTHOR_UNKNOWN)
        self.assertEqual(g.readiness,"NOT_TRADE_READY")
        self.assertEqual(g.attribution,"NO_AUTOMATIC_PARENT_OR_VC_SELECTION")
    def test_true_contact_follows_third_closed_four_hour_bar(self):
        g=run()
        p=parent(g)[0]
        self.assertEqual(p.level_known_at_ms,SEPT_START+48*STEP)
        self.assertEqual(p.first_closed_15m_contact_start_ms,SEPT_START+48*STEP)
        self.assertEqual(p.first_closed_15m_contact_known_at_ms,SEPT_START+49*STEP)
        self.assertEqual(p.first_closed_15m_source_row_id,SHA+":"+str(SEPT_START+48*STEP))
    def test_last_parent_bar_not_mistaken_for_later_test(self):
        g=run(synth(native()[:48]))
        p=parent(g)[0]
        self.assertEqual(p.first_closed_15m_contact_known_at_ms,None)
        self.assertEqual(p.state,"NO_NATIVE_15M_CONTACT")
    def test_after_contact_three_candle_gap_at_15m(self):
        g=run()
        p=parent(g)[0]
        edges=[x for x in g.edges if x.parent_id==p.parent_id and ":15m:" in x.child_id]
        self.assertTrue(any(e.child_known_at_ms==SEPT_START+52*STEP for e in edges))
        self.assertTrue(all(e.child_known_at_ms>e.contact_known_at_ms for e in edges))
        self.assertTrue(all(e.certification.endswith("NOT_AUTHOR_PARENT_VC") for e in edges))
    def test_child_three_bars_must_start_after_contact_is_closed(self):
        g=run()
        p=parent(g)[0]
        for e in g.edges:
            if e.parent_id!=p.parent_id:continue
            c=next(c for c in g.children_15m+g.children_1h if c.id==e.child_id)
            self.assertGreaterEqual(c.origin_start_ms,p.first_closed_15m_contact_known_at_ms)
    def test_no_contact_no_children_even_if_far_later_gap(self):
        g=run(synth(native(with_touch=False)))
        p=parent(g)[0]
        self.assertEqual(p.state,"NO_NATIVE_15M_CONTACT")
        self.assertFalse(any(e.parent_id==p.parent_id for e in g.edges))
    def test_no_forced_directional_vc_filter(self):
        g=run()
        self.assertTrue(all(e.temporal_relation=="THREE_CHILD_SOURCE_BARS_AFTER_FIRST_15M_CONTACT" for e in g.edges))
    def test_source_ids_present_for_all_1h_15m_gap_children(self):
        g=run()
        for c in g.children_1h+g.children_15m:
            self.assertEqual(c.source_zip_shas,(SHA,))
            self.assertEqual(len(c.source_native_15m_rows),12 if c.tf=="1h" else 3)
    def test_contact_count_is_not_author_first_test_approval(self):
        p=parent(run())[0]
        self.assertGreater(p.subsequent_15m_contacts,0)
        self.assertEqual(p.author_status,AUTHOR_UNKNOWN)
    def test_previous_closed_prefix_immutable_by_later_bars(self):
        full=synth()
        earlier=synth(native()[:48])
        cutoff=earlier.as_of_ms
        a=run(earlier)
        b=run(full,cutoff=cutoff)
        self.assertEqual(a,b)
    def test_future_asof_cannot_be_requested(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"FUTURE_OR_UNCLOSED_ASOF"):
            run(q,cutoff=q.as_of_ms+STEP)
    def test_open_15m_asof_not_allowed(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"FUTURE_OR_UNCLOSED_ASOF"):
            run(q,cutoff=q.as_of_ms-1)
    def test_cross_symbol_original_15m_rejected(self):
        q=synth()
        bad=replace(q.native_15m_closed[5],symbol="ETHUSDT")
        with self.assertRaisesRegex(C18Rejected,"CROSS_SYMBOL_OR_NON_NATIVE_15M"):
            run(replace(q,native_15m_closed=q.native_15m_closed[:5]+(bad,)+q.native_15m_closed[6:]))
    def test_wrong_native_15m_tf_rejected(self):
        q=synth()
        bad=replace(q.native_15m_closed[5],tf="5m")
        with self.assertRaisesRegex(C18Rejected,"CROSS_SYMBOL_OR_NON_NATIVE_15M"):
            run(replace(q,native_15m_closed=q.native_15m_closed[:5]+(bad,)+q.native_15m_closed[6:]))
    def test_gap_in_15m_history_rejected(self):
        q=synth()
        rows=q.native_15m_closed
        with self.assertRaisesRegex(C18Rejected,"INCOMPLETE_FUTURE_OR_DISORDERED_NATIVE_15M"):
            run(replace(q,native_15m_closed=rows[:5]+rows[6:]))
    def test_forged_original_sha_rejected(self):
        q=synth()
        bad=replace(q.native_15m_closed[3],origin_zip_sha256="b"*64)
        with self.assertRaisesRegex(C18Rejected,"INVALID_NATIVE_15M_SOURCE_SHA"):
            run(replace(q,native_15m_closed=q.native_15m_closed[:3]+(bad,)+q.native_15m_closed[4:]))
    def test_forged_original_price_rejected(self):
        q=synth()
        bad=replace(q.native_15m_closed[3],high=D(99))
        with self.assertRaisesRegex(C18Rejected,"MUTATED_OR_NONFINITE_NATIVE_15M_PRICE"):
            run(replace(q,native_15m_closed=q.native_15m_closed[:3]+(bad,)+q.native_15m_closed[4:]))
    def test_changed_1h_aggregated_price_rejected(self):
        q=synth()
        bad=replace(q.derived_1h_closed[1],high=D(500))
        with self.assertRaisesRegex(C18Rejected,"DERIVED_1H_SOURCE_GEOMETRY_MISMATCH"):
            run(replace(q,derived_1h_closed=q.derived_1h_closed[:1]+(bad,)+q.derived_1h_closed[2:]))
    def test_changed_4h_source_provenance_rejected(self):
        q=synth()
        bad=replace(q.derived_4h_closed[1],source_native_15m_zip_shas=("b"*64,))
        with self.assertRaisesRegex(C18Rejected,"DERIVED_4H_SOURCE_GEOMETRY_MISMATCH"):
            run(replace(q,derived_4h_closed=q.derived_4h_closed[:1]+(bad,)+q.derived_4h_closed[2:]))
    def test_forged_author_ready_rejected(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"FORGED_C16_AUTHOR_STATUS"):
            run(replace(q,readiness="READY"))
    def test_forged_author_approval_rejected(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"FORGED_C16_AUTHOR_STATUS"):
            run(replace(q,author_status="APPROVED"))
    def test_false_native_daily_parity_count_rejected(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"FALSE_C16_NATIVE_DAILY_MATCH_COUNT"):
            run(replace(q,crosschecked_native_1d=1))
    def test_partial_incomplete_hour_prefix_is_rejected(self):
        q=synth()
        with self.assertRaisesRegex(C18Rejected,"DERIVED_1H_SOURCE_GEOMETRY_MISMATCH"):
            run(replace(q,derived_1h_closed=q.derived_1h_closed[:-1]))
    def test_no_trade_fields_in_graph_or_children(self):
        g=run()
        self.assertFalse(hasattr(g,"trades"))
        self.assertFalse(hasattr(g.children_15m[0],"entry"))
    def test_full_history_cannot_be_claimed_as_original_five_minute(self):
        g=run()
        self.assertIn("15M_NATIVE",g.source_scope)
        self.assertNotIn("5M",g.source_scope)
if __name__=="__main__": unittest.main()
