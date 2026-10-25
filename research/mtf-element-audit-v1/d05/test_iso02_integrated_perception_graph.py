from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from iso02_integrated_perception_graph import (
    DECISION_STATE, EXPECTED, READINESS, SEMANTIC_GATES, build_integrated_graph,
    canonical, replay_bytes, validate_integrated_graph,
)

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "evidence/c57/C57_ORIGINAL_45ZIP_4H_FIRST_CONTACT_LATER_1H_THEN_FIRST_ANY_NATIVE15M_IMB.json"
B = ROOT / "evidence/c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json"
C = ROOT / "ISO01-registry.json"


class ISO02IntegratedGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if C.exists():
            c_bytes = C.read_bytes()
        else:
            import sys
            sys.path.insert(0, str(ROOT / "tests"))
            from probe_iso01_frozen_c56_parent_state_registry import run as run_iso01
            c_bytes = (json.dumps(run_iso01(), sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        cls.inputs = {"route_a": A.read_bytes(), "route_b": B.read_bytes(), "route_c": c_bytes}
        cls.graph = build_integrated_graph(**cls.inputs)

    def fresh(self):
        return copy.deepcopy(self.graph)

    def reject(self, graph, code):
        with self.assertRaisesRegex(ValueError, code):
            validate_integrated_graph(graph)

    def test_01_three_frozen_sources_have_expected_hash(self):
        for route, data in self.inputs.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED[route]["sha256"])

    def test_02_complete_counts(self):
        self.assertEqual(len(self.graph["objects"]), 2052)
        self.assertEqual(len(self.graph["relationships"]), 1204)
        self.assertEqual(len(self.graph["scenarios"]), 848)

    def test_03_every_parent_has_one_scenario(self):
        parents = [o for o in self.graph["objects"] if o["kind"].endswith("parent")]
        self.assertEqual(len(parents), len(self.graph["scenarios"]))

    def test_04_no_cross_route_relationships(self):
        by_id = {o["object_id"]: o for o in self.graph["objects"]}
        for e in self.graph["relationships"]:
            self.assertEqual(by_id[e["parent_id"]]["route"], by_id[e["child_id"]]["route"])
        self.assertEqual(self.graph["cross_route_relationships"], 0)

    def test_05_read_only_execution_contract(self):
        self.assertEqual(self.graph["readiness"], READINESS)
        self.assertEqual(self.graph["decision_state"], DECISION_STATE)
        self.assertIsNone(self.graph["PnL"])
        for key in ("orders", "fills", "trades"):
            self.assertEqual(self.graph[key], [])

    def test_06_semantic_gates_fail_closed(self):
        self.assertEqual(self.graph["semantic_gates"], list(SEMANTIC_GATES))
        self.assertTrue(all(g["state"] in ("NEEDS_SOURCE", "NOT_STARTED") for g in SEMANTIC_GATES))

    def test_07_replay_is_byte_deterministic(self):
        self.assertEqual(replay_bytes(self.graph), replay_bytes(build_integrated_graph(**self.inputs)))

    def test_08_canonical_json_has_no_whitespace_ambiguity(self):
        self.assertEqual(canonical({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_09_route_a_sha_tamper_rejected(self):
        data = bytearray(self.inputs["route_a"]); data[-3] ^= 1
        with self.assertRaisesRegex(ValueError, "ROUTE_A_SOURCE_SHA_MISMATCH"):
            build_integrated_graph(route_a=bytes(data), route_b=self.inputs["route_b"], route_c=self.inputs["route_c"])

    def test_10_route_b_sha_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "ROUTE_B_SOURCE_SHA_MISMATCH"):
            build_integrated_graph(route_a=self.inputs["route_a"], route_b=b"{}", route_c=self.inputs["route_c"])

    def test_11_route_c_sha_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "ROUTE_C_SOURCE_SHA_MISMATCH"):
            build_integrated_graph(route_a=self.inputs["route_a"], route_b=self.inputs["route_b"], route_c=b"{}")

    def test_12_duplicate_object_rejected(self):
        g = self.fresh(); g["objects"].append(copy.deepcopy(g["objects"][0])); self.reject(g, "DUPLICATE_OBJECT_ID")

    def test_13_dangling_parent_rejected(self):
        g = self.fresh(); g["relationships"][0]["parent_id"] = "missing"; self.reject(g, "DANGLING_RELATION")

    def test_14_dangling_child_rejected(self):
        g = self.fresh(); g["relationships"][0]["child_id"] = "missing"; self.reject(g, "DANGLING_RELATION")

    def test_15_cross_route_relation_rejected(self):
        g = self.fresh(); e = g["relationships"][0]
        other = next(o for o in g["objects"] if o["route"] != e["route"] and o["symbol"] == "ETHUSDT")
        e["child_id"] = other["object_id"]; self.reject(g, "CROSS_ROUTE_OR_SYMBOL_RELATION|DANGLING|FORGED")

    def test_16_duplicate_relation_rejected(self):
        g = self.fresh(); g["relationships"].append(copy.deepcopy(g["relationships"][0])); self.reject(g, "DUPLICATE_RELATION|FORGED_SCENARIO")

    def test_17_invalid_object_knowledge_rejected(self):
        g = self.fresh(); g["objects"][0]["known_at_ms"] = -1; self.reject(g, "INVALID_OBJECT_IDENTITY_OR_KNOWLEDGE")

    def test_18_forged_object_id_rejected(self):
        g = self.fresh(); g["objects"][0]["object_id"] = "iso02-route_a-forged"; self.reject(g, "FORGED_OBJECT_FIELDS")

    def test_19_author_identity_promotion_rejected(self):
        g = self.fresh(); g["objects"][0]["author_identity_approved"] = True; self.reject(g, "FORGED_OBJECT_FIELDS")

    def test_20_semantic_class_promotion_rejected(self):
        g = self.fresh(); g["objects"][0]["semantic_class"] = "ACADEMIC_CORE"; self.reject(g, "FORGED_OBJECT_FIELDS")

    def test_21_graph_readiness_promotion_rejected(self):
        g = self.fresh(); g["readiness"] = "TRADE_READY"; self.reject(g, "GRAPH_CONTRACT")

    def test_22_decision_promotion_rejected(self):
        g = self.fresh(); g["decision_state"] = "ENTER_LONG"; self.reject(g, "DECISION_GATE")

    def test_23_order_injection_rejected(self):
        g = self.fresh(); g["orders"] = [{"symbol": "ETHUSDT"}]; self.reject(g, "EXECUTION_CONTENT")

    def test_24_fill_injection_rejected(self):
        g = self.fresh(); g["fills"] = [{"price": "1"}]; self.reject(g, "EXECUTION_CONTENT")

    def test_25_trade_injection_rejected(self):
        g = self.fresh(); g["trades"] = [{"pnl": 1}]; self.reject(g, "EXECUTION_CONTENT")

    def test_26_pnl_injection_rejected(self):
        g = self.fresh(); g["PnL"] = 100; self.reject(g, "DECISION_GATE")

    def test_27_scenario_author_promotion_rejected(self):
        g = self.fresh(); g["scenarios"][0]["author_scenario_state"] = "VALID_AUTHOR_LONG"; self.reject(g, "SCENARIO_SEMANTIC_OR_DECISION")

    def test_28_scenario_entry_injection_rejected(self):
        g = self.fresh(); g["scenarios"][0]["entry"] = "1"; self.reject(g, "SCENARIO_EXECUTION_CONTENT")

    def test_29_scenario_stop_injection_rejected(self):
        g = self.fresh(); g["scenarios"][0]["stop"] = "1"; self.reject(g, "SCENARIO_EXECUTION_CONTENT")

    def test_30_scenario_target_injection_rejected(self):
        g = self.fresh(); g["scenarios"][0]["target"] = "1"; self.reject(g, "SCENARIO_EXECUTION_CONTENT")

    def test_31_scenario_order_injection_rejected(self):
        g = self.fresh(); g["scenarios"][0]["orders"] = [1]; self.reject(g, "SCENARIO_EXECUTION_CONTENT")

    def test_32_scenario_child_binding_rejected(self):
        g = self.fresh(); s = next(s for s in g["scenarios"] if s["child_ids"]); s["child_ids"] = []
        self.reject(g, "SCENARIO_RELATION_BINDING|FORGED_SCENARIO")

    def test_33_scenario_state_forgery_rejected(self):
        g = self.fresh(); g["scenarios"][0]["observed_scenario_state"] = "FORGED"; self.reject(g, "FORGED_SCENARIO")

    def test_34_scenario_asof_forgery_rejected(self):
        g = self.fresh(); g["scenarios"][0]["as_of_ms"] += 1; self.reject(g, "FORGED_SCENARIO")

    def test_35_semantic_gate_removal_rejected(self):
        g = self.fresh(); g["semantic_gates"] = []; self.reject(g, "GATE_OR_SOURCE_MUTATION")

    def test_36_source_manifest_mutation_rejected(self):
        g = self.fresh(); g["sources"]["route_a"]["sha256"] = "0" * 64; self.reject(g, "GATE_OR_SOURCE_MUTATION")

    def test_37_relation_timestamp_forgery_rejected(self):
        g = self.fresh(); e = next(e for e in g["relationships"] if e["relation"] == "SUBSEQUENT_CHILD")
        child = next(o for o in g["objects"] if o["object_id"] == e["child_id"]); child["known_at_ms"] = 0
        self.reject(g, "FORGED_OBJECT_FIELDS|NON_SUBSEQUENT_CHILD")

    def test_38_route_b_preknown_relation_present(self):
        relations = [e for e in self.graph["relationships"] if e["route"] == "route_b"]
        self.assertEqual(len(relations), 29)
        self.assertTrue(all(e["relation"] == "PREKNOWN_AT_CONTACT" for e in relations))

    def test_39_route_c_single_child_absence_preserved(self):
        states = {s["observed_scenario_state"] for s in self.graph["scenarios"] if s["route"] == "route_c"}
        self.assertIn("ONLY_3M_CHILD_BREAK_OBSERVED_5M_ABSENT_IN_COMPLETE_SOURCE", states)
        self.assertIn("ONLY_5M_CHILD_BREAK_OBSERVED_3M_ABSENT_IN_COMPLETE_SOURCE", states)

    def test_40_right_censorship_not_absence(self):
        censored = [s for s in self.graph["scenarios"] if s["observed_scenario_state"] == "RIGHT_CENSORED_UNKNOWN"]
        self.assertEqual(len(censored), 6)

    def test_41_author_bos_not_promoted(self):
        children = [o for o in self.graph["objects"] if o["route"] == "route_c" and not o["kind"].endswith("parent")]
        self.assertTrue(children)
        self.assertTrue(all(o["payload"]["author_bos_approved"] is False for o in children))

    def test_42_route_a_vc_not_promoted(self):
        children = [o for o in self.graph["objects"] if o["kind"] == "native15m_imb"]
        self.assertTrue(all(o["payload"]["academic_vc_certified"] is False for o in children))

    def test_43_route_b_idm_not_promoted(self):
        children = [o for o in self.graph["objects"] if o["kind"] == "preknown1h_liquidity"]
        self.assertTrue(all(o["payload"]["author_idm_certified"] is False for o in children))

    def test_44_scenario_duplicate_rejected(self):
        g = self.fresh(); g["scenarios"].append(copy.deepcopy(g["scenarios"][0])); self.reject(g, "SCENARIO_IDENTITY")

    def test_45_parent_scenario_coverage_rejected(self):
        g = self.fresh(); g["scenarios"].pop(); self.reject(g, "PARENT_SCENARIO_COVERAGE")

    def test_46_replay_validates_before_serializing(self):
        g = self.fresh(); g["trades"] = [1]
        with self.assertRaisesRegex(ValueError, "EXECUTION_CONTENT"):
            replay_bytes(g)


if __name__ == "__main__":
    unittest.main(verbosity=2)
