"""ISO02: deterministic, read-only Ember perception/relationship/scenario layer.

PAPER ONLY - NOT_TRADE_READY. No order, decision, execution or PnL API exists.
Only the three pinned frozen evidence contracts are accepted. Technical geometry
never gets promoted to author-certified POI, VC, IDM, BOS, StrongHL or FTA.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA = "EMBER_ISO02_INTEGRATED_PERCEPTION_RELATIONSHIP_SCENARIO_V1"
SOURCE_COMMIT = "46a57eaa38c1e6f03cabf8b6d3be8d1a69f311cf"
READINESS = "NOT_TRADE_READY"
DECISION_STATE = "BLOCKED_SEMANTIC_GATE"
EXPECTED = {
    "route_a": {
        "sha256": "3ce556499294bb005f4ecfc57a817488ab6a66ef498c1181ceca2874acff1b95",
        "schema": "EMBER_C57_FRESH_BINANCE_USDM_ORIGINAL45ZIP_4H_SOURCE_FIRST3M_TOUCH_LATER1H_TO_FIRST_ANY_NATIVE15M_IMB_V1",
        "source": "evidence/c57/C57_ORIGINAL_45ZIP_4H_FIRST_CONTACT_LATER_1H_THEN_FIRST_ANY_NATIVE15M_IMB.json",
    },
    "route_b": {
        "sha256": "405a34b939845357412ab4ec2d055d71885e3f6a1b22f55bc25c87c60272808e",
        "schema": "EMBER_C58_ORIGINAL45ZIP_CRYPTO_1H_PREKNOWN_INSIDE_4H_TECHNICAL_IMB_FIRST_3M_CONTACT_SOURCE_V1",
        "source": "evidence/c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json",
    },
    "route_c": {
        "sha256": "f7fd818804d46daee493bdb473558610e3db14a3bb1a59408d9b2bd1250a55fa",
        "schema": "EMBER_ISO01_FROZEN_C56_PARENT_OBJECT_STATE_REGISTRY_V1",
        "source": "ISO01 deterministic replay of frozen C56 evidence",
    },
}
SEMANTIC_GATES = (
    {"capability": "AUTHOR_TYPED_POI_AND_VALID_TEST", "state": "NEEDS_SOURCE"},
    {"capability": "AUTHOR_VOLUME_CONFIRMATION_VC", "state": "NEEDS_SOURCE"},
    {"capability": "AUTHOR_IDM_STRONGHL_AND_AHEAD", "state": "NEEDS_SOURCE"},
    {"capability": "AUTHOR_TIMESTAMPED_BOS", "state": "NEEDS_SOURCE"},
    {"capability": "AUTHOR_FTA_SESSION_AND_STRUCTURED_STOP", "state": "NEEDS_SOURCE"},
    {"capability": "AUTHOR_ENTRY_DECISION_AND_GOLDENS", "state": "NEEDS_SOURCE"},
    {"capability": "EXECUTION_PAPER_OOS_AND_PERFORMANCE", "state": "NOT_STARTED"},
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(route: str, kind: str, fields: Mapping[str, Any]) -> str:
    digest = _sha(("EMBER_ISO02_OBJECT_V1\0" + canonical([route, kind, fields])).encode())
    return f"iso02-{route}-{kind}-{digest}"


def _decode(route: str, data: bytes) -> dict[str, Any]:
    contract = EXPECTED[route]
    if _sha(data) != contract["sha256"]:
        raise ValueError(f"ISO02_{route.upper()}_SOURCE_SHA_MISMATCH")
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict) or value.get("schema") != contract["schema"]:
        raise ValueError(f"ISO02_{route.upper()}_SOURCE_SCHEMA_MISMATCH")
    if value.get("readiness") != READINESS:
        raise ValueError(f"ISO02_{route.upper()}_READINESS_PROMOTION")
    for forbidden in ("orders", "fills", "trades"):
        if value.get(forbidden) not in (0, [], None):
            raise ValueError(f"ISO02_{route.upper()}_EXECUTION_CONTENT")
    return value


def _observations(source: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    result = [dict(item) for market in source["markets"] for item in market[key]]
    return result


def _obj(route: str, symbol: str, kind: str, identity: Mapping[str, Any], known_at_ms: int,
         state: str, source_status: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not symbol or not isinstance(known_at_ms, int) or known_at_ms < 0:
        raise ValueError("ISO02_INVALID_OBJECT_IDENTITY_OR_KNOWLEDGE")
    return {
        "object_id": _identity(route, kind, identity), "route": route, "symbol": symbol,
        "kind": kind, "identity": dict(identity), "known_at_ms": known_at_ms, "observation_state": state,
        "source_status": source_status, "semantic_class": "ADAPTED_ENGINE",
        "author_identity_approved": False, "payload": dict(payload),
    }


def _edge(route: str, parent: Mapping[str, Any], child: Mapping[str, Any], relation: str) -> dict[str, Any]:
    if parent["route"] != route or child["route"] != route or parent["symbol"] != child["symbol"]:
        raise ValueError("ISO02_CROSS_ROUTE_OR_SYMBOL_RELATION")
    if relation == "SUBSEQUENT_CHILD" and child["known_at_ms"] <= parent["known_at_ms"]:
        raise ValueError("ISO02_NON_SUBSEQUENT_CHILD")
    if relation == "PREKNOWN_AT_CONTACT":
        contact = parent["payload"].get("first_contact_bar_start_ms")
        if contact is None or child["known_at_ms"] > contact:
            raise ValueError("ISO02_NOT_PREKNOWN_AT_CONTACT")
    return {"route": route, "parent_id": parent["object_id"], "child_id": child["object_id"],
            "relation": relation, "causality": "SOURCE_OBSERVED_NOT_AUTHOR_CERTIFIED"}


def _scenario(route: str, parent: Mapping[str, Any], children: list[Mapping[str, Any]]) -> dict[str, Any]:
    status = parent["source_status"]
    if route == "route_a":
        if status.startswith("FIRST_ANY_"):
            state = "TECHNICAL_4H_3M_1H_15M_SEQUENCE_OBSERVED"
        elif status == "RIGHT_CENSORED_NO_15M_IMB_BY_SOURCE_END":
            state = "RIGHT_CENSORED_UNKNOWN"
        else:
            state = "ABSENT_IN_COMPLETE_FROZEN_SOURCE"
    elif route == "route_b":
        state = ("PREKNOWN_UNSWEPT_CHILD_CANDIDATES_OBSERVED" if children
                 else "ABSENT_OR_NO_CONTACT_IN_COMPLETE_FROZEN_SOURCE")
    else:
        state = parent["observation_state"]
    return {
        "scenario_id": _identity(route, "scenario", {"parent_id": parent["object_id"]}),
        "route": route, "symbol": parent["symbol"], "parent_id": parent["object_id"],
        "child_ids": sorted(c["object_id"] for c in children), "as_of_ms": max(
            [parent["known_at_ms"]] + [c["known_at_ms"] for c in children]),
        "observed_scenario_state": state, "author_scenario_state": "UNKNOWN",
        "decision_state": DECISION_STATE, "entry": None, "stop": None, "target": None,
        "orders": [], "fills": [], "trades": [], "PnL": None, "readiness": READINESS,
    }


def _route_a(source: Mapping[str, Any]) -> tuple[list[dict], list[dict], list[dict]]:
    objects, edges, scenarios = [], [], []
    for o in _observations(source, "complete_original_source_observations"):
        symbol, status = o["symbol"], o["source_status"]
        ident = {"symbol": symbol, "4h_known": o["fourh_source_known_ms"],
                 "3m_contact": o["original3m_first_contact_id"],
                 "1h_known": o["subsequent_1h_source_known_ms"], "side": o["fourh_source_side"]}
        parent = _obj(route="route_a", symbol=symbol, kind="4h_parent", identity=ident,
                      known_at_ms=o["fourh_source_known_ms"], state="OBSERVED", source_status=status,
                      payload={"side": o["fourh_source_side"], "first_contact_known_ms": o["original3m_first_contact_known_ms"],
                               "subsequent_1h_source_known_ms": o["subsequent_1h_source_known_ms"], "blockers": o["blockers"]})
        objects.append(parent); children = []
        gap = o["first_any_15m_imb"]
        if gap is not None:
            if gap["fully_known_ms"] <= parent["known_at_ms"]:
                raise ValueError("ISO02_ROUTE_A_LOOKAHEAD_OR_PRE_PARENT_CHILD")
            child = _obj("route_a", symbol, "native15m_imb", {"parent": ident, "first_start": gap["first_start_ms"],
                         "raw_ids": gap["original_native15m_ids"]}, gap["fully_known_ms"], "OBSERVED", status,
                         {"side": gap["side"], "top": gap["top"], "bottom": gap["bottom"],
                          "academic_vc_certified": gap["academic_vc_certified"]})
            objects.append(child); children.append(child)
            edges.append(_edge("route_a", parent, child, "SUBSEQUENT_CHILD"))
        scenarios.append(_scenario("route_a", parent, children))
    return objects, edges, scenarios


def _route_b(source: Mapping[str, Any]) -> tuple[list[dict], list[dict], list[dict]]:
    objects, edges, scenarios = [], [], []
    for o in _observations(source, "source_observations"):
        symbol, status = o["symbol"], o["source_state"]
        ident = {"symbol": symbol, "4h_known": o["four_hour_gap_fully_known_ms"],
                 "3m_contact": o["first_contact_original3m_id"], "side": o["technical_4h_imb_side"],
                 "top": o["technical_4h_imb_top"], "bottom": o["technical_4h_imb_bottom"]}
        parent = _obj("route_b", symbol, "4h_parent", ident, o["four_hour_gap_fully_known_ms"],
                      "OBSERVED", status, {"side": o["technical_4h_imb_side"], "top": o["technical_4h_imb_top"],
                      "bottom": o["technical_4h_imb_bottom"], "first_contact_bar_start_ms": o["first_contact_bar_start_ms"],
                      "blockers": o["blockers"]})
        objects.append(parent); children = []
        for p in o["preknown_inside_1h_liquidity"]:
            child = _obj("route_b", symbol, "preknown1h_liquidity", {"parent": ident, "pivot_center": p["pivot_center_ms"],
                         "raw_id": p["pivot_original_native3m_center_row_id"], "kind": p["kind"], "level": p["level"]},
                         p["pivot_fully_known_ms"], "PREKNOWN_UNSWEPT_AT_CONTACT", status,
                         {"kind": p["kind"], "level": p["level"], "unswept_until_contact_bar_start": p["unswept_until_contact_bar_start"],
                          "author_idm_certified": p["author_idm_certified"], "strong_high_low_author_certified": p["strong_high_low_author_certified"]})
            objects.append(child); children.append(child)
            edges.append(_edge("route_b", parent, child, "PREKNOWN_AT_CONTACT"))
        scenarios.append(_scenario("route_b", parent, children))
    return objects, edges, scenarios


def _route_c(source: Mapping[str, Any]) -> tuple[list[dict], list[dict], list[dict]]:
    objects, edges, scenarios = [], [], []
    for s in source["parent_states"]:
        p = s["parent"]
        if s["readiness"] != READINESS or s["orders"] or s["fills"] or s["trades"]:
            raise ValueError("ISO02_ROUTE_C_EXECUTION_OR_READINESS_PROMOTION")
        ident = {"symbol": p["symbol"], "raid_type": p["raid_type"], "pivot": p["first_1h_pivot_center_ms"],
                 "breach": p["first_1h_breach_ms"], "raid_known": p["raid_closed_known_ms"]}
        parent = _obj("route_c", p["symbol"], "1h_raid_parent", ident, p["raid_closed_known_ms"],
                      s["observation_state"], p["source_status"], {"raid_type": p["raid_type"], "blockers": p["blockers"]})
        objects.append(parent); children = []
        for tf, key, raw in (("3m", "original_3m_bos_known_ms", "original_3m_bos_raw_id"),
                             ("5m", "original_5m_bos_known_ms", "original_5m_bos_raw_id")):
            if p[key] is None:
                continue
            child = _obj("route_c", p["symbol"], f"native{tf}_break", {"parent": ident, "tf": tf, "raw_id": p[raw]},
                         p[key], "OBSERVED", p["source_status"], {"timeframe": tf, "author_bos_approved": p["author_bos_approved"]})
            objects.append(child); children.append(child)
            edges.append(_edge("route_c", parent, child, "SUBSEQUENT_CHILD"))
        scenarios.append(_scenario("route_c", parent, children))
    return objects, edges, scenarios


def build_integrated_graph(*, route_a: bytes, route_b: bytes, route_c: bytes) -> dict[str, Any]:
    decoded = {name: _decode(name, data) for name, data in
               (("route_a", route_a), ("route_b", route_b), ("route_c", route_c))}
    objects: list[dict] = []; edges: list[dict] = []; scenarios: list[dict] = []
    for name, builder in (("route_a", _route_a), ("route_b", _route_b), ("route_c", _route_c)):
        o, e, s = builder(decoded[name]); objects.extend(o); edges.extend(e); scenarios.extend(s)
    objects.sort(key=lambda x: x["object_id"]); edges.sort(key=lambda x: (x["parent_id"], x["child_id"], x["relation"]))
    scenarios.sort(key=lambda x: x["scenario_id"])
    graph = {"schema": SCHEMA, "scope": "READ_ONLY_PERCEPTION_IDENTIFICATION_STATE_RELATIONSHIP_SCENARIO",
             "source_commit": SOURCE_COMMIT, "sources": EXPECTED, "objects": objects,
             "relationships": edges, "scenarios": scenarios, "semantic_gates": list(SEMANTIC_GATES),
             "cross_route_relationships": 0, "decision_state": DECISION_STATE, "readiness": READINESS,
             "orders": [], "fills": [], "trades": [], "PnL": None}
    validate_integrated_graph(graph)
    return graph


def validate_integrated_graph(graph: Mapping[str, Any]) -> None:
    if graph.get("schema") != SCHEMA or graph.get("readiness") != READINESS:
        raise ValueError("ISO02_GRAPH_CONTRACT")
    if graph.get("decision_state") != DECISION_STATE or graph.get("PnL") is not None:
        raise ValueError("ISO02_DECISION_GATE")
    if any(graph.get(k) for k in ("orders", "fills", "trades")):
        raise ValueError("ISO02_EXECUTION_CONTENT")
    objects = graph["objects"]; ids = [o["object_id"] for o in objects]
    if len(ids) != len(set(ids)):
        raise ValueError("ISO02_DUPLICATE_OBJECT_ID")
    by_id = {o["object_id"]: o for o in objects}
    for o in objects:
        expected = _obj(o["route"], o["symbol"], o["kind"], o["identity"],
                        o["known_at_ms"], o["observation_state"], o["source_status"], o["payload"])
        if dict(o) != expected:
            raise ValueError("ISO02_FORGED_OBJECT_FIELDS")
        if o["semantic_class"] != "ADAPTED_ENGINE" or o["author_identity_approved"] is not False:
            raise ValueError("ISO02_SEMANTIC_PROMOTION")
        if not o["object_id"].startswith(f"iso02-{o['route']}-") or o["known_at_ms"] < 0:
            raise ValueError("ISO02_OBJECT_BINDING")
    edge_keys = set()
    for e in graph["relationships"]:
        if e["route"] not in EXPECTED or e["causality"] != "SOURCE_OBSERVED_NOT_AUTHOR_CERTIFIED":
            raise ValueError("ISO02_RELATION_CONTRACT")
        p, c = by_id.get(e["parent_id"]), by_id.get(e["child_id"])
        if p is None or c is None:
            raise ValueError("ISO02_DANGLING_RELATION")
        checked = _edge(e["route"], p, c, e["relation"])
        if checked != dict(e):
            raise ValueError("ISO02_FORGED_RELATION")
        key = (e["parent_id"], e["child_id"], e["relation"])
        if key in edge_keys:
            raise ValueError("ISO02_DUPLICATE_RELATION")
        edge_keys.add(key)
    if graph["cross_route_relationships"] != 0:
        raise ValueError("ISO02_CROSS_ROUTE_COUNT")
    scenario_ids = set()
    for s in graph["scenarios"]:
        if s["scenario_id"] in scenario_ids or s["parent_id"] not in by_id:
            raise ValueError("ISO02_SCENARIO_IDENTITY")
        scenario_ids.add(s["scenario_id"])
        if s["author_scenario_state"] != "UNKNOWN" or s["decision_state"] != DECISION_STATE:
            raise ValueError("ISO02_SCENARIO_SEMANTIC_OR_DECISION_PROMOTION")
        if any(s[k] is not None for k in ("entry", "stop", "target")) or any(s[k] for k in ("orders", "fills", "trades")):
            raise ValueError("ISO02_SCENARIO_EXECUTION_CONTENT")
        if s["readiness"] != READINESS or s["PnL"] is not None:
            raise ValueError("ISO02_SCENARIO_READINESS")
        p = by_id[s["parent_id"]]
        expected_children = sorted(e["child_id"] for e in graph["relationships"] if e["parent_id"] == p["object_id"])
        if s["child_ids"] != expected_children or s["route"] != p["route"] or s["symbol"] != p["symbol"]:
            raise ValueError("ISO02_SCENARIO_RELATION_BINDING")
        expected_scenario = _scenario(s["route"], p, [by_id[i] for i in s["child_ids"]])
        if dict(s) != expected_scenario:
            raise ValueError("ISO02_FORGED_SCENARIO")
    if len(graph["scenarios"]) != len([o for o in objects if o["kind"].endswith("parent")]):
        raise ValueError("ISO02_PARENT_SCENARIO_COVERAGE")
    if graph["semantic_gates"] != list(SEMANTIC_GATES) or graph["sources"] != EXPECTED:
        raise ValueError("ISO02_GATE_OR_SOURCE_MUTATION")


def replay_bytes(graph: Mapping[str, Any]) -> bytes:
    validate_integrated_graph(graph)
    return (canonical(graph) + "\n").encode("utf-8")
