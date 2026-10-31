"""A223: COUNT original 4H regime-close anticipation on real Binance BTC USD-M bars.

Uses pinned AST bodies of the author's regime and first-entry code and its
Wilder RSI. This is a source causality audit (not a PnL/backtest).
No synthetic prices and no live/private trading.
"""
import ast
import hashlib
import json
import sys
from bisect import bisect_left, bisect_right
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as binance  # noqa: E402
import a223_original_d1_regime_open_time_audit as original  # noqa: E402

FEATURES = "src/data/strategy_c_v2_features.py"
FEATURES_SHA = "92e06ce2bf7f59a6f853c81ce176e153693e1776"


def original_feature_rsi():
    url = f"https://raw.githubusercontent.com/{original.REPO}/{original.COMMIT}/{FEATURES}"
    raw = binance.fetch(url)
    if binance.blob_sha(raw) != FEATURES_SHA:
        raise ValueError("Author RSI source Git blob SHA drift")
    tree = ast.parse(raw.decode("utf-8"))
    wanted = {"rsi_series", "_rsi_series", "_rsi_from_avgs"}
    nodes = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in wanted]
    if {x.name for x in nodes} != wanted:
        raise ValueError("Cannot extract full original Wilder RSI")
    ast_mod = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)] + nodes,
        type_ignores=[],
    )
    ast.fix_missing_locations(ast_mod)
    scope = {}
    exec(compile(ast_mod, "<ORIGINAL Wilder RSI>", "exec"), scope)
    return scope["rsi_series"], hashlib.sha256(raw).hexdigest()


def archive_hourly_btc():
    manifest = json.loads((ROOT / "research/a217_trendrider_original/evidence/source_manifest.json").read_text())
    jobs = [("BTCUSDT", "1h", y, m) for y, m in binance.month_iter()]
    rows, receipts = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for task in as_completed([pool.submit(binance.load_one, job, manifest) for job in jobs]):
            job, clean, receipt = task.result()
            rows.extend(clean)
            receipts.append(receipt)
    rows.sort()
    timestamps = [r[0] for r in rows]
    if len(timestamps) != len(set(timestamps)) or any(b-a != 3600000 for a,b in zip(timestamps,timestamps[1:])):
        raise ValueError("Missing or duplicate genuine 1h Binance BTC bar")
    dates = pd.to_datetime(timestamps, unit="ms", utc=True)
    if dates[0] != pd.Timestamp("2023-11-01", tz="UTC") or dates[-1] != pd.Timestamp("2026-09-30T23:00:00Z"):
        raise ValueError("Unexpected authenticated Binance window")
    df = pd.DataFrame([r[1:] for r in rows],
        columns=["open","high","low","close","volume"], index=dates)
    return df, receipts


def check():
    data = binance.fetch(f"https://raw.githubusercontent.com/{original.REPO}/{original.COMMIT}/{original.ORIGINAL}")
    if binance.blob_sha(data) != original.SHA:
        raise ValueError("Pinned original entry code changed")
    rsi, rsi_sha = original_feature_rsi()
    env={"rsi_series":rsi, "timedelta":timedelta, "bisect_left":bisect_left,"bisect_right":bisect_right}
    find_zones=original.extract_original_function(data.decode(),"_identify_regime_zones",env)
    generate_entries=original.extract_original_function(data.decode(),"_generate_signals_in_zone",env)
    df,receipts=archive_hourly_btc()
    daily_4h=df.resample("4h", label="left", closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"
    })
    count_4h=df["close"].resample("4h").count()
    if (count_4h != 4).any() or daily_4h.isna().any().any():
        raise ValueError("Non-aligned genuine 4h UTC resample")
    bars_4h=[SimpleNamespace(timestamp=ts.to_pydatetime()) for ts in daily_4h.index]
    feats_4h=[SimpleNamespace(close=float(v)) for v in daily_4h["close"]]
    zones=find_zones(bars_4h,feats_4h)
    bars_1h=[SimpleNamespace(timestamp=ts.to_pydatetime(),
                              open=float(row.open),high=float(row.high),
                              low=float(row.low),close=float(row.close))
             for ts,row in df.iterrows()]
    cfg=SimpleNamespace(
        hold_exec_bars=24, max_entries_per_zone=6, cooldown_bars=0,
        entry_type="hybrid", pullback_pct=0.0075, breakout_pct=0.0025
    )
    results={}
    for year in ("2024","2025","2026"):
        results[year]={"regime_zone_starts":0,"base_signals":0,
                       "base_signals_before_4h_confirmation":0,
                       "other_signals":0, "sample":[]}
    for t0,t1,_,_ in zones:
        y=str(t0.year)
        if y not in results:
            continue
        if t0 < pd.Timestamp("2024-01-01T00:00:00Z").to_pydatetime() or t0 >= pd.Timestamp("2026-10-01T00:00:00Z").to_pydatetime():
            continue
        results[y]["regime_zone_starts"]+=1
        entries=generate_entries(bars_1h,t0,t1,cfg)
        for i,kind in entries:
            if kind == "base":
                results[y]["base_signals"]+=1
                # Original backtester consumes signal at 1H close and fills
                # at the following hourly bar's open.
                fill=bars_1h[i].timestamp+timedelta(hours=1)
                four_h_close=t0+timedelta(hours=4)
                if fill < four_h_close:
                    results[y]["base_signals_before_4h_confirmation"]+=1
                    if len(results[y]["sample"]) < 3:
                        results[y]["sample"].append({
                            "rsi_bar_open_utc":t0.isoformat(),
                            "original_1h_fill_utc":fill.isoformat(),
                            "rsi_4h_available_utc":four_h_close.isoformat(),
                            "anticipation_hours":(four_h_close-fill).total_seconds()/3600
                        })
            else:
                results[y]["other_signals"]+=1
    total=sum(x["base_signals_before_4h_confirmation"] for x in results.values())
    if total == 0:
        raise AssertionError("Unexpected: no original premature source entries across real BTC bars")
    record={
        "cycle":"A223",
        "verdict":"ORIGINAL_RESEARCH_REGIME_TIMESTAMP_LEAKAGE_ON_GENUINE_FUTURES",
        "pinned_original_commit":original.COMMIT,
        "original_exe_source_git_blob":original.SHA,
        "original_wilder_rsi_sha":FEATURES_SHA,
        "original_wilder_rsi_sha256":rsi_sha,
        "market":"BINANCE_USD_M_FUTURES_BTCUSDT_1H_AUTHENTIC",
        "genuine_monthly_archives_SHA_verified":len(receipts),
        "hourly_bars":len(df),"reconstituted_4h_bars":len(daily_4h),
        "original_code_executed_without_change":["_identify_regime_zones","_generate_signals_in_zone","rsi_series","_rsi_series","_rsi_from_avgs"],
        "regime_base_signal_timing":results,
        "all_years_earliest_entry_count":total,
        "author_reported_pnl_invalidated_as_independent_proof":True,
        "actual_pnl_measured":False,
        "live_engine_proven_same_bug":False,
        "author_reported_full_trade_set_reproduced":False,
        "no_orders":True,
        "source_note":"Original 4h RSI(20) uses bar's closing price. Source zone starts at that bar's OPEN and first 1h base entry may fill before 4h close. We count only the identifiable first base entry, not complete author portfolio PnL. Do not retune.",
    }
    out=HERE/"evidence/A223_D1_REAL_BTC_ORIGINAL_PREMATURE_GATE.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n","utf8")
    print(json.dumps({"market":record["market"],"verified_zip":len(receipts),
                      "early_base_entries":total,"years":{k:{x:v for x,v in d.items() if x!="sample"} for k,d in results.items()}},ensure_ascii=False),flush=True)


if __name__=="__main__":
    check()
