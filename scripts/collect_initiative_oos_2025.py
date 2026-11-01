"""Predeclared 2025 USD-M Futures independent-period Binance Vision downloader.

Binance Vision original monthly ZIP plus companion published .CHECKSUM.
FROZEN 12 symbols, 4h Jan-Aug and 1h Jun-Aug 2025; no substitutions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from scripts.run_mtf_v3_universe import inspect_tf_agreement, load_batched

SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LINKUSDT",
    "AVAXUSDT", "ADAUSDT", "OPUSDT", "ARBUSDT", "LDOUSDT", "NEARUSDT",
)
FOUR_MONTHS = tuple(f"2025-{i:02d}" for i in range(1, 9))
ONE_MONTHS = tuple(f"2025-{i:02d}" for i in range(6, 9))
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
FIELDS = (
    "symbol", "tf", "time_ms", "open", "high", "low", "close",
    "volume", "taker_buy_base", "quote_volume", "trades",
)


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EMBER-OOS-Research/1.0"})
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("failed")


def parse_source(raw: bytes, symbol: str, tf: str, month: str) -> list[dict]:
    step = 3_600_000 if tf == "1h" else 14_400_000
    rows = []
    for item in csv.reader(io.StringIO(raw.decode("utf-8-sig"))):
        if not item or item[0].lower().strip() in ("open_time", "open time"):
            continue
        if len(item) < 11:
            raise ValueError(f"missing source kline fields: {symbol} {tf} {month}")
        ts = int(item[0])
        dt = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m")
        if (
            not 1_000_000_000_000 <= ts < 10_000_000_000_000
            or ts % step or dt != month
        ):
            raise ValueError(f"wrong venue UTC clock or archive month {symbol} {tf} {ts}")
        op, high, low, close = map(float, item[1:5])
        vol, taker = float(item[5]), float(item[9])
        if not (
            low > 0 and high >= max(op, close) and low <= min(op, close)
            and vol >= 0 and 0 <= taker <= vol * (1 + 1e-7)
        ):
            raise ValueError(f"invalid source OHLCV or taker {symbol} {tf} {ts}")
        rows.append({
            "symbol": symbol, "tf": tf, "time_ms":str(ts),
            "open":item[1], "high":item[2], "low":item[3], "close":item[4],
            "volume":item[5], "taker_buy_base":item[9],
            "quote_volume":item[7], "trades":item[8],
        })
    if not rows:
        raise ValueError(f"empty USD-M futures month {symbol} {tf} {month}")
    return rows


def download(spec: tuple[str, str, str]) -> tuple[list[dict], dict]:
    symbol, tf, month = spec
    name = f"{symbol}-{tf}-{month}.zip"
    url = f"{BASE}/{symbol}/{tf}/{name}"
    archive = fetch(url)
    checksum = fetch(url + ".CHECKSUM").decode("utf-8-sig").strip().split()[0].lower()
    actual = hashlib.sha256(archive).hexdigest()
    if not re.fullmatch(r"[a-f0-9]{64}", checksum) or checksum != actual:
        raise ValueError(f"Binance published checksum mismatch {url}")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = [x for x in z.namelist() if x.endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"ambiguous original ZIP contents {url}")
        member = z.read(names[0])
    rows = parse_source(member, symbol, tf, month)
    return rows, {
        "url":url,"symbol":symbol,"tf":tf,"month":month,
        "zip_sha256":actual,"checksum_sha256":checksum,
        "raw_csv_sha256":hashlib.sha256(member).hexdigest(),"rows":len(rows),
    }


def run(out_dir: Path, workers: int = 10) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        (symbol, tf, month) for symbol in SYMBOLS
        for tf, months in (("4h", FOUR_MONTHS), ("1h", ONE_MONTHS))
        for month in months
    ]
    rows = []
    receipts = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = {pool.submit(download, spec):spec for spec in specs}
        for task in as_completed(tasks):
            data, receipt = task.result()
            rows.extend(data)
            receipts.append(receipt)
    rows.sort(key=lambda x:(x["symbol"],x["tf"],int(x["time_ms"])))
    target = out_dir / "binance_usdm_1h_4h_batch01.csv"
    with target.open("w",encoding="utf-8",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    sources, source_receipt = load_batched(out_dir)
    if set(sources) != set(SYMBOLS):
        raise ValueError("2025 symbol universe changed or missing")
    parity = {
        symbol:inspect_tf_agreement(x["1h"],x["4h"])
        for symbol,x in sources.items()
    }
    if any(v["compared_full_4h_bars"] < 250 or v["ohlcv_mismatches"]
           for v in parity.values()):
        raise ValueError("2025 USD-M 1H vs 4H mismatch or missing overlap")
    result = {
        "status":"2025_REAL_BINANCE_USDM_MONTHLY_SHA256_VERIFIED",
        "symbols":list(SYMBOLS),"months_4h":FOUR_MONTHS,"months_1h":ONE_MONTHS,
        "archives":len(receipts),
        "sources":sorted(receipts,key=lambda x:(x["symbol"],x["tf"],x["month"])),
        "converted_csv_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "converted_receipt":source_receipt,
        "tf_parity":parity,
    }
    (out_dir.parent/"2025_original_source_receipts.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",
    )
    print(json.dumps({
        "status":result["status"],"source_archives":len(receipts),
        "instruments":len(sources),"converted_rows":len(rows),
        "converted_sha256":result["converted_csv_sha256"],
    },sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=10)
    args = parser.parse_args()
    run(args.out_dir,args.workers)


if __name__ == "__main__":
    main()
