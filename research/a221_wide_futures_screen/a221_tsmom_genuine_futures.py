"""A221: real Binance UM replication of PINNED ORIGINAL TSMOM signals, with real funding.

No orders. Independent conservative next-open executable audit, NOT author's
native reported equity. Genuine source receipts rechecked against A217 SHA.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "efa37deac60fb9d91abcb181440c94f2f0eac4b8"
SOURCE_BLOB = "af7d999ff114a872df6bfe65fb5376577451021b"
SETTINGS_BLOB = "579df537946b20ce2c8ca55d4a8ab47629b769ba"
COINS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
BAR_HOURS = 1
START = (2023, 11)
END = (2026, 10)  # excl 2026 October, unposted monthly archive
BASE_BPS = 10.5
STRESS_BPS = 22.5


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def fetch(url: str) -> bytes:
    if not url.startswith(("https://data.binance.vision/", "https://raw.githubusercontent.com/")):
        raise ValueError("Unapproved source")
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EMBER-A221-Causal-Futures-Research"})
            with urllib.request.urlopen(req, timeout=50) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Official upstream unavailable {url}: {last}")


def month_iter():
    y, m = START
    while (y, m) < END:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def as_ms(v: str) -> int:
    x = int(v)
    if x >= 10**15:
        x //= 1000
    if not 1_690_000_000_000 < x < 1_800_000_000_000:
        raise ValueError(f"Unexpected funding/price epoch {v}")
    return x


def load_one(job: tuple[str, str, int, int], manifest: dict):
    sym, kind, y, m = job
    if kind == "1h":
        url = f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1h/{sym}-1h-{y}-{m:02}.zip"
    else:
        url = f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02}.zip"
    key = f"{sym}/{kind}/{y}/{m}"
    expected = manifest["source_receipts"].get(key)
    if not expected or expected["url"] != url:
        raise ValueError(f"Missing genuine A217 SHA receipt {key}")
    data = fetch(url)
    zip_sha = hashlib.sha256(data).hexdigest()
    if zip_sha != expected["zip_sha256"]:
        raise ValueError(f"Official Binance ZIP changed SHA {key}")
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        members = [n for n in bundle.namelist() if n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Bad archive CSV member count {key}")
        raw = bundle.read(members[0])
    csv_sha = hashlib.sha256(raw).hexdigest()
    if csv_sha != expected["csv_sha256"]:
        raise ValueError(f"Official Binance CSV changed SHA {key}")
    rows = list(csv.reader(io.StringIO(raw.decode("utf8"))))
    if len(rows) != expected["raw_csv_lines"]:
        raise ValueError(f"Official CSV number of lines drift {key}")
    clean = []
    if kind == "funding":
        header = [s.strip().lower().replace("_", "") for s in rows[0]]
        it, ir = header.index("calctime"), header.index("lastfundingrate")
        for row in rows[1:]:
            if not row:
                continue
            ts, rate = as_ms(row[it]), float(row[ir])
            if ts % 3_600_000 > 1000 or not np.isfinite(rate):
                raise ValueError(f"Bad settlement {key}")
            clean.append((ts // 3_600_000 * 3_600_000, rate))
    else:
        for row in rows:
            if not row or not row[0].isdigit():
                continue
            ts = as_ms(row[0])
            o, h, l, c, v = map(float, row[1:6])
            if not (0 < l <= min(o, c) <= max(o, c) <= h and v >= 0):
                raise ValueError(f"Bad USD-M OHLC {key}")
            clean.append((ts, o, h, l, c, v))
    if not clean:
        raise ValueError(f"No genuine market rows {key}")
    return job, clean, {"key": key, "zip_sha256": zip_sha, "csv_sha256": csv_sha, "n": len(clean)}


def load_all(manifest):
    jobs = []
    for y, m in month_iter():
        for sym in COINS:
            jobs.append((sym, "1h", y, m))
            if (y, m) >= (2024, 1):
                jobs.append((sym, "funding", y, m))
    rows = {(sym, kind): [] for sym in COINS for kind in ("1h", "funding")}
    receipts = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(load_one, j, manifest) for j in jobs]
        for i, future in enumerate(as_completed(futures)):
            job, parsed, receipt = future.result()
            rows[(job[0], job[1])].extend(parsed)
            receipts.append(receipt)
            if (i + 1) % 40 == 0:
                print(f"SHA-ATTESTED {i+1}/{len(jobs)} real Binance USD-M month ZIP", flush=True)
    candles = {}
    funding = {}
    for sym in COINS:
        bars = sorted(rows[(sym, "1h")])
        times = [b[0] for b in bars]
        if len(times) != len(set(times)) or any(b-a != 3_600_000 for a, b in zip(times, times[1:])):
            raise ValueError(f"Continuity or duplicate failure: {sym}")
        start = pd.Timestamp("2023-11-01T00:00:00Z")
        end = pd.Timestamp("2026-09-30T23:00:00Z")
        ts = pd.to_datetime(times, utc=True, unit="ms")
        if ts[0] != start or ts[-1] != end:
            raise ValueError(f"Unexpected Binance USD-M window {sym}: {ts[0]} {ts[-1]}")
        candles[sym] = pd.DataFrame([b[1:] for b in bars], columns=["open", "high", "low", "close", "volume"], index=ts)
        frows = sorted(rows[(sym, "funding")])
        ftimes = [a for a, _ in frows]
        if len(ftimes) != len(set(ftimes)):
            raise ValueError(f"Duplicate funding settlement {sym}")
        funding[sym] = pd.Series([b for _, b in frows], index=pd.to_datetime(ftimes, utc=True, unit="ms"), dtype="float64")
    base_index = candles[COINS[0]].index
    if not all(candles[sym].index.equals(base_index) for sym in COINS):
        raise ValueError("Futures assets have nonparallel UTC bar grid")
    return candles, funding, receipts


def compute(params, source, candles, funding):
    windows = [
        ("2024", pd.Timestamp("2024-01-01T00:00:00Z"), pd.Timestamp("2025-01-01T00:00:00Z")),
        ("2025", pd.Timestamp("2025-01-01T00:00:00Z"), pd.Timestamp("2026-01-01T00:00:00Z")),
        ("2026-Jan-Sep", pd.Timestamp("2026-01-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z")),
    ]
    details = {}
    sigs = {}
    prefix_probes = []
    for sym in COINS:
        df = candles[sym]
        signal = source.tsmom_signals(df, params)
        # Adversarial prefix stability: a later candle may never change an earlier decision.
        for cut in ("2024-04-01T00:00:00Z", "2024-12-01T00:00:00Z",
                    "2025-04-01T00:00:00Z", "2025-12-01T00:00:00Z",
                    "2026-04-01T00:00:00Z", "2026-09-01T00:00:00Z"):
            at = pd.Timestamp(cut)
            prefix = source.tsmom_signals(df.loc[:at], params)
            got = float(prefix.loc[at, "position"])
            expected = float(signal.loc[at, "position"])
            if not np.isclose(got, expected, rtol=0, atol=1e-12):
                raise ValueError(f"TSMOM source future-prefix leakage {sym} {cut}: {got}!={expected}")
            prefix_probes.append({"symbol": sym, "asof": cut, "passed": True})
        pos = signal["position"].shift(1).fillna(0.0)
        if pos.abs().max() > 1.000000001:
            raise ValueError("1x future exposure cap violated")
        if not (pos.iloc[:700] == 0.0).all():
            raise ValueError("Source 30d startup signal unverified")
        sigs[sym] = pos
    for label, start, end in windows:
        t = candles[COINS[0]].index
        active = (t >= start) & (t < end)
        per = {}
        for sym in COINS:
            df = candles[sym]
            original = sigs[sym]
            positions = original.loc[active].copy()
            opens = df["open"].loc[active]
            # Stop at the last hourly open inside each period; no future-price leakage.
            fwd = opens.shift(-1) / opens - 1.0
            positions.iloc[-1] = 0.0  # force flat at last observable open, closing fee
            turnover = positions.diff().abs()
            turnover.iloc[0] = abs(positions.iloc[0])  # independent annual cash restart
            if fwd.iloc[:-1].isna().any():
                raise ValueError("Source future open incomplete")
            fwd.iloc[-1] = 0.0
            gross = (positions * fwd).fillna(0.0)
            ft = funding[sym]
            carry = pd.Series(0.0, index=positions.index)
            settled = ft.loc[(ft.index >= start) & (ft.index < end)]
            if len(settled) < 450:  # ~3 payments/day for 2024/25, lower for short 2026
                raise ValueError(f"Missing real funding settlements {sym} {label}")
            # Settlement at hour t belongs to position held into t, before current t-open fills.
            held_prior = original.shift(1).reindex(settled.index).fillna(0.0)
            # Annual portfolio restarted flat: no overnight carry from previous year.
            held_prior.loc[held_prior.index == start] = 0.0
            carry.loc[settled.index] = -(held_prior * settled).to_numpy()
            per[sym] = {
                "gross": gross / 3.0, "base": (gross - turnover * BASE_BPS / 10000 + carry) / 3.0,
                "stress": (gross - turnover * STRESS_BPS / 10000 + carry) / 3.0,
                "fund": carry / 3.0,
                "cost_bps_base": float(turnover.sum() * BASE_BPS / 3.0),
                "cost_bps_stress": float(turnover.sum() * STRESS_BPS / 3.0),
                "settlements": len(settled),
                "turnover": float(turnover.sum()),
                "held_hours": int((positions.abs() > 0).sum()),
                "flips": int((np.sign(positions).diff().fillna(0) != 0).sum()),
            }
        frame = {k: sum(per[sym][k] for sym in COINS) for k in ("gross", "base", "stress", "fund")}
        view = {}
        for k, ret in frame.items():
            eq = (1 + ret).cumprod()
            peak = pd.concat([pd.Series([1.0]), eq.reset_index(drop=True)]).cummax().iloc[1:].to_numpy()
            dd = float((eq.to_numpy() / peak - 1).min())
            view[k] = {
                "net_return_pct": round(100 * float(eq.iloc[-1] - 1), 5),
                "marked_open_to_open_max_dd_pct": round(dd * 100, 5),
                "sharpe_ann_hourly": round(float(ret.mean() / ret.std(ddof=0) * np.sqrt(365 * 24)), 5) if ret.std(ddof=0)>0 else None,
            }
        details[label] = {
            "hours": int(active.sum()),
            "account_model": "single $3000 account, 3 equal-capital sleeves, no leverage",
            "scenarios": view,
            "actual_signed_funding_return_pct_simple_sum": round(100 * float(frame["fund"].sum()), 6),
            "asset_logs": {sym: {k: v for k, v in per[sym].items() if not isinstance(v, pd.Series)} for sym in COINS},
        }
        if not all(np.isfinite(view[k]["net_return_pct"]) for k in view):
            raise ValueError("Nonfinite economic result")
    return details, prefix_probes


def main():
    mandate = json.loads((ROOT / "config/research_mandate.lock.json").read_text("utf8"))
    assert mandate["state"] == "LOCKED_USER_ONLY" and mandate["scope"] == "BINANCE_USDT_M_FUTURES"
    manifest = json.loads((ROOT / "research/a217_trendrider_original/evidence/source_manifest.json").read_text("utf8"))
    print("A221: fetching original and genuine SHA-receipted Binance Futures", flush=True)
    with tempfile.TemporaryDirectory() as td:
        sourcepath = Path(td) / "tsmom.py"
        url = f"https://raw.githubusercontent.com/yongzhe2160cs/trading-engine/{SOURCE_COMMIT}/strategy/tsmom.py"
        raw = fetch(url)
        if blob_sha(raw) != SOURCE_BLOB:
            raise ValueError("Original TSMOM Git blob changed")
        sourcepath.write_bytes(raw)
        cfg = fetch(f"https://raw.githubusercontent.com/yongzhe2160cs/trading-engine/{SOURCE_COMMIT}/config/settings.py")
        if blob_sha(cfg) != SETTINGS_BLOB:
            raise ValueError("Original author deploy settings changed")
        spec = importlib.util.spec_from_file_location("a221_original_tsmom", sourcepath)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        params = mod.TsmomParams(lookback=720, vol_window=336, target_vol=0.2, max_leverage=1.0, rebalance=24)
        candles, funding, receipts = load_all(manifest)
        results, prefix_probes = compute(params, mod, candles, funding)
    output = {
        "cycle": "A221",
        "market": "genuine Binance USD-M Futures, BTCUSDT ETHUSDT SOLUSDT",
        "source_commit": SOURCE_COMMIT,
        "original_blob_sha": SOURCE_BLOB,
        "original_params": {"lookback":720,"vol_window":336,"target_vol":0.2,"max_leverage":1.0,"rebalance":24},
        "all_price_and_funding_zip_sha_match_a217": True,
        "source_zip_receipts": sorted(receipts, key=lambda x:x["key"]),
        "not_original_portfolio_accounting": True,
        "independent_after_cost_open_fill_audit": True,
        "not_untouched_oos": True,
        "real_exchange_fills_proved": False,
        "liquidation_and_intrabar_mark_audited": False,
        "verified_futures_candidate": False,
        "periods": results,
        "prefix_causality_probes": prefix_probes,
        "no_orders": True,
    }
    path = HERE / "evidence" / "A221_TSMOM_REAL_BINANCE_REPLAY.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"receipt_count":len(receipts),"prefix_causality_probes":len(prefix_probes),"periods":results},ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
