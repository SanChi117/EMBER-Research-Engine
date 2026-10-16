#!/usr/bin/env python3
"""B1/C09: independent one-day Binance BTC 5m original -> 1h raid -> 5m BOS.

No claims about true author-approved patterns or other unscanned days.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from f03_5m_original_source import download_source_5m
from c09_source_5m_raid_bos_geometry import inspect_source_raid_bos_5m
T=1790899200000
URL="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2026-10-02.zip"
RECEIPT=ROOT/"evidence"/"f03"/"F03_BTCUSDT_5M_2026-10-02_ORIGINAL_RECEIPT.json"

def main(outpath=None):
    verified=download_source_5m(URL)
    receipt=json.loads(RECEIPT.read_text(encoding="utf8"))
    assert receipt["original_zip_url"]==verified.archive_url
    assert receipt["original_zip_sha256"]==verified.zip_sha256
    assert receipt["original_raw_csv_sha256"]==verified.raw_csv_sha256
    assert verified.readiness=="NOT_TRADE_READY"
    before=inspect_source_raid_bos_5m(verified,T+8*3600000)
    whole=inspect_source_raid_bos_5m(verified,T+86400000)
    assert whole.five_minute_closed_count==288
    assert whole.hourly_closed_count==24
    assert before.hourly_closed_count==8
    assert whole.readiness=="NOT_TRADE_READY"
    assert whole.stronghl_status=="NO_INDEPENDENT_STRONG_HL_VC_CERTIFICATE"
    assert all(e.raid_1h_known_at_ms<e.bos_5m_known_at_ms and
               e.bos_5m_known_at_ms<=whole.as_of_ms for e in whole.bos_witnesses)
    report={
        "cycle":"B1_C09_REAL_BINANCE_PRICE_GEOMETRY_ONLY",
        "symbol":"BTCUSDT","market":"BINANCE_USDM_FUTURES",
        "date":"2026-10-02",
        "5m_sha_locked":verified.zip_sha256==receipt["original_zip_sha256"],
        "native_raw_5m_bars":len(verified.rows),
        "derived_closed_1h_bars":whole.hourly_closed_count,
        "v05_hourly_pivots":whole.hourly_pivot_candidates,
        "v05_1h_raid_candidates":whole.hourly_raid_candidates,
        "v05_5m_pivots":whole.five_minute_pivot_candidates,
        "v05_raid_linked_5m_bos_candidates":whole.five_minute_bos_candidates,
        "bos_source_row_ids":[x.original_5m_member_id for x in whole.bos_witnesses],
        "original_5m_source_sha":verified.zip_sha256,
        "earlier_prefix_asof_ms":before.as_of_ms,
        "earlier_prefix_hourly_closed":before.hourly_closed_count,
        "author_raid_freshness_24h_approved":False,
        "author_strong_hl_vc_approved":False,
        "author_poi_approved":False,
        "trade_signals_approved":0,
        "readiness":"NOT_TRADE_READY"
    }
    print(json.dumps(report,sort_keys=True,indent=2))
    if outpath:Path(outpath).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
