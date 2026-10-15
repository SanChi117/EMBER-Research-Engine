"""B1/C03 adversarial provenance contract tests. Synthetic bars are NOT academy labels."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest

D05=Path(__file__).resolve().parent
BASE=D05.parent
sys.path.insert(0,str(D05))
sys.path.insert(0,str(BASE/"tools"))
sys.path.insert(0,str(BASE.parent/"mtf-course-v05"/"src"))

from strict_event_lineage_d03 import CausalEvent, EventLedger, D03Rejected
from course_primitives_v05 import Bar
from poi_price_lineage_b1 import (
    ZoneReference, BarWitness, PriceLineageRejected, GeometricLink,
    bar_digest, link_test_contact, link_vc_after_test
)

TF=900_000
HR=3600_000
COURSE="https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view"

def testbar(l=99,h=104,tf="15m",start=HR):
    step=TF if tf=="15m" else 300_000
    return Bar(start,start+step,102,h,l,102,tf)

def vcbar(start=HR+TF):
    return Bar(start,start+TF,110,112,108,111,"15m")

def event(uid,kind,start,end,known,parents=(),evidence=("evidence",),
          tf="15m",symbol="BTCUSDT",venue="BINANCE",market="USDM_FUTURES"):
    return CausalEvent(uid,kind,symbol,venue,market,tf,start,end,known,
                       tuple(parents),tuple(evidence))

def fixture(*, bar=None, with_vc=False, parent_test=True, market="USDM_FUTURES",
            test_symbol="BTCUSDT", vc_parent="test", test_source_sha=None):
    b=bar if bar is not None else testbar()
    v=vcbar()
    g=EventLedger()
    g.add(event("parent_source","SOURCE",0,HR,HR,tf="1h",market=market))
    g.add(event("poi","POI",0,HR,HR,("parent_source",),("course-poi",),
                tf="1h",market=market))
    g.add(event("test_source","SOURCE",b.start,b.end,b.end,
                evidence=(test_source_sha or bar_digest(b),),tf=b.tf,
                market=market))
    g.add(event("test","TEST",b.start,b.end,b.end,
                ("poi",) if parent_test else ("test_source",),("test_source",),
                tf=b.tf,symbol=test_symbol,market=market))
    zone=ZoneReference("poi","parent_source",COURSE,"LONG","1h",98,100,
                       HR,"BTCUSDT","BINANCE",market)
    witness=BarWitness("test_source","test",b,"BTCUSDT","BINANCE",market,"LONG")
    vw=BarWitness("vc_source","vc",v,"BTCUSDT","BINANCE",market,"LONG")
    if with_vc:
        g.add(event("vc_source","SOURCE",v.start,v.end,v.end,evidence=(bar_digest(v),),
                    market=market))
        g.add(event("vc","VC",v.start,v.end,v.end,(vc_parent,),("vc_source",),
                    market=market))
    return g,zone,witness,vw

class ParentChildGeometryContract(unittest.TestCase):
    def test_valid_test_source_price_intersection_is_diagnostic_only(self):
        g,z,w,_=fixture()
        a=link_test_contact(g,z,w,HR+TF)
        self.assertEqual(a.relation,"TEST_PRICE_INTERSECTION_ONLY_FIRSTNESS_UNPROVEN")
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
        self.assertEqual(a.status,"EVIDENCE_LINK_ONLY_NOT_ACADEMICALLY_APPROVED")
        self.assertEqual(a.bar_sha256,bar_digest(w.bar))

    def test_valid_vc_may_be_away_from_parent_price_zone(self):
        g,z,w,v=fixture(with_vc=True)
        a=link_vc_after_test(g,z,w,v,HR+2*TF)
        self.assertEqual(a.relation,"VC_CAUSALLY_AFTER_PRICE_TOUCH_SEMANTICS_UNKNOWN")
        self.assertGreater(v.bar.l,z.high)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")

    def test_outside_poi_bar_must_be_rejected(self):
        g,z,w,_=fixture(bar=testbar(l=101,h=105))
        with self.assertRaisesRegex(PriceLineageRejected,"PRICE_NEVER_INTERSECTED_POI"):
            link_test_contact(g,z,w,HR+TF)

    def test_boundary_at_poi_high_counts_only_as_observation(self):
        b=testbar(l=100,h=104)
        g,z,w,_=fixture(bar=b)
        self.assertEqual(link_test_contact(g,z,w,HR+TF).readiness,"NOT_TRADE_READY")

    def test_invalid_zone_geometry_does_not_auto_approve(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"INVALID_ZONE_GEOMETRY"):
            link_test_contact(g,replace(z,low=101,high=100),w,HR+TF)
        with self.assertRaisesRegex(PriceLineageRejected,"INVALID_ZONE_GEOMETRY"):
            link_test_contact(g,replace(z,low=float("nan")),w,HR+TF)

    def test_unverified_source_rule_uri_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"UNKNOWN_ZONE_SOURCE"):
            link_test_contact(g,replace(z,course_uri="heuristic"),w,HR+TF)

    def test_wrong_witness_side_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"SIDE_MISMATCH"):
            link_test_contact(g,z,replace(w,side="SHORT"),HR+TF)

    def test_wrong_child_symbol_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"WRONG_CHILD_INSTRUMENT"):
            link_test_contact(g,z,replace(w,symbol="ETHUSDT"),HR+TF)

    def test_wrong_child_venue_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"WRONG_CHILD_INSTRUMENT"):
            link_test_contact(g,z,replace(w,venue="KRAKEN"),HR+TF)

    def test_spot_rejected_even_if_causal_ledger_accepts_it(self):
        g,z,w,_=fixture(market="SPOT")
        with self.assertRaisesRegex(PriceLineageRejected,"NOT_FUTURES_EVIDENCE"):
            link_test_contact(g,z,w,HR+TF)

    def test_parent_zone_tf_mismatch_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"POI_ZONE_METADATA_MISMATCH"):
            link_test_contact(g,replace(z,tf="4h"),w,HR+TF)

    def test_child_tf_wrong_relative_to_observed_bar(self):
        g,z,w,_=fixture()
        other=testbar(tf="5m")
        with self.assertRaisesRegex(PriceLineageRejected,"CHILD_TIMEFRAME_OR_ORIGIN_MISMATCH"):
            link_test_contact(g,z,replace(w,bar=other),HR+TF)

    def test_missing_external_bar_binding(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"RAW_SOURCE_BAR_NOT_SAME_CANDLE"):
            link_test_contact(g,z,replace(w,source_uid="parent_source"),HR+TF)

    def test_forged_original_bar_checksum_detected(self):
        g,z,w,_=fixture(test_source_sha="0"*64)
        with self.assertRaisesRegex(PriceLineageRejected,"UNBOUND_RAW_BAR_PROVENANCE"):
            link_test_contact(g,z,w,HR+TF)

    def test_child_test_event_not_parented_to_poi(self):
        g,z,w,_=fixture(parent_test=False)
        with self.assertRaisesRegex(PriceLineageRejected,"TEST_NOT_DIRECTLY_PARENTED_BY_POI"):
            link_test_contact(g,z,w,HR+TF)

    def test_unknown_as_of_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"INVALID_LEDGER_OR_AS_OF"):
            link_test_contact(g,z,w,"later")

    def test_before_child_close_no_future_leak(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"CHILD_OR_SOURCE_NOT_KNOWN_AS_OF"):
            link_test_contact(g,z,w,HR+TF-1)

    def test_prefix_stable_even_if_future_different_bar_appears(self):
        g,z,w,_=fixture()
        old=link_test_contact(g,z,w,HR+TF)
        v=vcbar()
        g.add(event("future_source","SOURCE",v.start,v.end,v.end,evidence=(bar_digest(v),)))
        new=link_test_contact(g,z,w,HR+TF)
        self.assertEqual(old,new)

    def test_event_ledger_replay_is_identical_and_immutable(self):
        g,z,w,v=fixture(with_vc=True)
        replay=EventLedger.replay(g.export())
        self.assertEqual(g.digest(),replay.digest())
        self.assertEqual(link_test_contact(g,z,w,HR+TF),
                         link_test_contact(replay,z,w,HR+TF))
        self.assertEqual(link_vc_after_test(g,z,w,v,HR+2*TF),
                         link_vc_after_test(replay,z,w,v,HR+2*TF))
        with self.assertRaises(FrozenInstanceError):
            link_test_contact(g,z,w,HR+TF).readiness="READY"

    def test_parent_invalidation_blocks_later_geometry(self):
        g,z,w,v=fixture(with_vc=True)
        g.add(event("invalidated","INVALIDATION",HR+TF,HR+2*TF,HR+2*TF,
                    ("poi",),("invalid-evidence",)))
        with self.assertRaisesRegex(PriceLineageRejected,"POI_CAUSALLY_INVALIDATED"):
            link_test_contact(g,z,w,HR+2*TF)
        self.assertEqual(link_test_contact(g,z,w,HR+TF).readiness,"NOT_TRADE_READY")

    def test_later_vc_requires_direct_test_evidence_parent(self):
        g,z,w,v=fixture(with_vc=True,vc_parent="poi")
        with self.assertRaisesRegex(PriceLineageRejected,"VC_NOT_CAUSALLY_LINKED_TO_TEST"):
            link_vc_after_test(g,z,w,v,HR+2*TF)

    def test_forged_test_geometry_cannot_authorize_vc(self):
        g,z,w,v=fixture(bar=testbar(l=101,h=105),with_vc=True)
        with self.assertRaisesRegex(PriceLineageRejected,"PRICE_NEVER_INTERSECTED_POI"):
            link_vc_after_test(g,z,w,v,HR+2*TF)

    def test_vc_child_future_as_of_not_ready(self):
        g,z,w,v=fixture(with_vc=True)
        with self.assertRaisesRegex(PriceLineageRejected,"VC_OR_SOURCE_NOT_ACTIVE_AS_OF"):
            link_vc_after_test(g,z,w,v,HR+2*TF-1)

    def test_causal_ledger_itself_rejects_cross_market_parent(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(D03Rejected,"CROSS_INSTRUMENT_PARENT"):
            g.add(event("bad","VC",HR+TF,HR+2*TF,HR+2*TF,
                        ("test",),("test_source",),symbol="SOLUSDT"))

    def test_causal_ledger_rejects_confirmation_before_close(self):
        with self.assertRaisesRegex(D03Rejected,"UNKNOWN_UNCLOSED_EVENT"):
            event("future","TEST",HR,HR+TF,HR,("poi",),("test_source",))

    def test_unmatched_bars_are_not_full_first_test_proof(self):
        g,z,w,_=fixture()
        result=link_test_contact(g,z,w,HR+TF)
        self.assertIn("FIRSTNESS_UNPROVEN",result.relation)
        self.assertNotIn("CONFIRMED_FIRST_TEST",result.relation)

    def test_parent_zone_wrong_source_uid_rejected(self):
        g,z,w,_=fixture()
        with self.assertRaisesRegex(PriceLineageRejected,"POI_NOT_SOURCE_LINKED"):
            link_test_contact(g,replace(z,original_source_uid="test_source"),w,HR+TF)

if __name__ == "__main__":
    unittest.main(verbosity=2)
