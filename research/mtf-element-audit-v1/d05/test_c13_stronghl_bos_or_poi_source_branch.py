"""B1/C13 adversarial author POI OR BOS branch test; not academic approval."""
from __future__ import annotations
from dataclasses import FrozenInstanceError,replace
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"mtf-course-v05"/"src"))
from test_c11_contact_imb_source_witness import proof,T,DAY,PERIOD
from c10_two_day_original_5m_context import review_two_day_5m,TwoDayBos
from c12_attribution_ambiguity_gate import inspect_ambiguity_from_original_source
from c13_stronghl_bos_or_poi_source_branch import (
 compare_geometric_confirmation_routes,inspect_both_author_branches,BranchRejected)

NOW=T+DAY+40*PERIOD
def data():
    a,b=proof()
    return a,b,review_two_day_5m(a,b,NOW),inspect_ambiguity_from_original_source(a,b,NOW)
def fake_bos(raid,source,at=NOW):
    open_ms=at-PERIOD
    side=raid.split(":")[2]
    return TwoDayBos(raid,T+DAY+2*3600000,f"5m:BOS:{side}:{open_ms}:{raid}",
                     at,source.zip_sha256,f"{source.zip_sha256}:{open_ms}")
def injected():
    a,b,br,po=data()
    id=next(n.source_uid for n in po.nodes if n.node_type=="LIQUIDITY_RAID")
    ev=fake_bos(id,b)
    return replace(br,source_raid_bos=(ev,)),po,ev
class C13SourceBOSorPOITests(unittest.TestCase):
    def test_synthetic_source_dual_review_is_not_ready(self):
        a,b,_,_=data()
        q=inspect_both_author_branches(a,b,NOW)
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
        self.assertEqual(q.author_stronghl_approvals,0)
        self.assertEqual(q.author_vc_approvals,0)
    def test_explicit_source_bos_parent_can_coexist_with_imb(self):
        br,po,ev=injected()
        q=compare_geometric_confirmation_routes(br,po)
        self.assertEqual(q.raids_with_both_branches,1)
        x=next(x for x in q.parent_bos_links if x.raid_source_uid==ev.raid_id)
        self.assertEqual(x.classification,"BOTH_BOS_AND_IMB_GEOMETRY_NOT_AUTHOR_CERTIFIED")
        self.assertIn(ev.bos_id,x.bos_event_ids)
        self.assertGreater(len(x.imb_event_ids),0)
    def test_bos_only_parent_is_not_promoted_to_stronghl(self):
        br,po,ev=injected()
        id="1h:RAID:SHORT:"+str(T+DAY)+":1h:LOW:"+str(T)
        other=fake_bos(id,proof()[1])
        q=compare_geometric_confirmation_routes(replace(br,source_raid_bos=(other,)),po)
        self.assertTrue(any(x.classification=="BOS_ONLY_GEOMETRY_NOT_AUTHOR_CERTIFIED" for x in q.parent_bos_links))
        self.assertEqual(q.author_stronghl_approvals,0)
    def test_imb_only_path_is_not_promoted(self):
        _,_,br,po=data()
        q=compare_geometric_confirmation_routes(replace(br,source_raid_bos=()),po)
        self.assertEqual(q.raids_with_bos_branch,0)
        self.assertGreater(q.raids_with_imb_branch,0)
        self.assertTrue(all(x.classification=="IMB_ONLY_GEOMETRY_NOT_AUTHOR_CERTIFIED" for x in q.parent_bos_links))
    def test_no_paths_no_trigger_not_ready(self):
        _,_,br,po=data()
        empty=replace(po,nodes=(),total_raid_imb_edges=0,unique_imb_nodes_with_edges=0,
                      raid_nodes_with_edges=0)
        q=compare_geometric_confirmation_routes(replace(br,source_raid_bos=()),empty)
        self.assertEqual(q.raids_with_any_observed_branch,0)
        self.assertEqual(q.unknown_raids_without_either,br.confirmed_1h_raids)
    def test_cross_symbol_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"SOURCE_OR_RAID_COUNTS_DISAGREE"):
            compare_geometric_confirmation_routes(replace(br,symbol="ETHUSDT"),po)
    def test_future_as_of_mismatch_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"SOURCE_OR_RAID_COUNTS_DISAGREE"):
            compare_geometric_confirmation_routes(replace(br,as_of_ms=br.as_of_ms+PERIOD),po)
    def test_distinct_raid_count_mismatch_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"SOURCE_OR_RAID_COUNTS_DISAGREE"):
            compare_geometric_confirmation_routes(replace(br,confirmed_1h_raids=br.confirmed_1h_raids+1),po)
    def test_fake_ready_bos_review_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"FAKE_ALREADY_CERTIFIED_AUTHOR_EVENT"):
            compare_geometric_confirmation_routes(replace(br,readiness="READY"),po)
    def test_fake_ready_imb_review_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"FAKE_ALREADY_CERTIFIED_AUTHOR_EVENT"):
            compare_geometric_confirmation_routes(br,replace(po,author_vc_approvals=1))
    def test_fake_attribution_node_author_certified_rejected(self):
        _,_,br,po=data()
        x=list(po.nodes);x[0]=replace(x[0],author_attribution="CERTIFIED")
        with self.assertRaisesRegex(BranchRejected,"FORGED_AUTHOR_ATTRIBUTION"):
            compare_geometric_confirmation_routes(br,replace(po,nodes=tuple(x)))
    def test_one_raid_duplicate_node_rejected(self):
        _,_,br,po=data()
        x=next(x for x in po.nodes if x.node_type=="LIQUIDITY_RAID")
        with self.assertRaisesRegex(BranchRejected,"DUPLICATE_PARENT_RAID_NODE"):
            compare_geometric_confirmation_routes(br,replace(po,nodes=po.nodes+(x,)))
    def test_one_imb_duplicate_node_rejected(self):
        _,_,br,po=data()
        x=next(x for x in po.nodes if x.node_type=="5M_CLASSIC_IMB")
        with self.assertRaisesRegex(BranchRejected,"DUPLICATE_CHILD_IMB_NODE"):
            compare_geometric_confirmation_routes(br,replace(po,nodes=po.nodes+(x,)))
    def test_forged_bos_wrong_parent_suffix_rejected(self):
        br,po,ev=injected()
        altered=replace(ev,bos_id=ev.bos_id+":WRONG")
        with self.assertRaisesRegex(BranchRejected,"INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF"):
            compare_geometric_confirmation_routes(replace(br,source_raid_bos=(altered,)),po)
    def test_5m_bos_cannot_be_known_before_source_close(self):
        br,po,ev=injected()
        altered=replace(ev,bos_known=ev.bos_known-PERIOD)
        with self.assertRaisesRegex(BranchRejected,"INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF"):
            compare_geometric_confirmation_routes(replace(br,source_raid_bos=(altered,)),po)
    def test_bos_before_raid_rejected(self):
        br,po,ev=injected()
        altered=replace(ev,raid_known=ev.bos_known)
        with self.assertRaisesRegex(BranchRejected,"INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF"):
            compare_geometric_confirmation_routes(replace(br,source_raid_bos=(altered,)),po)
    def test_forged_source_sha_rejected(self):
        br,po,ev=injected()
        altered=replace(ev,original_day_zip_sha256="00"*32)
        with self.assertRaisesRegex(BranchRejected,"INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF"):
            compare_geometric_confirmation_routes(replace(br,source_raid_bos=(altered,)),po)
    def test_duplicate_bos_event_rejected(self):
        br,po,ev=injected()
        with self.assertRaisesRegex(BranchRejected,"INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF"):
            compare_geometric_confirmation_routes(replace(br,source_raid_bos=(ev,ev)),po)
    def test_fake_imb_graph_edge_count_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"RAID_IMB_EDGE_COUNT_MISMATCH"):
            compare_geometric_confirmation_routes(br,replace(po,total_raid_imb_edges=po.total_raid_imb_edges+1))
    def test_new_raid_not_in_supported_count_rejected(self):
        _,_,br,po=data()
        with self.assertRaisesRegex(BranchRejected,"MORE_BRANCH_RAIDS_THAN_CONFIRMED_RAID_EVENTS"):
            compare_geometric_confirmation_routes(replace(br,confirmed_1h_raids=po.total_known_raid_candidates),
                                                   replace(po,total_known_raid_candidates=0)) # count mismatch first
    def test_future_history_rejected_by_unmodified_C10(self):
        a,b=proof()
        with self.assertRaises(Exception):
            inspect_both_author_branches(a,b,T+2*DAY+PERIOD)
    def test_frozen_output_cannot_become_trade(self):
        br,po,ev=injected()
        q=compare_geometric_confirmation_routes(br,po)
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            q.parent_bos_links[0].attribution="AUTHOR_CONFIRMED"

if __name__=="__main__":
    unittest.main(verbosity=2)
