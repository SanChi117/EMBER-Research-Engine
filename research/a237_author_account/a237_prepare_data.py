"""A237: four genuine Binance USD-M original author pair datasets.
Wraps frozen A228 data prep; no synthetic candles/spot fallback and no edits
to pinned original strategy implementations.
"""
from __future__ import annotations
import json
from pathlib import Path
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as base

base.COINS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT")
orig_fetch = base.month_fetch


def four_pair_fetch(job, receipt_manifest):
    kind, symbol, year, month = job
    if kind != "funding" or symbol != "BNBUSDT":
        return orig_fetch(job, receipt_manifest)
    # BNB has no matching A217 pinned funding receipt. Pin the *new genuine*
    # futures monthly ZIP+CSV SHA in the generated input receipt instead.
    url = (f"https://data.binance.vision/data/futures/um/monthly/"
           f"fundingRate/{symbol}/{symbol}-fundingRate-{year}-{month:02}.zip")
    csvrows, receipt = base.csv_zip_content(url)
    cols = [x.strip().lower().replace("_", "") for x in csvrows[0]]
    t_idx, rate_idx = cols.index("calctime"), cols.index("lastfundingrate")
    rows = sorted((base.genuine.as_ms(row[t_idx]), float(row[rate_idx]))
                  for row in csvrows[1:] if row and row[t_idx].isdigit())
    import calendar
    minimum = calendar.monthrange(year, month)[1] * 3 - 3
    if len(rows) < minimum:
        raise ValueError(f"BNB_MISSING_GENUINE_MONTHLY_FUNDING {year}-{month:02} {len(rows)}<{minimum}")
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError("BNB_FUNDING_DUPLICATE_SETTLEMENT_TIMESTAMP")
    # Official funding timestamps occasionally differ by +1ms around the 8h boundary.\n    # Only allow a 1-second tolerance, never conceal a missing 8h settlement.\n    gaps = [(a[0], b[0], (b[0]-a[0])/3600_000)
            for a, b in zip(rows, rows[1:]) if not (0 < b[0]-a[0] <= 8*3600_000 + 1000)]
    if gaps:
        raise ValueError(f"BNB_FUNDING_MISSING_SETTLEMENT_GAP month={year}-{month:02} n={len(rows)} bad_first={gaps[:5]} max_gap_h={max(g[-1] for g in gaps):.3f}")
    receipt.update(type="funding", parsed_rows=len(rows),
                   source_tag="OFFICIAL_BINANCE_USDM_BNB_NEW_SHA",
                   author_account_cycle="A237")
    return job, rows, receipt


def main():
    base.month_fetch = four_pair_fetch
    base.main()
    manifest_path = base.OUT / "A228_ORIGINAL_AND_MARKET_RECEIPTS.json"
    receipt = json.loads(manifest_path.read_text("utf8"))
    actual = set(receipt["dataframe_rows"])
    for tf in ("5m", "15m", "1h", "4h"):
        if f"BNBUSDT_{tf}" not in actual:
            raise ValueError(f"BNB_4PAIR_MISSING_{tf}")
    n = sum(x["type"] == "funding" and "BNBUSDT" in x["url"]
            for x in receipt["archive_receipts"])
    if n != 31:
        raise ValueError(f"A237_BNB_MONTHLY_FUNDING_N_{n}_EXPECTED_31")
    print("A237_FOUR_PAIR_GENUINE_DATA_READY", n, "bnb funding monthly ZIP source receipts", flush=True)


if __name__ == "__main__":
    main()
