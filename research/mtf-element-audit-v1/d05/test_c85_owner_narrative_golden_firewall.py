"""C85 real original 153 crypto cases and owner narrative anti-promotion tests."""
from dataclasses import replace
from pathlib import Path
import json, unittest
from c83_owner_course_text_crosswalk import source_matched_queue,C83Rejected
from c85_owner_narrative_golden_firewall import (
 C85Rejected,Claim,ROUTES,TEXT_EXAMPLES,COURSE_RULES,REQUIRED,
 reject_untrusted_claim,independent_source_report,summary,witness,serialize_witness
)
ROOT=Path(__file__).resolve().parents[1]
C73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
C72=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
C81=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
Q=source_matched_queue(C73,C72,C81)
BASE=Claim(Q[0].source_key,"A1H_TRIGGER_5M_VC")
class TestActualCryptoAndCourse(unittest.TestCase):
    def test_01_original153(self):
        self.assertEqual(len(independent_source_report(C73,C72,C81)),153)
    def test_02_priority_counts(self):
        self.assertEqual(summary(independent_source_report(C73,C72,C81))["priority"],
            {"0":12,"1":23,"2":71,"3":47})
    def test_03_real_entry_proofs_zero(self):
        r=summary(independent_source_report(C73,C72,C81))
        self.assertEqual((r["owner_authenticated_positive"],r["owner_authenticated_negative"],r["trades"]),(0,0,0))
    def test_04_4_example_schematic_not_crypto(self):
        r=witness(C73,C72,C81)
        self.assertEqual(len(r["owner_text_examples"]),4)
        self.assertTrue(all(x["label"]=="OWNER_TEXT_SCHEMATIC" for x in r["owner_text_examples"]))
    def test_05_all_rule_anchor_ids_unique(self):
        self.assertEqual(len({a for a,b,c in COURSE_RULES}),len(COURSE_RULES))
        self.assertGreaterEqual(len(COURSE_RULES),14)
    def test_06_narrative_4h_trigger_ltf15m(self):
        self.assertEqual(ROUTES["A4H_TRIGGER_15M_VC"][-1],"15M_VC_SNR_IMB")
    def test_07_15m_trigger_then5m(self):
        self.assertIn("15M_TRIGGER_BSL",ROUTES["A1H_TRIGGER_5M_VC"])
        self.assertIn("5M_VC_IMB_SNR",ROUTES["A1H_TRIGGER_5M_VC"])
    def test_08_without_trigger_direct15m(self):
        self.assertEqual(ROUTES["A1H_NO_TRIGGER_DIRECT_15M_VC"][-1],"15M_DIRECT_VC_IMB")
    def test_09_no_price_image_binding(self):
        r=independent_source_report(C73,C72,C81)
        self.assertTrue(all(x["course_text_example_match"]=="NOT_PROVEN" for x in r))
    def test_10_serialization_deterministic(self):
        self.assertEqual(serialize_witness(C73,C72,C81),serialize_witness(C73,C72,C81))
    def test_11_mutated_c73(self):
        with self.assertRaises(C83Rejected):independent_source_report(C73+b"x",C72,C81)
    def test_12_mutated_c72(self):
        with self.assertRaises(C83Rejected):independent_source_report(C73,C72+b"x",C81)
    def test_13_mutated_c81(self):
        with self.assertRaises(C83Rejected):independent_source_report(C73,C72,C81+b"x")
    def test_14_forged_c81_owner(self):
        x=json.loads(C81);x[0]["author_verified"]=True
        with self.assertRaises(C83Rejected):
            independent_source_report(C73,C72,json.dumps(x).encode())
    def test_15_future5m_source(self):
        x=json.loads(C81);x[0]["first5m_known_ms"]=x[0]["source15m_known_ms"]-1
        with self.assertRaises(C83Rejected):
            independent_source_report(C73,C72,json.dumps(x).encode())
    def test_16_negative_case_fake(self):
        r=independent_source_report(C73,C72,C81);r[0]["author_negative_case"]=True
        with self.assertRaises(C85Rejected):summary(r)
    def test_17_positive_case_fake(self):
        r=independent_source_report(C73,C72,C81);r[0]["author_positive_case"]=True
        with self.assertRaises(C85Rejected):summary(r)
    def test_18_course_match_fake(self):
        r=independent_source_report(C73,C72,C81);r[0]["course_text_example_match"]="MATCH"
        with self.assertRaises(C85Rejected):summary(r)
    def test_19_missing_proof_flags_on_every_source_case(self):
        r=independent_source_report(C73,C72,C81)
        self.assertTrue(all(len(x["missing_proofs"])==len(REQUIRED) for x in r))
    def test_20_chronology_claim_does_not_prove_author(self):
        r=independent_source_report(C73,C72,C81)
        self.assertEqual(sum(x["author_positive_case"] for x in r if x["priority"]==0),0)

class TestUntrustedClaims(unittest.TestCase):
    def test_21_text_example_never_author_golden(self):
        x=reject_untrusted_claim(BASE,Q)
        self.assertEqual(x["submission_status"],"UNVERIFIED_OWNER_MEDIA_QUARANTINE")
        self.assertFalse(x["positive_golden"])
    def test_22_valid_sha_alone_not_author_proof(self):
        x=reject_untrusted_claim(replace(BASE,course_media_digest="a"*64,
          attestation="owner",reviewer="independent",provider_media_id="image-1",
          positive_label=True),Q)
        self.assertFalse(x["author_verified"] or x["positive_golden"])
    def test_23_negative_label_claim_quarantined(self):
        x=reject_untrusted_claim(replace(BASE,negative_label=True),Q)
        self.assertFalse(x["negative_golden"])
    def test_24_route_b_rejected(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,route="B"),Q)
    def test_25_route_c_rejected(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,route="C"),Q)
    def test_26_fake_author_verified_flag(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,claimed_author_verified=True),Q)
    def test_27_fake_author_class(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,claim_class="AUTHOR_VERIFIED"),Q)
    def test_28_invalid_golden_case(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,case_key="DOGEUSDT/0"),Q)
    def test_29_wrong_symbol_vs_source(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,native_symbol="BTCUSDT" if Q[0].symbol!="BTCUSDT" else "XRPUSDT"),Q)
    def test_30_unknown_course_id(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,author_example_id="FORGED"),Q)
    def test_31_fake_hash_format(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,course_media_digest="not a sha"),Q)
    def test_32_conflicting_positive_negative_labels(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,positive_label=True,negative_label=True),Q)
    def test_33_unknown_timeframe(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,native_tf="2m"),Q)
    def test_34_timestamp_without_native_tf(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,native_closed_ms=1790000000000),Q)
    def test_35_negative_timestamp(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,native_tf="15m",native_closed_ms=-10),Q)
    def test_36_fake_media_too_long(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,provider_media_id="a"*241),Q)
    def test_37_source_case_tampered_queue_length(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(BASE,Q[:1])
    def test_38_type_error(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(dict(case_key=Q[0].source_key),Q)
    def test_39_owner_narrative_still_not_crypto_with_claimed_time(self):
        x=reject_untrusted_claim(replace(BASE,native_tf="15m",
                 native_closed_ms=Q[0].source15m_known_ms,
                 native_symbol=Q[0].symbol,positive_label=True),Q)
        self.assertFalse(x["author_verified"])
    def test_40_alternative_narrative_no_trigger(self):
        x=reject_untrusted_claim(replace(BASE,
           author_example_id="A1H_NO_TRIGGER_DIRECT_15M_VC"),Q)
        self.assertFalse(x["entry_allowed"])
    def test_41_invalid_claim_class(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,claim_class="GOLDEN"),Q)
    def test_42_attestation_too_long(self):
        with self.assertRaises(C85Rejected):
            reject_untrusted_claim(replace(BASE,attestation="x"*300),Q)
    def test_43_media_label_after_quote_still_not_time_ticker(self):
        x=reject_untrusted_claim(replace(BASE,claim_class="OWNER_TEXT_RULE",
         course_media_digest="f"*64,native_symbol=Q[0].symbol),Q)
        self.assertEqual(x["course_kind"],"OWNER_TEXT_SCHEMATIC_NOT_CRYPTO_GOLDEN")

if __name__=="__main__":unittest.main()
