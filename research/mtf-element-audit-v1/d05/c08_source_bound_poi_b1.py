"""B1/C04: bind B1/C03 observed 15m/1d Bar to C08 independently-audited
Binance USD-M Futures ZIP and immutable source-receipt bundle.

No actual trades/POI/VC are academically classified by this module.
Unit tests can supply synthetic receipt directories; ONLY the repository's
Git-pinned C08 evidence and remote TLS+CHECKSUM justify a C08-origin claim.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
from typing import Optional

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from strict_vision_d04 import parse_url, verify_raw_zip, D04Rejected
from poi_price_lineage_b1 import (
    BarWitness, ZoneReference, GeometricLink,
    link_test_contact, link_vc_after_test,
)
from course_primitives_v05 import Bar
from strict_event_lineage_d03 import EventLedger

RECEIPTS_ROOT=ROOT/"evidence"/"c08"
C08_OK="HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED"
EXPECTED_SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")
SOURCE_STATUS="C08_ARCHIVE_AND_RECORDED_RAW_ROW_MATCH_TECHNICAL_ONLY"
NO_SIGNALS="NOT_TRADE_READY"

class C08WitnessRejected(ValueError):
    def __init__(self, code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ArchivedBarProof:
    witness: BarWitness
    zip_url: str
    zip_sha256: str
    raw_csv_sha256: str
    bar_time: int
    status: str=SOURCE_STATUS
    readiness: str=NO_SIGNALS

@dataclass(frozen=True)
class C08EventLink:
    event: GeometricLink
    bar_proof: ArchivedBarProof
    status: str=SOURCE_STATUS
    readiness: str=NO_SIGNALS

def _locked_receipt(symbol,tf,start,root):
    if symbol not in EXPECTED_SYMBOLS or tf not in ("15m","1d"):
        raise C08WitnessRejected("SYMBOL_OR_TF_NOT_IN_C08")
    if type(start) is not int or start<0:
        raise C08WitnessRejected("INVALID_KLINE_TIMESTAMP")
    root=Path(root)
    try:
        agg=json.loads((root/"C08_315_AGGREGATE.json").read_text(encoding="utf8"))
        batch=json.loads((root/f"C08_{symbol}_63_RECEIPTS.json").read_text(encoding="utf8"))
    except (OSError,ValueError,TypeError) as e:
        raise C08WitnessRejected("MISSING_OR_INVALID_C08_PROOF") from e
    if (agg.get("result")!="FULL_315_ATTESTED" or agg.get("unique_sources")!=315
        or agg.get("verified_archives")!=315 or agg.get("manifest_expected")!=315
        or agg.get("sources_by_symbol",{}).get(symbol)!=63
        or agg.get("statuses",{}).get(C08_OK)!=315):
        raise C08WitnessRejected("INCOMPLETE_C08_GLOBAL_ACCEPTANCE")
    recs=batch.get("receipts")
    if (batch.get("data_market")!="BINANCE_USDM_FUTURES_ONLY"
        or batch.get("selected_sources")!=63 or batch.get("verified_source_archives")!=63
        or not isinstance(recs,list) or len(recs)!=63):
        raise C08WitnessRejected("INCOMPLETE_C08_SYMBOL_RECEIPTS")
    selected=[];unique=set()
    for r in recs:
        u=r.get("url")
        try:info=parse_url(u)
        except (D04Rejected,ValueError,TypeError) as e:raise C08WitnessRejected("UNSAFE_C08_RECEIPT_URL") from e
        if u in unique:raise C08WitnessRejected("DUPLICATE_C08_RECEIPT")
        unique.add(u)
        if (r.get("status")!=C08_OK or r.get("normalized_all_11_columns_matched") is not True
            or r.get("symbol")!=info["symbol"] or r.get("tf")!=info["tf"]
            or r.get("rows")!=info["expected_rows"]):
            raise C08WitnessRejected("UNVERIFIED_C08_RECEIPT")
        if info["symbol"]==symbol and info["tf"]==tf and info["start_ms"]<=start<info["end_ms"]:
            selected.append((r,info))
    if len(selected)!=1:
        raise C08WitnessRejected("C08_ARCHIVE_COVERAGE_NOT_UNIQUE")
    return selected[0]

def c08_attested_bar(witness:BarWitness, zip_blob:bytes, checksum_blob:bytes,
                     *,receipt_dir:Optional[Path]=None) -> ArchivedBarProof:
    """Verify receipt-pinned raw archive + full D04 96/1 daily rows + exact Bar OHLC.

    The immutable C08 Git-tracked receipt file must be trusted separately via
    workflow Git blob hash, since a replacement receipt could bless fake data.
    """
    if not isinstance(witness,BarWitness) or not isinstance(witness.bar,Bar):
        raise C08WitnessRejected("INVALID_BAR_WITNESS")
    if witness.market!="USDM_FUTURES" or witness.venue!="BINANCE":
        raise C08WitnessRejected("NOT_BINANCE_USDM_FUTURES")
    b=witness.bar
    receipt,meta=_locked_receipt(witness.symbol,b.tf,b.start,
                                 RECEIPTS_ROOT if receipt_dir is None else receipt_dir)
    try:
        verified=verify_raw_zip(receipt["url"],zip_blob,checksum_blob)
    except (D04Rejected,ValueError,TypeError) as e:
        raise C08WitnessRejected("RAW_ZIP_OR_CHECKSUM_REJECTED") from e
    if (verified["zip_sha256"]!=receipt["zip_sha256"]
        or verified["raw_csv_sha256"]!=receipt["raw_csv_sha256"]
        or verified["bars"]!=receipt["rows"]):
        raise C08WitnessRejected("SOURCE_ARCHIVE_DIFFERS_FROM_LOCKED_C08")
    csv_name=meta["filename"][:-4]+".csv"
    with zipfile.ZipFile(io.BytesIO(zip_blob)) as z:
        raw=z.read(csv_name)
    if hashlib.sha256(raw).hexdigest()!=receipt["raw_csv_sha256"]:
        raise C08WitnessRejected("RAW_CSV_HASH_MISMATCH")
    hits=[]
    for fields in csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline="")):
        if fields and fields[0].lower()=="open_time":
            continue
        if len(fields)!=12:
            raise C08WitnessRejected("UNEXPECTED_RAW_KLINE_FIELDS")
        try:tm=int(fields[0])
        except ValueError as e:raise C08WitnessRejected("INVALID_RAW_OPEN_TIME") from e
        if tm==b.start:
            hits.append(fields)
    if len(hits)!=1:
        raise C08WitnessRejected("BAR_NOT_UNIQUELY_IN_RAW_C08_SOURCE")
    item=hits[0]
    if int(item[6])!=b.end-1:
        raise C08WitnessRejected("RAW_BAR_END_DIFFERENT")
    try:
        raw_prices=tuple(Decimal(item[i]) for i in (1,2,3,4))
        claimed=tuple(Decimal(str(value)) for value in (b.o,b.h,b.l,b.c))
    except (InvalidOperation,ValueError) as e:
        raise C08WitnessRejected("NONNUMERIC_BAR_OHLC") from e
    if claimed!=raw_prices:
        raise C08WitnessRejected("OBSERVED_OHLC_DIFFERS_FROM_RAW_C08")
    return ArchivedBarProof(witness,receipt["url"],verified["zip_sha256"],
                            verified["raw_csv_sha256"],b.start)

def link_c08_test(ledger:EventLedger,zone:ZoneReference,witness:BarWitness,
                  at:int,zip_blob:bytes,checksum_blob:bytes,*,receipt_dir=None):
    proof=c08_attested_bar(witness,zip_blob,checksum_blob,receipt_dir=receipt_dir)
    link=link_test_contact(ledger,zone,witness,at)
    return C08EventLink(link,proof)

def link_c08_vc(ledger:EventLedger,zone:ZoneReference,
                test_witness:BarWitness,vc_witness:BarWitness,at:int,
                test_zip:bytes,test_checksum:bytes,
                vc_zip:bytes,vc_checksum:bytes,*,receipt_dir=None):
    # Two independent C08 source checks. Never infer VC semantics from contact.
    c08_attested_bar(test_witness,test_zip,test_checksum,receipt_dir=receipt_dir)
    proof=c08_attested_bar(vc_witness,vc_zip,vc_checksum,receipt_dir=receipt_dir)
    link=link_vc_after_test(ledger,zone,test_witness,vc_witness,at)
    return C08EventLink(link,proof)
