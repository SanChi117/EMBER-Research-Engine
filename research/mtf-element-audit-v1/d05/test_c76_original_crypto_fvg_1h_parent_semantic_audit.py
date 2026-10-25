"""C76 negative and positive cases. These fixtures are synthetic only."""
from dataclasses import replace
from decimal import Decimal as D
import unittest
from c75_external_imb_first_visit_lifecycle import AdaptedFVG
from c76_original_crypto_fvg_1h_parent_semantic_audit import (
    C76Rejected, classify_original_parent_fvg, summarize_c76_original_contexts)

def parent(kind="1H_NEW_VC_RB_SOURCE", episodes=1):
    d = {
        "symbol":"BTCUSDT", "side":"LONG", "readiness":"NOT_TRADE_READY",
        "state": ("NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"
                  if episodes > 1 else "NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID"),
        "source_1h_poi_kind": kind, "source_1h_poi_created_at_ms": 3600000,
        "source_1h_poi_bottom": "100", "source_1h_poi_top": "110",
        "original_first_source3m_touch_closed_ms": 5400000,
        "first_source15m_event_fully_known_ms": 7200000,
        "episodes_before_first_15m_pattern": episodes,
        "orders":[], "fills":[], "trades":[]
    }
    for k in ("author_15m_trigger","author_15m_vc","author_1h_poi_valid_first_test",
              "author_5m_vc","author_entry","author_stronghl","author_structural_sl",
              "route_b_idm_used","route_c_raid_bos_used"):
        d[k] = False
    return d

def fvg(known=4500000,lower="102",upper="105",symbol="BTCUSDT",
        side="LONG"):
    return AdaptedFVG(symbol,"15m",side,D(lower),D(upper),
                      "a"*64+":2700000","b"*64+":3600000",
                      known,"b"*64)

class TestC76SemanticAudit(unittest.TestCase):
    def test_01_contained_rb_is_only_observation(self):
        x=classify_original_parent_fvg(parent(),(fvg(),))
        self.assertEqual(x.parent_embedded_15m_fvg,
            "CONTAINED_FVG_IN_RB_OR_SNR_PARENT_UNVERIFIED")
        self.assertFalse(x.author_15m_trigger)

    def test_02_nested_imb_is_excluded(self):
        x=classify_original_parent_fvg(parent("1H_NEW_VC_IMB_SOURCE"),(fvg(),))
        self.assertEqual(x.parent_embedded_15m_fvg,
            "NESTED_IN_PARENT_IMB_INELIGIBLE_TO_ASSUME_TRIGGER")

    def test_03_snr_source_kind(self):
        x=classify_original_parent_fvg(parent("1H_NEW_VC_SNR_SOURCE"),(fvg(),))
        self.assertEqual(x.parent_kind,"SNR_SOURCE_ONLY")

    def test_04_later_fvg_cannot_retroactively_be_pretest(self):
        x=classify_original_parent_fvg(parent(),(fvg(known=6300000),))
        self.assertEqual(x.eligible_nested_count,0)
        self.assertEqual(x.parent_embedded_15m_fvg,"NO_PRETOUCH_SAME_SIDE_PARENT_FVG")

    def test_05_partial_zone_overlap_is_not_entry(self):
        x=classify_original_parent_fvg(parent(),(fvg(lower="99",upper="104"),))
        self.assertEqual(x.eligible_overlap_count,1)
        self.assertEqual(x.parent_embedded_15m_fvg,"PARTIAL_PARENT_OVERLAP_NO_AUTOMATIC_ENTRY")

    def test_06_source_event_fvg_separate_clock(self):
        x=classify_original_parent_fvg(parent(),(fvg(known=7200000),))
        self.assertTrue(x.source_first_15m_fvg_at_event)
        self.assertEqual(x.eligible_nested_count,0)
        self.assertFalse(x.author_15m_vc)

    def test_07_repeat_visit_not_validated(self):
        x=classify_original_parent_fvg(parent(episodes=2),(fvg(),))
        self.assertEqual(x.parent_first_touch,"SOURCE_REPEAT_VISIT")
        self.assertFalse(x.author_first_valid_poi_test)

    def test_08_no_external_match(self):
        x=classify_original_parent_fvg(parent(),())
        self.assertEqual(x.parent_embedded_15m_fvg,"NO_PRETOUCH_SAME_SIDE_PARENT_FVG")

    def test_09_parent_not_known_before_fvg(self):
        x=classify_original_parent_fvg(parent(),(fvg(known=3500000),))
        self.assertEqual(x.eligible_nested_count,0)

    def test_10_no_opposite_side_promotion(self):
        x=classify_original_parent_fvg(parent(),(fvg(side="SHORT"),))
        self.assertEqual(x.eligible_nested_count,0)

    def test_11_explicit_no_first_touch(self):
        p=parent()
        p["state"]="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH"
        p["original_first_source3m_touch_closed_ms"]=None
        x=classify_original_parent_fvg(p,(fvg(),))
        self.assertEqual(x.parent_first_touch,"NO_FIRST_TEST")

    def test_12_full_source_summary_no_trades(self):
        d=summarize_c76_original_contexts([parent(),parent(episodes=2)],(fvg(),))
        self.assertEqual(d["original_c73_contexts"],2)
        self.assertEqual((d["orders"],d["fills"],d["trades"]),(0,0,0))

def mutate(**changes):
    def runner(self):
        p=parent()
        p.update(changes)
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(p,(fvg(),))
    return runner

CASES={
"bad_symbol":dict(symbol="FAKEUSDT"),
"bad_side":dict(side="BOTH"),
"cross_route_idm":dict(route_b_idm_used=True),
"cross_route_raid_bos":dict(route_c_raid_bos_used=True),
"forged_15m_trigger":dict(author_15m_trigger=True),
"forged_15m_vc":dict(author_15m_vc=True),
"forged_5m_vc":dict(author_5m_vc=True),
"forged_stronghl":dict(author_stronghl=True),
"forged_entry":dict(author_entry=True),
"forged_orders":dict(orders=["BUY"]),
"unknown_kind":dict(source_1h_poi_kind="CUSTOM_SIGNAL"),
"no_poi_time":dict(source_1h_poi_created_at_ms=None),
"future_poi":dict(source_1h_poi_created_at_ms=6000000),
"bad_lower":dict(source_1h_poi_bottom="NaN"),
"bad_upper":dict(source_1h_poi_top="Infinity"),
"negative_zone":dict(source_1h_poi_bottom="-3"),
"inverted_zone":dict(source_1h_poi_top="90"),
"false_event_order":dict(first_source15m_event_fully_known_ms=3500000),
"future_touch_bool":dict(original_first_source3m_touch_closed_ms=True),
"zero_creation":dict(source_1h_poi_created_at_ms=0),
"fake_visit_count":dict(episodes_before_first_15m_pattern=3),
"faked_readiness":dict(readiness="READY"),
}
for label, change in CASES.items():
    setattr(TestC76SemanticAudit,"test_negative_"+label,mutate(**change))

class TestC76CandidateTamper(unittest.TestCase):
    def test_other_symbol_fvg_rejected(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(parent(),(fvg(symbol="ETHUSDT"),))

    def test_promoted_author_fvg_rejected(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(parent(),(replace(fvg(),author_15m_trigger=True),))

    def test_wrong_tf_fvg_rejected(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(parent(),(replace(fvg(),tf="5m"),))

    def test_untrusted_dict_fvg_rejected(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(parent(),({"fvg":"source"},))

    def test_wrong_fvg_iterable_rejected(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg(parent(),[fvg()])

    def test_fake_parent_context_structure(self):
        with self.assertRaises(C76Rejected):
            classify_original_parent_fvg({"author_entry":True},())

if __name__=="__main__":
    unittest.main()
