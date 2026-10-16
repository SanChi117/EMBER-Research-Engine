"""F05: adversarial author-source route test suite; no ready trades."""
from dataclasses import FrozenInstanceError,replace
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from f05_source_entry_vc_branches import (
 ClaimedStage,EntryCourseRejected,inspect_source_entry_branch,
 inspect_idm_bypass_claim,RESULTS,STEPS)
T=1790899200000
TIME={"4H_POI_TEST":4*3600000,"4H_LIQUIDITY_RAID":4*3600000,
      "1H_TRIGGER":5*3600000,"1H_VC_NEW_POI":5*3600000,
      "1H_POI_TEST":6*3600000,"15M_TRIGGER":6*3600000+900000,
      "15M_VC_ENTRY":6*3600000+1800000,
      "5M_VC_ENTRY":6*3600000+2100000}
DEFAULT={"4H_POI_TEST":"SNR","4H_LIQUIDITY_RAID":"BSL",
         "1H_TRIGGER":"BSL","1H_VC_NEW_POI":"RB",
         "1H_POI_TEST":"RB","15M_TRIGGER":"BSL",
         "15M_VC_ENTRY":"IMB","5M_VC_ENTRY":"SNR"}
def stage_list(name):
    result=[]
    for i,role in enumerate(RESULTS[name]):
        result.append(ClaimedStage(role,DEFAULT[role],STEPS[role][0],f"e:{i}",
                   "BTCUSDT",T+TIME[role],
                   result[-1].source_id if result else None))
    return result
def check(route,steps=None,at=T+86400000):
    return inspect_source_entry_branch(route,stage_list(route) if steps is None else steps,at)
R_DIRECT="4H_TEST_1H_TRIGGER_15M_VC"
R_FIVE="4H_TEST_1H_VC_POI_TEST_15M_TRIGGER_5M_VC"
R_RAID="4H_RAID_1H_VC_POI_TEST_15M_VC"
class SourceEntryVCBranches(unittest.TestCase):
    def test_all_five_original_course_branch_shapes(self):
        self.assertEqual(len(RESULTS),5)
        for name in RESULTS:
            with self.subTest(route=name):
                review=check(name)
                self.assertEqual(review.required_remaining_roles,())
                self.assertEqual(review.readiness,"NOT_TRADE_READY")
    def test_4h_test_and_1h_trigger_can_finish_at_15m(self):
        a=check(R_DIRECT)
        self.assertEqual(a.entry_vc_tf,"15m")
        self.assertEqual(a.fta_timeframe,"4h")
    def test_4h_raid_cannot_invent_1h_trigger(self):
        b=stage_list(R_DIRECT)
        b[0]=replace(b[0],role="4H_LIQUIDITY_RAID",kind="BSL")
        with self.assertRaisesRegex(EntryCourseRejected,"UNEXPECTED_PARENT_TRIGGER_VC_SEQUENCE"):
            check(R_DIRECT,b)
    def test_no_1h_trigger_requires_new_1h_vc_poi(self):
        a=stage_list(R_FIVE)
        a.pop(1)
        with self.assertRaisesRegex(EntryCourseRejected,"UNEXPECTED_PARENT_TRIGGER_VC_SEQUENCE"):
            check(R_FIVE,a)
    def test_1h_new_poi_must_be_tested_before_15m_trigger(self):
        a=stage_list(R_FIVE)
        a.pop(2)
        with self.assertRaisesRegex(EntryCourseRejected,"UNEXPECTED_PARENT_TRIGGER_VC_SEQUENCE"):
            check(R_FIVE,a)
    def test_no_15m_trigger_allows_15m_vc_entry(self):
        a=check(R_RAID)
        self.assertEqual(a.entry_vc_tf,"15m")
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_15m_trigger_requires_5m_vc_route(self):
        a=stage_list(R_FIVE)
        a[-1]=replace(a[-1],role="15M_VC_ENTRY",kind="IMB",tf="15m")
        with self.assertRaisesRegex(EntryCourseRejected,"UNEXPECTED_PARENT_TRIGGER_VC_SEQUENCE"):
            check(R_FIVE,a)
    def test_source_restricts_entry_vc_to_imb_or_snr(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],kind="RB")
        with self.assertRaisesRegex(EntryCourseRejected,"UNAUTHORIZED_VC_OR_WRONG_TIMEFRAME"):
            check(R_DIRECT,a)
    def test_source_allows_1h_rb_as_vc_but_not_direct_entry_vc(self):
        a=check(R_FIVE)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
        self.assertEqual(a.entry_vc_types,("IMB","SNR"))
    def test_1h_imb_trigger_inside_4h_imb_forbidden(self):
        a=stage_list(R_DIRECT)
        a[0]=replace(a[0],kind="IMB")
        a[1]=replace(a[1],kind="IMB")
        with self.assertRaisesRegex(EntryCourseRejected,"1H_IMB_TRIGGER_INSIDE_4H_IMB_FORBIDDEN"):
            check(R_DIRECT,a)
    def test_1h_imb_trigger_with_snr_support_allowed_unverified(self):
        a=stage_list(R_DIRECT)
        a[1]=replace(a[1],kind="IMB")
        self.assertEqual(check(R_DIRECT,a).readiness,"NOT_TRADE_READY")
    def test_15m_imb_trigger_needs_supporting_1h_rb_or_snr(self):
        a=stage_list(R_FIVE)
        a[1]=replace(a[1],kind="IMB")
        a[2]=replace(a[2],kind="IMB")
        a[3]=replace(a[3],kind="IMB")
        with self.assertRaisesRegex(EntryCourseRejected,"15M_IMB_TRIGGER_REQUIRES_UNPROVED_RB_SNR"):
            check(R_FIVE,a)
    def test_15m_imb_trigger_with_supporting_1h_rb_allowed_not_ready(self):
        a=stage_list(R_FIVE)
        a[3]=replace(a[3],kind="IMB")
        self.assertEqual(check(R_FIVE,a).readiness,"NOT_TRADE_READY")
    def test_4h_raid_15m_imb_trigger_with_1h_snr_support(self):
        name="4H_RAID_1H_VC_POI_TEST_15M_TRIGGER_5M_VC"
        a=stage_list(name)
        a[1]=replace(a[1],kind="SNR")
        a[2]=replace(a[2],kind="SNR")
        a[3]=replace(a[3],kind="IMB")
        self.assertEqual(check(name,a).readiness,"NOT_TRADE_READY")
    def test_created_new_1h_vc_poi_must_match_tested_type(self):
        a=stage_list(R_FIVE)
        a[2]=replace(a[2],kind="SNR")
        with self.assertRaisesRegex(EntryCourseRejected,"TEST_NOT_OF_NEW_1H_POI"):
            check(R_FIVE,a)
    def test_new_1h_poi_cannot_be_tested_at_its_creation_time(self):
        a=stage_list(R_FIVE)
        a[2]=replace(a[2],known_at_ms=a[1].known_at_ms)
        with self.assertRaisesRegex(EntryCourseRejected,"1H_POI_TEST_NOT_AFTER_POI_CREATION"):
            check(R_FIVE,a)
    def test_wrong_parent_uid_rejected(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],parent_source_id="a-fake")
        with self.assertRaisesRegex(EntryCourseRejected,"UNLINKED_PARENT_STAGE"):
            check(R_DIRECT,a)
    def test_cross_symbol_rejected(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],symbol="ETHUSDT")
        with self.assertRaisesRegex(EntryCourseRejected,"CROSS_SYMBOL_CONTEXT"):
            check(R_DIRECT,a)
    def test_spot_rejected(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],market="BINANCE_SPOT")
        with self.assertRaisesRegex(EntryCourseRejected,"INVALID_MARKET"):
            check(R_DIRECT,a)
    def test_future_stage_rejected(self):
        with self.assertRaisesRegex(EntryCourseRejected,"FUTURE_OR_NONMONOTONIC_STAGE"):
            check(R_DIRECT,at=T+4*3600000)
    def test_not_closed_stage_rejected(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],known_at_ms=a[-1].known_at_ms-1)
        with self.assertRaisesRegex(EntryCourseRejected,"UNCLOSED_STAGE_EVIDENCE"):
            check(R_DIRECT,a)
    def test_duplicate_event_source_rejected(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],source_id=a[-2].source_id)
        with self.assertRaisesRegex(EntryCourseRejected,"REPEATED_SOURCE_EVENT"):
            check(R_DIRECT,a)
    def test_caller_cannot_self_approve_source(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],course_verified=True)
        with self.assertRaisesRegex(EntryCourseRejected,"SELF_DECLARED_ACADEMIC_OR_PRICE_ATTESTATION"):
            check(R_DIRECT,a)
    def test_caller_cannot_self_approve_price(self):
        a=stage_list(R_DIRECT)
        a[-1]=replace(a[-1],price_geometry_verified=True)
        with self.assertRaisesRegex(EntryCourseRejected,"SELF_DECLARED_ACADEMIC_OR_PRICE_ATTESTATION"):
            check(R_DIRECT,a)
    def test_partial_route_records_missing_roles(self):
        a=stage_list(R_FIVE)[:2]
        q=check(R_FIVE,a)
        self.assertEqual(q.required_remaining_roles,("1H_POI_TEST","15M_TRIGGER","5M_VC_ENTRY"))
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
    def test_idm_not_force_extra_ltf_vc(self):
        self.assertIn("NO_ORDER",inspect_idm_bypass_claim(
            high_tf_vc_claimed=True,strong_hl_claimed=True,trigger_tf="4h",entry_tf="1h"))
    def test_idm_needs_stronghl_evidence(self):
        self.assertIn("MISSING",inspect_idm_bypass_claim(
            high_tf_vc_claimed=True,strong_hl_claimed=False,trigger_tf="1h",entry_tf="15m"))
    def test_idm_wrong_tf_not_allowed(self):
        with self.assertRaisesRegex(EntryCourseRejected,"UNSUPPORTED_AUTHOR_IDM_HIERARCHY"):
            inspect_idm_bypass_claim(high_tf_vc_claimed=True,strong_hl_claimed=True,trigger_tf="15m",entry_tf="5m")
    def test_readiness_immutable(self):
        q=check(R_DIRECT)
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
if __name__=="__main__":
    unittest.main(verbosity=2)
