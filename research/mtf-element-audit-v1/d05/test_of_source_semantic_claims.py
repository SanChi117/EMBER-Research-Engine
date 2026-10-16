"""D05/F02 source OF topology counterexamples; labels ARE NOT price proof."""
from dataclasses import FrozenInstanceError,replace
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from of_source_semantic_claims import OFClaim,OFSourceRejected,inspect_of_source_claims
T=1790899200000
def e(kind,when,tf="4h",side="LONG",id=None):
    return OFClaim(kind,side,tf,when,"BTCUSDT",id or kind+":"+str(when))
def review(x,at=T+40*3600000,side="LONG",tf="4h"):
    return inspect_of_source_claims(side,tf,"BTCUSDT",x,at)
class OrderFlowSourceBoundary(unittest.TestCase):
    def test_structure_only_is_not_of(self):
        v=review([])
        self.assertEqual(v.composition,"OF_COMPONENTS_MISSING_LIQUIDITY_OR_IMBALANCE")
        self.assertEqual(v.readiness,"NOT_TRADE_READY")
    def test_liquidity_alone_is_not_complete_of(self):
        v=review([e("LIQUIDITY_WORK",T+4*3600000)])
        self.assertIn("MISSING",v.composition)
    def test_imbalance_alone_is_not_complete_of(self):
        v=review([e("IMBALANCE",T+4*3600000)])
        self.assertIn("MISSING",v.composition)
    def test_both_required_source_components_present_but_not_trade(self):
        a=review([e("LIQUIDITY_WORK",T+4*3600000),
                  e("IMBALANCE",T+8*3600000)])
        self.assertIn("NOT_AUTHOR_CERTIFIED",a.composition)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_same_tf_strong_hl_support_is_claim_not_certificate(self):
        a=review([e("STRONG_HL_VC",T+8*3600000)])
        self.assertEqual(a.link_volume_evidence,"STRONG_HL_VC_CLAIM_UNVERIFIED")
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_lower_tf_strong_hl_support_allowed(self):
        a=review([e("STRONG_HL_VC",T+5*3600000,tf="1h")])
        self.assertIn("UNVERIFIED",a.link_volume_evidence)
    def test_higher_tf_vc_cannot_certify_lower_of_link(self):
        with self.assertRaisesRegex(OFSourceRejected,"STRONG_HL_VC_ABOVE_SOURCE_OF_TF"):
            review([e("STRONG_HL_VC",T+24*3600000,tf="1d")])
    def test_target_reached_alone_does_not_invalidate_of(self):
        a=review([e("HTF_TARGET",T+8*3600000)])
        self.assertIn("NOT_AUTOMATIC_INVALIDATION",a.target_status)
        self.assertEqual(a.invalidation_status,"NO_INVALIDATION_CLAIM")
    def test_target_then_bos_is_only_unverified_invalidation_candidate(self):
        a=review([e("HTF_TARGET",T+8*3600000),
                  e("STRUCTURE_BOS",T+12*3600000,side="SHORT")])
        self.assertIn("POSSIBLE_INVALIDATION",a.invalidation_status)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_opposing_same_tf_poi_is_invalidation_case_not_ready(self):
        a=review([e("OPPOSITE_POI",T+8*3600000,side="SHORT")])
        self.assertIn("POSSIBLE_INVALIDATION",a.invalidation_status)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_opposing_poi_other_tf_cannot_auto_invalidate(self):
        with self.assertRaisesRegex(OFSourceRejected,"OPPOSITE_POI_MUST_BE_SAME_OF_TF"):
            review([e("OPPOSITE_POI",T+5*3600000,tf="1h",side="SHORT")])
    def test_wrong_invalidation_side_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"WRONG_EVENT_SIDE_FOR_OF_ROLE"):
            review([e("STRUCTURE_BOS",T+8*3600000)])
    def test_missing_side_on_liquidity_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"WRONG_EVENT_SIDE_FOR_OF_ROLE"):
            review([e("LIQUIDITY_WORK",T+8*3600000,side="SHORT")])
    def test_spot_or_wrong_market_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"WRONG_MARKET_OR_SYMBOL"):
            review([replace(e("IMBALANCE",T+8*3600000),market="SPOT")])
    def test_cross_symbol_claim_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"WRONG_MARKET_OR_SYMBOL"):
            review([replace(e("IMBALANCE",T+8*3600000),symbol="ETHUSDT")])
    def test_future_claim_not_seen_at_earlier_asof(self):
        with self.assertRaisesRegex(OFSourceRejected,"UNSORTED_OR_FUTURE_EVENT"):
            review([e("IMBALANCE",T+8*3600000)],at=T+4*3600000)
    def test_out_of_order_claims_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"UNSORTED_OR_FUTURE_EVENT"):
            review([e("IMBALANCE",T+12*3600000),e("LIQUIDITY_WORK",T+8*3600000)])
    def test_unclosed_1h_claim_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"EVENT_KNOWN_BEFORE_OWN_TF_CLOSE"):
            review([e("STRONG_HL_VC",T+5*3600000+1,tf="1h")])
    def test_duplicate_evidence_claim_does_not_double_confirm(self):
        with self.assertRaisesRegex(OFSourceRejected,"DUPLICATE_OR_MISSING_EVIDENCE_SOURCE"):
            review([e("IMBALANCE",T+4*3600000,id="same"),e("LIQUIDITY_WORK",T+8*3600000,id="same")])
    def test_mutation_cannot_promote_to_trade_ready(self):
        a=review([e("IMBALANCE",T+8*3600000)])
        with self.assertRaises(FrozenInstanceError):
            a.readiness="READY"
    def test_no_target_does_not_fabricate_invalidation(self):
        a=review([e("LIQUIDITY_WORK",T+8*3600000),e("IMBALANCE",T+12*3600000)])
        self.assertEqual(a.invalidation_status,"NO_INVALIDATION_CLAIM")
        self.assertEqual(a.target_status,"HTF_TARGET_UNOBSERVED")
    def test_invalid_of_context_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"INVALID_OF_CONTEXT"):
            review([],side="FLAT")
    def test_unknown_evidence_kind_rejected(self):
        with self.assertRaisesRegex(OFSourceRejected,"UNRECOGNIZED_EVENT_KIND_OR_TF"):
            review([e("EMA_SIGNAL",T+8*3600000)])
if __name__=="__main__":
    unittest.main(verbosity=2)
