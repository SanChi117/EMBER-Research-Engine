"""D05/F01: exact 5-route teaching topology, negative and positive evidence checks.

These tests do NOT assert that any volume confirmation was identified from
price charts. All proof labels are artificial infrastructure fixtures.
"""
from dataclasses import FrozenInstanceError,replace
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch

H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import tda_source_route_contract as route
from tda_source_route_contract import RouteStepEvidence,TDARouteRejected,inspect_tda_route,KNOWN_ROUTES,STEP_TF

T=1790899200000
SPAN={"1d":86400000,"4h":14400000,"1h":3600000,"15m":900000,"5m":300000}
TIMES={"1d":T,"4h":T+14400000,"1h":T+18000000,"15m":T+18900000,"5m":T+19200000}

def evidence(color,full=True):
    names=list(KNOWN_ROUTES[color])
    if not full:names=names[:-1]
    return [RouteStepEvidence(name,STEP_TF[name],TIMES[STEP_TF[name]],
            f"{color}-source-{i}","BTCUSDT") for i,name in enumerate(names)]
def inspect(color="RED",xs=None,at=T+24*3600000):
    return inspect_tda_route(color,evidence(color) if xs is None else xs,at)
class SourceTopologyContract(unittest.TestCase):
    def test_five_author_routes_exactly_match_original_image(self):
        x=route.verify_source_route_schema()
        self.assertEqual(set(x),set(KNOWN_ROUTES))
        self.assertEqual(len(x),5)

    def test_all_five_have_correct_tf_source_chain_and_no_ready(self):
        for color in KNOWN_ROUTES:
            with self.subTest(color=color):
                a=inspect(color)
                self.assertEqual(a.step_names,KNOWN_ROUTES[color])
                self.assertEqual(a.missing_step_names,())
                self.assertEqual(a.readiness,"NOT_TRADE_READY")

    def test_five_minute_routes_do_not_silently_use_15m_proxy(self):
        for color in ("GREEN","BLUE"):
            a=inspect(color)
            self.assertIn("5M_VC_ENTRY",a.data_gaps)
            self.assertEqual(a.readiness,"NOT_TRADE_READY")

    def test_15m_final_routes_do_not_require_imaginary_5m(self):
        for color in ("ORANGE","RED","YELLOW"):
            a=inspect(color)
            self.assertNotIn("5M_VC_ENTRY",a.data_gaps)
            self.assertEqual(a.step_names[-1],"15M_VC_ENTRY")

    def test_partial_branch_is_not_misreported_complete(self):
        xs=evidence("GREEN",full=False)
        a=inspect("GREEN",xs)
        self.assertEqual(a.missing_step_names,("5M_VC_ENTRY",))
        self.assertEqual(a.readiness,"NOT_TRADE_READY")

    def test_missing_daily_context_is_not_silently_substituted(self):
        xs=evidence("RED")[1:]
        with self.assertRaisesRegex(TDARouteRejected,"OUT_OF_ORDER_OR_FALSE_BRANCH"):
            inspect("RED",xs)

    def test_wrong_child_resolution_from_chart_rejected(self):
        xs=evidence("GREEN")
        xs[-1]=replace(xs[-1],timeframe="15m")
        with self.assertRaisesRegex(TDARouteRejected,"TIMEFRAME_DOES_NOT_MATCH_AUTHOR_BRANCH"):
            inspect("GREEN",xs)

    def test_wrong_branch_composition_detected(self):
        xs=evidence("GREEN")
        xs[1]=replace(xs[1],name="4H_VC_POI")
        with self.assertRaisesRegex(TDARouteRejected,"OUT_OF_ORDER_OR_FALSE_BRANCH"):
            inspect("GREEN",xs)

    def test_wrong_child_order_detected(self):
        xs=evidence("RED")
        xs[1],xs[2]=xs[2],xs[1]
        with self.assertRaisesRegex(TDARouteRejected,"OUT_OF_ORDER_OR_FALSE_BRANCH"):
            inspect("RED",xs)

    def test_unclosed_future_confirmation_rejected(self):
        xs=evidence("RED")
        with self.assertRaisesRegex(TDARouteRejected,"LOOKAHEAD_OR_UNORDERED_EVIDENCE"):
            inspect("RED",xs,at=T+14400000)

    def test_out_of_order_known_at_rejected(self):
        xs=evidence("RED")
        xs[2]=replace(xs[2],known_at_ms=T+3600000)
        with self.assertRaisesRegex(TDARouteRejected,"LOOKAHEAD_OR_UNORDERED_EVIDENCE"):
            inspect("RED",xs)

    def test_fake_not_closed_tf_confirmation_rejected(self):
        xs=evidence("RED")
        xs[1]=replace(xs[1],known_at_ms=T+14400000+1)
        with self.assertRaisesRegex(TDARouteRejected,"EVENT_KNOWN_AT_NOT_CLOSED_TF"):
            inspect("RED",xs)

    def test_lookahead_future_suffix_does_not_affect_already_known_prefix(self):
        xs=evidence("RED",full=False)
        v=inspect("RED",xs,at=T+18000000)
        trailing=evidence("RED")[-1]
        self.assertEqual(v,inspect("RED",xs,at=T+18000000))
        self.assertGreater(trailing.known_at_ms,v.available_at_ms)

    def test_cross_symbol_in_branch_rejected(self):
        xs=evidence("RED")
        xs[1]=replace(xs[1],symbol="ETHUSDT")
        with self.assertRaisesRegex(TDARouteRejected,"CROSS_SYMBOL_ROUTE"):
            inspect("RED",xs)

    def test_spot_source_rejected(self):
        xs=evidence("RED")
        xs[0]=replace(xs[0],market="SPOT")
        with self.assertRaisesRegex(TDARouteRejected,"WRONG_SOURCE_MARKET"):
            inspect("RED",xs)

    def test_duplicate_event_uid_rejected(self):
        xs=evidence("RED")
        xs[2]=replace(xs[2],source_uid=xs[1].source_uid)
        with self.assertRaisesRegex(TDARouteRejected,"MISSING_OR_REUSED_EVENT_SOURCE_UID"):
            inspect("RED",xs)

    def test_self_approved_course_label_rejected(self):
        xs=evidence("RED")
        xs[-1]=replace(xs[-1],course_semantics_approved=True)
        with self.assertRaisesRegex(TDARouteRejected,"SELF_ASSERTED_COURSE_APPROVAL_NOT_ACCEPTED"):
            inspect("RED",xs)

    def test_faked_five_minute_c08_native_certificate_rejected(self):
        xs=evidence("GREEN")
        xs[-1]=replace(xs[-1],c08_native_source_verified=True)
        with self.assertRaisesRegex(TDARouteRejected,"5M_NOT_PRESENT_IN_C08_ATTESTED_MANIFEST"):
            inspect("GREEN",xs)

    def test_incomplete_or_forged_evidence_is_not_course_signal(self):
        xs=evidence("RED")
        xs[0]=replace(xs[0],c08_native_source_verified=True)
        xs[-1]=replace(xs[-1],c08_native_source_verified=True)
        out=inspect("RED",xs)
        self.assertEqual(out.readiness,"NOT_TRADE_READY")
        self.assertEqual(len(out.semantic_gaps),len(xs))

    def test_unrecognized_route_color_fails(self):
        with self.assertRaisesRegex(TDARouteRejected,"UNKNOWN_ROUTE_COLOR"):
            inspect_tda_route("PURPLE",[],T)

    def test_route_extra_undocumented_step_fails(self):
        xs=evidence("RED")
        xs.append(replace(xs[-1],source_uid="fake-extra"))
        with self.assertRaisesRegex(TDARouteRejected,"EXTRA_ROUTE_STEPS"):
            inspect("RED",xs)

    def test_source_schema_injection_attempt_fails_closed(self):
        raw=json.loads(route.TOPOLOGY.read_text(encoding="utf8"))
        raw["paths"][0]["steps"].append("5M_VC_ENTRY")
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"unverified.json"
            path.write_text(json.dumps(raw),encoding="utf8")
            with patch.object(route,"TOPOLOGY",path):
                with self.assertRaisesRegex(TDARouteRejected,"COURSE_BRANCH_OR_TF_CHANGED"):
                    route.verify_source_route_schema()

    def test_cannot_edit_a_pass_into_ready(self):
        x=inspect()
        with self.assertRaises(FrozenInstanceError):
            x.readiness="READY"
if __name__=="__main__":
    unittest.main(verbosity=2)
