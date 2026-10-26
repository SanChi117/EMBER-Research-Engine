"""C79 original academic course next proof: no source geometry can trade."""
import unittest
from dataclasses import replace
from c79_course_next_evidence_map import hypothetical_next_step as route,C79Rejected

def case(**update):
    x=dict(parent_tf="1H",parent_poi="RB",parent_raid=False,
           trigger_1h="NONE",first_1h_poi_test="NOT_TESTED",
           trigger_15m="NONE",vc_kind="NONE",from_4h_reaction=True)
    x.update(update)
    return x

def scan(**kw):return route(**case(**kw))

class C79Course(unittest.TestCase):
    def test_01_new_1h_requires_first_valid_test(self):
        x=scan()
        self.assertEqual(x.next_evidence,"REQUIRE_AUTHOR_VALID_FIRST_1H_POI_TEST")
    def test_02_physical_wick_not_valid_first_test(self):
        self.assertEqual(scan(first_1h_poi_test="SOURCE_TOUCH_ONLY").next_evidence,
                         "REQUIRE_AUTHOR_VALID_FIRST_1H_POI_TEST")
    def test_03_hypothetical_valid_1h_no_trigger_direct_15m(self):
        x=scan(first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID")
        self.assertEqual(x.next_evidence,"REQUIRE_DIRECT_15M_VC_IMB_OR_SNR")
    def test_04_hypothetical_valid_1h_bsl_trigger_needs_5m(self):
        x=scan(first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID",trigger_15m="BSL_RAID")
        self.assertEqual(x.next_evidence,"REQUIRE_5M_VC_IMB_OR_SNR")
    def test_05_hypothetical_valid_1h_ssl_trigger_needs_5m(self):
        x=scan(first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID",trigger_15m="SSL_RAID")
        self.assertEqual(x.next_evidence,"REQUIRE_5M_VC_IMB_OR_SNR")
    def test_06_4h_poi_1h_trigger_needs_15m_vc(self):
        x=scan(parent_tf="4H",parent_poi="SNR",trigger_1h="BSL_RAID",from_4h_reaction=False,first_4h_poi_test="HYPOTHETICAL_AUTHOR_VALID")
        self.assertEqual(x.next_evidence,"REQUIRE_15M_VC_IMB_OR_SNR")
    def test_07_4h_raid_no_1h_trigger_wait_1h_vc(self):
        x=scan(parent_tf="4H",parent_poi="LIQUIDITY",parent_raid=True,
               from_4h_reaction=False)
        self.assertEqual(x.next_evidence,"REQUIRE_1H_VC_RB_SNR_IMB_NEW_POI")
    def test_08_4h_poi_no_1h_trigger_wait_1h_vc(self):
        x=scan(parent_tf="4H",parent_poi="RB",from_4h_reaction=False,first_4h_poi_test="HYPOTHETICAL_AUTHOR_VALID")
        self.assertEqual(x.next_evidence,"REQUIRE_1H_VC_RB_SNR_IMB_NEW_POI")
    def test_09_all_hypothetical_decisions_not_trade_ready(self):
        for p in [
          case(),
          case(first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID"),
          case(first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID",trigger_15m="BSL_RAID"),
          case(parent_tf="4H",from_4h_reaction=False,trigger_1h="SSL_RAID",first_4h_poi_test="HYPOTHETICAL_AUTHOR_VALID")
        ]:
            r=route(**p)
            self.assertFalse(r.author_authenticated)
            self.assertFalse(r.entry_allowed)
            self.assertEqual((r.orders,r.fills,r.trades),((),(),()))
            self.assertEqual(r.readiness,"NOT_TRADE_READY")
    def test_10_8_combinations_no_entry(self):
        for poi in ("RB","SNR","IMB"):
            for trigger in ("NONE","SSL_RAID","BSL_RAID"):
                r=scan(parent_poi=poi,first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID",trigger_15m=trigger)
                self.assertFalse(r.entry_allowed)
    def test_11_source_candidate_kind_not_vc_proof(self):
        x=scan(first_1h_poi_test="SOURCE_TOUCH_ONLY",vc_kind="IMB")
        self.assertEqual(x.next_evidence,"REQUIRE_AUTHOR_VALID_FIRST_1H_POI_TEST")
    def test_12_4h_wick_touch_not_author_valid_test(self):
        x=scan(parent_tf="4H",from_4h_reaction=False,first_4h_poi_test="SOURCE_TOUCH_ONLY",trigger_1h="SSL_RAID")
        self.assertEqual(x.next_evidence,"REQUIRE_AUTHOR_VALID_FIRST_4H_POI_TEST")
    def test_13_nested_15m_imb_requires_separate_author_review(self):
        x=scan(parent_poi="IMB",first_1h_poi_test="HYPOTHETICAL_AUTHOR_VALID",trigger_15m="ELIGIBLE_IMB")
        self.assertEqual(x.next_evidence,"REQUIRE_AUTHOR_REVIEW_OF_NESTED_15M_IMB_ELIGIBILITY")
        self.assertFalse(x.entry_allowed)
    def test_14_immutable_public_response(self):
        from dataclasses import FrozenInstanceError
        o=scan()
        with self.assertRaises(FrozenInstanceError):o.entry_allowed=True

def fails(**override):
    def impl(self):
        with self.assertRaises(C79Rejected):scan(**override)
    return impl

NEG={
"bad_tf":dict(parent_tf="3M"),
"bad_poi":dict(parent_poi="PIVOT"),
"string_raid":dict(parent_raid="TRUE"),
"fake_trigger":dict(trigger_15m="BOS"),
"fake_1h_trigger":dict(trigger_1h="IDM"),
"bad_vc":dict(vc_kind="OB"),
"unknown_touch":dict(first_1h_poi_test="AUTHOR_APPROVED"),
"4h_raid_1h_trigger":dict(parent_tf="4H",parent_raid=True,from_4h_reaction=False,trigger_1h="SSL_RAID"),
"4h_nested_imb":dict(parent_tf="4H",parent_poi="IMB",trigger_1h="ELIGIBLE_IMB",from_4h_reaction=False,first_4h_poi_test="HYPOTHETICAL_AUTHOR_VALID"),
"4h_with_15m_trigger":dict(parent_tf="4H",from_4h_reaction=False,trigger_15m="BSL_RAID"),
"4h_with_1h_test":dict(parent_tf="4H",from_4h_reaction=False,first_1h_poi_test="SOURCE_TOUCH_ONLY"),
"1h_raid":dict(parent_tf="1H",parent_raid=True),
"1h_has_1h_trigger":dict(parent_tf="1H",trigger_1h="BSL_RAID"),
"1h_no4h_context":dict(parent_tf="1H",from_4h_reaction=False),
"1h_liquidity_not_new_poi":dict(parent_tf="1H",parent_poi="LIQUIDITY"),
"not_bool_reaction":dict(from_4h_reaction=1),
"fake_4h_validation":dict(first_4h_poi_test="AUTHOR_VERIFIED"),
"not_bool_raid":dict(parent_raid=0)
}
for key,change in NEG.items():setattr(C79Course,"test_negative_"+key,fails(**change))
if __name__=="__main__": unittest.main()
