"""B1/C03: independent PRICE provenance gate layered on C07 D03.

Checks a child's observed OHLC zone intersection and source/parent as-of
lineage. It does NOT infer academic VC, BOS, IDM, order entry or fills.
Do not modify original course-v05 or D03 implementations.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))
sys.path.insert(0, str(BASE.parent / "mtf-course-v05" / "src"))
from strict_event_lineage_d03 import CausalEvent, EventLedger
from course_primitives_v05 import Bar, TF_MS

class PriceLineageRejected(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def bar_digest(bar: Bar) -> str:
    """Deterministic local bar-object digest, not Binance origin certification."""
    record = {key: getattr(bar,key) for key in ("start","end","o","h","l","c","tf")}
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":"),
                                     allow_nan=False).encode("utf8")).hexdigest()

@dataclass(frozen=True)
class ZoneReference:
    poi_uid: str
    original_source_uid: str
    course_uri: str
    side: str
    tf: str
    low: float
    high: float
    known_at_ms: int
    symbol: str
    venue: str
    market: str

@dataclass(frozen=True)
class BarWitness:
    source_uid: str
    child_uid: str
    bar: Bar
    symbol: str
    venue: str
    market: str

@dataclass(frozen=True)
class GeometricLink:
    poi_uid: str
    child_uid: str
    source_uid: str
    known_at_ms: int
    bar_sha256: str
    relation: str
    status: str = "EVIDENCE_LINK_ONLY_NOT_ACADEMICALLY_APPROVED"
    readiness: str = "NOT_TRADE_READY"

def _snapshot(ledger: EventLedger, at: int):
    if not isinstance(ledger,EventLedger) or type(at) is not int or at < 0:
        raise PriceLineageRejected("INVALID_LEDGER_OR_AS_OF")
    all_events = {e.uid:e for e in ledger.snapshot(at)}
    active_events = {e.uid:e for e in ledger.snapshot(at,active_only=True)}
    return all_events,active_events

def _zone_parent(ledger: EventLedger, zone: ZoneReference, at: int):
    if not isinstance(zone,ZoneReference):
        raise PriceLineageRejected("INVALID_ZONE_REFERENCE")
    if zone.side not in ("LONG","SHORT") or zone.tf not in TF_MS:
        raise PriceLineageRejected("INVALID_ZONE_SIDE_OR_TF")
    if not all(isinstance(x,(int,float)) and isfinite(x) and x>0 for x in (zone.low,zone.high)) or zone.low>=zone.high:
        raise PriceLineageRejected("INVALID_ZONE_GEOMETRY")
    if type(zone.known_at_ms) is not int or not zone.course_uri.startswith("https://drive.google.com/file/d/"):
        raise PriceLineageRejected("UNKNOWN_ZONE_SOURCE")
    all_events,active=_snapshot(ledger,at)
    p=all_events.get(zone.poi_uid)
    if p is None:
        raise PriceLineageRejected("POI_NOT_KNOWN_AS_OF")
    if p.uid not in active:
        raise PriceLineageRejected("POI_CAUSALLY_INVALIDATED")
    if p.kind!="POI" or zone.original_source_uid not in p.parent_uids:
        raise PriceLineageRejected("POI_NOT_SOURCE_LINKED")
    src=all_events.get(zone.original_source_uid)
    if not src or src.kind!="SOURCE" or src.uid not in active:
        raise PriceLineageRejected("POI_SOURCE_NOT_ACTIVE")
    if (p.symbol,p.venue,p.market,p.timeframe,p.known_at_ms)!=(
        zone.symbol,zone.venue,zone.market,zone.tf,zone.known_at_ms):
        raise PriceLineageRejected("POI_ZONE_METADATA_MISMATCH")
    if zone.market!="USDM_FUTURES":
        raise PriceLineageRejected("NOT_FUTURES_EVIDENCE")
    return p,all_events,active

def _checked_observation(parent:CausalEvent, child:CausalEvent,
                         source:CausalEvent, witness: BarWitness,
                         as_of_ms:int):
    b=witness.bar
    if not isinstance(b,Bar):
        raise PriceLineageRejected("INVALID_OBSERVED_BAR")
    if b.tf not in TF_MS or b.end-b.start!=TF_MS[b.tf] or not all(isfinite(x) and x>0 for x in (b.o,b.h,b.l,b.c)):
        raise PriceLineageRejected("BAD_OBSERVED_CANDLE")
    if (parent.symbol,parent.venue,parent.market)!=(
        witness.symbol,witness.venue,witness.market) or (
        child.symbol,child.venue,child.market)!=(witness.symbol,witness.venue,witness.market):
        raise PriceLineageRejected("WRONG_CHILD_INSTRUMENT")
    if source.kind!="SOURCE" or (
        source.symbol,source.venue,source.market,source.timeframe)!=(
        witness.symbol,witness.venue,witness.market,b.tf):
        raise PriceLineageRejected("SOURCE_INSTRUMENT_OR_TF_MISMATCH")
    if child.timeframe!=b.tf or (child.origin_open_ms,child.origin_close_ms)!=(b.start,b.end):
        raise PriceLineageRejected("CHILD_TIMEFRAME_OR_ORIGIN_MISMATCH")
    if (source.origin_open_ms,source.origin_close_ms)!=(b.start,b.end):
        raise PriceLineageRejected("RAW_SOURCE_BAR_NOT_SAME_CANDLE")
    digest=bar_digest(b)
    if digest not in source.evidence_uids or source.uid not in child.evidence_uids:
        raise PriceLineageRejected("UNBOUND_RAW_BAR_PROVENANCE")
    if b.start < parent.known_at_ms or b.end > as_of_ms or source.known_at_ms>b.end or child.known_at_ms<b.end or child.known_at_ms<source.known_at_ms:
        raise PriceLineageRejected("FUTURE_OR_BACKDATED_OBSERVATION")
    return digest

def link_first_test(ledger: EventLedger, zone:ZoneReference, witness:BarWitness,
                    as_of_ms:int) -> GeometricLink:
    """Observational geometry only: zone overlaps bar's [low,high]."""
    parent,events,active=_zone_parent(ledger,zone,as_of_ms)
    child=events.get(witness.child_uid)
    src=events.get(witness.source_uid)
    if child is None or src is None:
        raise PriceLineageRejected("CHILD_OR_SOURCE_NOT_KNOWN_AS_OF")
    if child.uid not in active or src.uid not in active:
        raise PriceLineageRejected("CHILD_OR_SOURCE_CAUSALLY_INVALID")
    if child.kind!="TEST" or parent.uid not in child.parent_uids:
        raise PriceLineageRejected("TEST_NOT_DIRECTLY_PARENTED_BY_POI")
    h=_checked_observation(parent,child,src,witness,as_of_ms)
    if not witness.bar.h >= zone.low or not witness.bar.l <= zone.high:
        raise PriceLineageRejected("PRICE_NEVER_INTERSECTED_POI")
    # This is not a true first-test oracle. Firstness requires replay of the
    # complete interval since zone became known, not just this witness.
    return GeometricLink(zone.poi_uid,child.uid,src.uid,child.known_at_ms,h,
                         "TEST_PRICE_INTERSECTION_ONLY_FIRSTNESS_UNPROVEN")

def link_vc_after_test(ledger: EventLedger, zone:ZoneReference,
                       test_link:GeometricLink, witness:BarWitness,
                       as_of_ms:int) -> GeometricLink:
    """Trace a lower-TF VC's causal parent to price-evidenced TEST.

    A VC may form AWAY from the parent zone. Never require its own candle to
    intersect the zone; that would invent a course rule.
    """
    parent,events,active=_zone_parent(ledger,zone,as_of_ms)
    child=events.get(witness.child_uid)
    src=events.get(witness.source_uid)
    if child is None or src is None or child.uid not in active or src.uid not in active:
        raise PriceLineageRejected("VC_OR_SOURCE_NOT_ACTIVE_AS_OF")
    if child.kind!="VC":
        raise PriceLineageRejected("NOT_VC_KIND")
    if not isinstance(test_link,GeometricLink) or test_link.poi_uid!=zone.poi_uid or (
        test_link.readiness!="NOT_TRADE_READY" or
        test_link.relation!="TEST_PRICE_INTERSECTION_ONLY_FIRSTNESS_UNPROVEN"):
        raise PriceLineageRejected("UNVERIFIED_TEST_LINK")
    test=events.get(test_link.child_uid)
    if test is None or test.uid not in active or test.kind!="TEST" or (
        test.uid not in child.parent_uids or parent.uid not in test.parent_uids):
        raise PriceLineageRejected("VC_NOT_CAUSALLY_LINKED_TO_TEST")
    if child.known_at_ms < test.known_at_ms or witness.bar.start<test.known_at_ms:
        raise PriceLineageRejected("VC_BEFORE_TEST")
    hash_now=_checked_observation(parent,child,src,witness,as_of_ms)
    # Do not accept a copied/fabricated test-link digest without checking
    # its original TEST's known time, source identity and current binding.
    if test.known_at_ms!=test_link.known_at_ms or test_link.source_uid not in events or (
        events[test_link.source_uid].uid not in test.evidence_uids or
        test_link.bar_sha256 not in events[test_link.source_uid].evidence_uids):
        raise PriceLineageRejected("STALE_OR_UNBOUND_TEST_LINK")
    return GeometricLink(zone.poi_uid,child.uid,src.uid,child.known_at_ms,
                         hash_now,"VC_CAUSALLY_AFTER_PRICE_TOUCH_SEMANTICS_UNKNOWN")
