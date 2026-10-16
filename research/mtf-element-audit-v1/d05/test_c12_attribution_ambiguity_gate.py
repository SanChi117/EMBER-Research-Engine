"""B1/C12: adversarial graph attribution, not academic VC adjudication."""
from __future__ import annotations

from dataclasses import FrozenInstanceError,replace
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"mtf-course-v05"/"src"))

from test_c11_contact_imb_source_witness import scan,proof,T,DAY,PERIOD
from c11_contact_imb_source_witness import ContactImbReview
from c12_attribution_ambiguity_gate import (
    audit_ambiguous_edges,inspect_ambiguity_from_original_source,AttributionRejected
)

def base():
    return scan()

def with_edges(*edges,parents=1):
    z=base()
    return replace(z,paired_source_price_witnesses=tuple(edges),
                   post_raid_5m_imb_candidates=len(edges),
                   raid_contact_candidates=parents)

class C12AttributionTests(unittest.TestCase):
    def test_source_context_remains_not_ready(self):
        a,b=proof()
        q=inspect_ambiguity_from_original_source(a,b,T+DAY+28*PERIOD)
        self.assertGreater(q.total_raid_imb_edges,0)
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
        self.assertEqual(q.author_vc_approvals,0)
        self.assertEqual(q.author_stronghl_approvals,0)

    def test_one_geometric_candidate_not_author_certified(self):
        q=audit_ambiguous_edges(base())
        self.assertEqual(q.raid_nodes_with_edges,1)
        self.assertEqual(q.unique_imb_nodes_with_edges,1)
        self.assertEqual(q.raids_with_multiple_imbs,0)
        self.assertEqual(q.imbs_with_multiple_raids,0)
        self.assertEqual({x.classification for x in q.nodes},
                         {"SINGLE_GEOMETRIC_MATCH_STILL_UNCERTIFIED"})

    def test_one_raid_two_imbs_is_ambiguous_not_first_wins(self):
        w=base().paired_source_price_witnesses[0]
        second=replace(w,confirmation_5m_imb_uid=w.confirmation_5m_imb_uid+":later",
                       confirmation_known_ms=w.confirmation_known_ms+PERIOD,
                       confirmation_source_5m_id=w.confirmation_source_5m_id.split(":")[0]+":"+
                       str(int(w.confirmation_source_5m_id.split(":")[1])+PERIOD),
                       first_later_poi_test_known_ms=None,
                       first_later_poi_test_source_id=None)
        q=audit_ambiguous_edges(with_edges(w,second))
        self.assertEqual(q.total_raid_imb_edges,2)
        self.assertEqual(q.raids_with_multiple_imbs,1)
        self.assertEqual(q.unique_imb_nodes_with_edges,2)
        self.assertEqual(q.nodes[0].classification,"MULTIPLE_GEOMETRIC_IMBS_NO_AUTHOR_CHOICE")
        self.assertEqual(q.readiness,"NOT_TRADE_READY")

    def test_one_imb_many_raid_parents_unresolved(self):
        w=base().paired_source_price_witnesses[0]
        other=replace(w,contact_1h_raid_uid=w.contact_1h_raid_uid+":other")
        q=audit_ambiguous_edges(with_edges(w,other,parents=2))
        self.assertEqual(q.unique_imb_nodes_with_edges,1)
        self.assertEqual(q.imbs_with_multiple_raids,1)
        self.assertEqual([n.classification for n in q.nodes if n.node_type=="5M_CLASSIC_IMB"],
                         ["MULTIPLE_PARENT_RAIDS_NO_AUTHOR_CHOICE"])

    def test_same_witness_twice_not_double_counted(self):
        w=base().paired_source_price_witnesses[0]
        with self.assertRaisesRegex(AttributionRejected,"DUPLICATE_CAUSAL_EDGE"):
            audit_ambiguous_edges(with_edges(w,w,parents=2))

    def test_fake_imb_same_id_other_raw_bar_rejected(self):
        w=base().paired_source_price_witnesses[0]
        other=replace(w,contact_1h_raid_uid=w.contact_1h_raid_uid+":other",
                      poi_high=w.poi_high+0.5)
        with self.assertRaisesRegex(AttributionRejected,"FORGED_DUPLICATED_IMB_GEOMETRY"):
            audit_ambiguous_edges(with_edges(w,other,parents=2))

    def test_bad_declared_review_edge_count_rejected(self):
        z=base()
        with self.assertRaisesRegex(AttributionRejected,"C11_EDGE_COUNT_INCONSISTENT"):
            audit_ambiguous_edges(replace(z,post_raid_5m_imb_candidates=99))

    def test_fake_source_symbol_rejected(self):
        z=base()
        w=replace(z.paired_source_price_witnesses[0],source_symbol="ETHUSDT")
        with self.assertRaisesRegex(AttributionRejected,"CROSS_SYMBOL_OR_FAKE_STRONGHL"):
            audit_ambiguous_edges(with_edges(w))

    def test_tainted_author_status_rejected(self):
        z=base()
        w=replace(z.paired_source_price_witnesses[0],academic_status="APPROVED")
        with self.assertRaisesRegex(AttributionRejected,"CROSS_SYMBOL_OR_FAKE_STRONGHL"):
            audit_ambiguous_edges(with_edges(w))

    def test_not_ready_incoming_review_required(self):
        z=base()
        with self.assertRaisesRegex(AttributionRejected,"UNTRUSTED_OR_READY_CONTACT_REVIEW"):
            audit_ambiguous_edges(replace(z,readiness="READY"))

    def test_missing_raid_source_uid_rejected(self):
        w=replace(base().paired_source_price_witnesses[0],contact_source_5m_id="invented")
        with self.assertRaisesRegex(AttributionRejected,"UNBOUND_OR_BAD_RAW_SOURCE_REFERENCE"):
            audit_ambiguous_edges(with_edges(w))

    def test_missing_confirm_imb_uid_rejected(self):
        w=replace(base().paired_source_price_witnesses[0],confirmation_5m_imb_uid="")
        with self.assertRaisesRegex(AttributionRejected,"INVALID_CONTACT_TO_IMB_CAUSAL_TIME"):
            audit_ambiguous_edges(with_edges(w))

    def test_impossibly_early_confirmation_rejected(self):
        w=base().paired_source_price_witnesses[0]
        w=replace(w,confirmation_known_ms=w.contact_known_ms)
        with self.assertRaisesRegex(AttributionRejected,"INVALID_CONTACT_TO_IMB_CAUSAL_TIME"):
            audit_ambiguous_edges(with_edges(w))

    def test_future_confirmation_cannot_influence_prefix(self):
        z=base()
        w=replace(z.paired_source_price_witnesses[0],
                  confirmation_known_ms=z.as_of_ms+PERIOD)
        with self.assertRaisesRegex(AttributionRejected,"INVALID_CONTACT_TO_IMB_CAUSAL_TIME"):
            audit_ambiguous_edges(with_edges(w))

    def test_wrong_original_imb_end_timestamp_rejected(self):
        w=base().paired_source_price_witnesses[0]
        w=replace(w,confirmation_source_5m_id=w.confirmation_source_5m_id[:-1]+"9")
        with self.assertRaisesRegex(AttributionRejected,"RAW_SOURCE_CLOSE_MISMATCH"):
            audit_ambiguous_edges(with_edges(w))

    def test_wrong_original_liquidity_wick_timestamp_rejected(self):
        w=base().paired_source_price_witnesses[0]
        w=replace(w,contact_source_5m_id=w.contact_source_5m_id.split(":")[0]+":1")
        with self.assertRaisesRegex(AttributionRejected,"RAW_SOURCE_CLOSE_MISMATCH"):
            audit_ambiguous_edges(with_edges(w))

    def test_fake_retrospective_poi_touch_not_first(self):
        w=base().paired_source_price_witnesses[0]
        w=replace(w,first_later_poi_test_known_ms=w.confirmation_known_ms)
        with self.assertRaisesRegex(AttributionRejected,"RETROSPECTIVE_OR_FUTURE_FIRST_TEST"):
            audit_ambiguous_edges(with_edges(w))

    def test_touch_source_missing_but_timestamp_given(self):
        w=base().paired_source_price_witnesses[0]
        w=replace(w,first_later_poi_test_source_id=None)
        with self.assertRaisesRegex(AttributionRejected,"UNPAIRED_FIRST_ZONE_TOUCH"):
            audit_ambiguous_edges(with_edges(w))

    def test_touch_after_asof_rejected(self):
        z=base()
        w=z.paired_source_price_witnesses[0]
        w=replace(w,first_later_poi_test_known_ms=z.as_of_ms+PERIOD)
        with self.assertRaisesRegex(AttributionRejected,"RETROSPECTIVE_OR_FUTURE_FIRST_TEST"):
            audit_ambiguous_edges(with_edges(w))

    def test_missing_parent_event_count_rejected(self):
        z=base()
        with self.assertRaisesRegex(AttributionRejected,"MORE_PARENT_RAIDS_THAN_SOURCE_OBSERVATIONS"):
            audit_ambiguous_edges(replace(z,raid_contact_candidates=0))

    def test_one_empty_review_does_not_create_forced_signal(self):
        z=base()
        q=audit_ambiguous_edges(replace(z,paired_source_price_witnesses=(),
                                        post_raid_5m_imb_candidates=0))
        self.assertEqual(q.total_raid_imb_edges,0)
        self.assertEqual(q.nodes,())
        self.assertEqual(q.author_vc_approvals,0)

    def test_order_invariance_of_unambiguous_output(self):
        z=base()
        w=z.paired_source_price_witnesses[0]
        second=replace(w,contact_1h_raid_uid=w.contact_1h_raid_uid+":alternate")
        x=audit_ambiguous_edges(with_edges(w,second,parents=2))
        y=audit_ambiguous_edges(with_edges(second,w,parents=2))
        self.assertEqual(x.nodes,y.nodes)

    def test_original_source_lookahead_rejected(self):
        a,b=proof()
        with self.assertRaisesRegex(AttributionRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_ambiguity_from_original_source(a,b,T+2*DAY+PERIOD)

    def test_history_prefix_at_contact_start_no_imb(self):
        a,b=proof()
        q=inspect_ambiguity_from_original_source(a,b,T+DAY+2*3600000)
        self.assertEqual(q.total_raid_imb_edges,0)
        self.assertEqual(q.author_stronghl_approvals,0)

    def test_immutable_graph_never_becomes_ready(self):
        q=audit_ambiguous_edges(base())
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            q.nodes[0].author_attribution="APPROVED"

if __name__=="__main__":
    unittest.main(verbosity=2)
