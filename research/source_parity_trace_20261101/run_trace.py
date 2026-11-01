"""Read-only original-Python signal trace. NO simulation, PnL, optimization, or orders.
CSV: frozen Binance USD-M /fapi/v1/klines closed candles, acquired 2026-11-01 UTC.
Source commits and blob receipts are checked before importing original classes.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CSV = HERE / "binance_usdtm_closed_20261101.csv"
SOURCES = {
    "P01": ("OctopusTakopi/crypto-trend-following", "804eb428705c913988371c28a57ca051bb3a7f9c", "engine.py", "99885dd8f3995b53dbd1a53e725e13fe99be9a29"),
    "P04": ("yongzhe2160cs/trading-engine", "efa37deac60fb9d91abcb181440c94f2f0eac4b8", "strategy/tsmom.py", "af7d999ff114a872df6bfe65fb5376577451021b"),
    "P05": ("adokav/signal-bot", "c859e5a2eebfd2f2f817bc2006f7f97a6f8d1ae7", "trading/strategies/tsmom.py", "1448abe29f47ef343ec72f779be4abb675c7714e"),
    "P06": ("hrodrig/freqhub-strategies", "210952246ae457a5f6d5e089ddea8b4960a71775", "strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py", "6e80c0b96754c21744726120b6904f940621ec01"),
    "P07": ("analogdada/perplab", "68251be7e1b4c0ade110bd4e097d524c6ce2acbc", "src/perplab/strategy/library/pullback_retest.py", "4b04c1834bbf0a3e69d9e67542aea204718550c8"),
    "P10": ("rgg81/crypto-trade", "65cf4284e7a397673d1ac8c982f0d113027ed27b", "src/crypto_trade/strategies/indicator/bb_squeeze.py", "7568c60cbef2157065d2d1b8944ca5a4c965f39b"),
}

EXPECTED_P07 = """SOLUSDT 2026-09-01T12:59Z -1
SOLUSDT 2026-09-01T18:59Z -1
BTCUSDT 2026-09-01T21:59Z -1
ETHUSDT 2026-09-01T22:59Z -1
ETHUSDT 2026-09-02T11:59Z -1
BTCUSDT 2026-09-03T04:59Z 1
SOLUSDT 2026-09-03T04:59Z 1
ETHUSDT 2026-09-03T14:59Z 1
SOLUSDT 2026-09-03T14:59Z 1
ETHUSDT 2026-09-03T17:59Z 1
SOLUSDT 2026-09-03T17:59Z 1
BTCUSDT 2026-09-03T21:59Z 1
SOLUSDT 2026-09-05T14:59Z 1
BTCUSDT 2026-09-05T18:59Z 1
SOLUSDT 2026-09-05T21:59Z 1
ETHUSDT 2026-09-06T03:59Z 1
SOLUSDT 2026-09-06T08:59Z 1
SOLUSDT 2026-09-07T09:59Z -1
SOLUSDT 2026-09-07T22:59Z -1
BTCUSDT 2026-09-08T07:59Z -1""".splitlines()

EXPECTED_P10 = """SOLUSDT 2026-09-01T08:59Z -1
BTCUSDT 2026-09-03T13:59Z 1
ETHUSDT 2026-09-03T13:59Z 1
BTCUSDT 2026-09-04T12:59Z -1
ETHUSDT 2026-09-04T12:59Z -1
BTCUSDT 2026-09-08T13:59Z -1
SOLUSDT 2026-09-08T13:59Z -1
ETHUSDT 2026-09-09T08:59Z 1
ETHUSDT 2026-09-10T12:59Z -1
BTCUSDT 2026-09-10T13:59Z -1
ETHUSDT 2026-09-11T12:59Z 1
SOLUSDT 2026-09-11T12:59Z 1
BTCUSDT 2026-09-11T13:59Z 1
SOLUSDT 2026-09-13T08:59Z -1
BTCUSDT 2026-09-14T13:59Z 1
ETHUSDT 2026-09-20T02:59Z -1
SOLUSDT 2026-09-20T02:59Z -1
BTCUSDT 2026-09-21T08:59Z 1
BTCUSDT 2026-09-23T14:59Z -1
ETHUSDT 2026-09-25T12:59Z 1""".splitlines()


def fmt(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def import_source(name: str, filename: Path):
    spec = importlib.util.spec_from_file_location(name, filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def clone_and_check(root: Path, key: str) -> Path:
    repo, commit, source, blob_sha = SOURCES[key]
    destination = root / key
    subprocess.run(
        ["git", "-c", "http.version=HTTP/1.1", "clone", "-q", "--depth", "1",
         "--filter=blob:none", "https://github.com/" + repo + ".git", str(destination)],
        check=True, timeout=120,
    )
    if subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip() != commit:
        subprocess.run(["git", "-C", str(destination), "fetch", "-q", "--depth", "1",
                        "origin", commit], check=True, timeout=90)
        subprocess.run(["git", "-C", str(destination), "checkout", "-q", commit], check=True, timeout=30)
    actual_commit = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    if actual_commit != commit:
        raise RuntimeError(key + " commit drift: " + actual_commit)
    content = (destination / source).read_bytes()
    actual_blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
    if actual_blob != blob_sha:
        raise RuntimeError(key + " source blob changed: " + actual_blob)
    return destination


def prepare(df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
    sub = df.loc[(df.symbol == symbol) & (df.interval == interval)].copy()
    sub.sort_values("open_time", inplace=True)
    sub.reset_index(drop=True, inplace=True)
    assert sub.close_time.is_monotonic_increasing
    assert ((sub.high >= sub[["open", "close"]].max(axis=1)) & (sub.low <= sub[["open", "close"]].min(axis=1))).all()
    return sub


def collect(series: pd.Series, sub: pd.DataFrame, symbol: str) -> list[str]:
    return [f"{symbol} {fmt(int(sub.close_time.iat[i]))} {int(val)}"
            for i, val in enumerate(series) if int(val) != 0]


def test_p07(repo: Path, df: pd.DataFrame) -> dict:
    sys.path.insert(0, str(repo / "src"))
    from perplab.strategy.library.pullback_retest import PullbackRetest

    rows = []
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        sub = prepare(df, sym, "1h")
        strategy = PullbackRetest()
        candles = strategy.indicators(sub.rename(columns=str.lower))
        signals = strategy.entry_signal_vectorized(candles)
        rows += collect(signals, sub, sym)
    rows.sort(key=lambda row: (row.split()[1], row.split()[0]))
    match = rows[:20] == EXPECTED_P07 and len(rows) == 134
    return {"n": len(rows), "first20_match_independent": match, "first20": rows[:20]}


def test_p10(repo: Path, df: pd.DataFrame) -> dict:
    sys.path.insert(0, str(repo / "src"))
    from crypto_trade.backtest_models import Signal

    # Original signal class unchanged. Isolate it from unrelated LightGBM registry imports.
    stub = types.ModuleType("crypto_trade.strategies")
    stub.__path__ = [str(repo / "src" / "crypto_trade" / "strategies")]
    stub.NO_SIGNAL = Signal(direction=0, weight=0)
    sys.modules["crypto_trade.strategies"] = stub
    from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy

    rows = []
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        sub = prepare(df, sym, "1h")
        inp = sub.rename(columns=str.lower).copy()
        inp["symbol"] = sym
        obj = BbSqueezeStrategy()
        obj.compute_features(inp)
        arr = [obj.get_signal(sym, int(t)).direction for t in sub.open_time]
        rows += collect(pd.Series(arr), sub, sym)
    rows.sort(key=lambda row: (row.split()[1], row.split()[0]))
    match = rows[:20] == EXPECTED_P10 and len(rows) == 54
    return {"n": len(rows), "first20_match_independent": match, "first20": rows[:20]}


def test_p04(repo: Path, df: pd.DataFrame) -> dict:
    original = import_source("original_p04_tsmom", repo / "strategy" / "tsmom.py")
    tree = ast.parse((repo / "config" / "settings.py").read_text())
    params = next(
        ast.literal_eval(a.value) for a in tree.body
        if isinstance(a, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "TSMOM_DEPLOY_PARAMS" for t in a.targets)
    )
    events = []
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        sub = prepare(df, sym, "1h")
        frame = pd.DataFrame({"close": sub.close.to_numpy()},
                             index=pd.to_datetime(sub.close_time, unit="ms", utc=True))
        result = original.tsmom_signals(frame, original.TsmomParams(**params))
        for i in range(len(result)):
            pos = float(result.position.iloc[i])
            if i >= params["lookback"] and i % params["rebalance"] == 0 and pos != 0.0:
                events.append({"sym": sym, "t": fmt(int(sub.close_time.iat[i])),
                               "position": round(pos, 5)})
    events.sort(key=lambda x: (x["t"], x["sym"]))
    return {"n_rebalance_states": len(events), "params": params, "first20": events[:20]}


def test_p05(repo: Path, df: pd.DataFrame) -> dict:
    sys.path.insert(0, str(repo))
    from trading.data.binance_perp import Candle
    original = import_source("original_p05_tsmom", repo / "trading" / "strategies" / "tsmom.py")
    out = []
    counts = {}
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        sub = prepare(df, sym, "1d")
        candles = [
            Candle(open_time=int(r.open_time)//1000, close_time=int(r.close_time)//1000,
                   available_at=int(r.close_time)//1000, open=float(r.open), high=float(r.high),
                   low=float(r.low), close=float(r.close), volume=float(r.volume),
                   quote_volume=float(r.quote_volume))
            for r in sub.itertuples(index=False)
        ]
        c = 0
        for i in range(60, len(candles)):
            decision = original.evaluate_tsmom(
                candles[:i+1], symbol=sym, decision_at=candles[i].close_time
            )
            if decision.signal is original.TsmomSignal.LONG:
                c += 1
                if len(out) < 20:
                    out.append({"sym": sym, "t": fmt(int(sub.close_time.iat[i])),
                                "scale": round(decision.position_scale, 4)})
        counts[sym] = c
    return {"long_daily_decisions_by_symbol": counts, "first20": out}


def test_p01(repo: Path, df: pd.DataFrame) -> dict:
    original = import_source("original_p01_engine", repo / "engine.py")
    daily = df[df.interval == "1d"].copy()
    daily["date"] = pd.to_datetime(daily.open_time, unit="ms", utc=True).dt.tz_localize(None)
    panel = {key: daily.pivot(index="date", columns="symbol", values=key)
             for key in ("open", "close", "quote_volume")}
    panel["hours"] = pd.DataFrame(24, index=panel["open"].index, columns=panel["open"].columns)
    # Source defaults; funding is NOT needed for the signal trace, no simulate() called.
    inputs = original.prepare_inputs(panel, original.Config())
    out = []
    for t in inputs.signal.index:
        for sym in inputs.signal.columns:
            val = inputs.signal.loc[t, sym]
            if pd.notna(val) and len(out) < 20:
                out.append({"symbol": sym, "date": t.strftime("%Y-%m-%d"),
                            "signal_z": round(float(val), 5)})
    return {"native_signal_trace": out, "end_default": original.Config().end,
            "note": "Signal only; portfolio allocation, funding, fills not tested"}


def test_p06(repo: Path, df: pd.DataFrame) -> dict:
    # Original class body executes unchanged. Freqtrade and TA-Lib dependency shims
    # are NOT full engine parity: result is only a conditional source-level trace.
    fake_ft = types.ModuleType("freqtrade")
    fake_s = types.ModuleType("freqtrade.strategy")
    fake_p = types.ModuleType("freqtrade.persistence")
    class Param:
        def __init__(self, *args, default=None, **kwargs):
            self.value = default
    class Trade:
        @staticmethod
        def get_trades_proxy(**kwargs):
            return []
    fake_s.IntParameter = Param
    fake_s.DecimalParameter = Param
    fake_s.BoolParameter = Param
    fake_s.CategoricalParameter = Param
    fake_s.IStrategy = type("IStrategy", (), {})
    fake_p.Trade = Trade
    sys.modules.update({"freqtrade": fake_ft, "freqtrade.strategy": fake_s,
                        "freqtrade.persistence": fake_p})
    ta = types.ModuleType("talib.abstract")
    def ema(frame, timeperiod):
        return frame["close"].ewm(span=timeperiod, adjust=False, min_periods=timeperiod).mean()
    def atr(frame, timeperiod):
        pc = frame["close"].shift(1)
        tr = pd.concat([frame["high"]-frame["low"],
                        (frame["high"]-pc).abs(), (frame["low"]-pc).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/timeperiod, adjust=False, min_periods=timeperiod).mean()
    ta.EMA = ema
    ta.ATR = atr
    m = types.ModuleType("talib")
    m.abstract = ta
    sys.modules["talib"] = m
    sys.modules["talib.abstract"] = ta
    source = import_source("original_p06_ftr", repo / SOURCES["P06"][2])
    strategy = source.FailureToReturnStrategy()
    rows = []
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        sub = prepare(df, sym, "1h")
        frame = sub.rename(columns=str.lower).copy()
        frame["date"] = pd.to_datetime(frame.open_time, unit="ms", utc=True)
        ind = strategy.populate_indicators(frame, {"pair": sym})
        decision = strategy.populate_entry_trend(ind, {"pair": sym})
        flags = decision["enter_long"].fillna(0).astype(int)
        rows += collect(flags, sub, sym)
    rows.sort(key=lambda row: (row.split()[1], row.split()[0]))
    return {"long_signals": len(rows), "first20": rows[:20],
            "status": "DEPENDENCY_SHIMS_NOT_FREQTRADE_PARITY",
            "note": "TA-lib EMA/ATR seeds differ from pandas shims; validate with full TA-lib"}


def main() -> None:
    df = pd.read_csv(CSV)
    assert set(df.interval) == {"1h", "1d"}
    assert set(df.symbol) == {"BTCUSDT", "ETHUSDT", "SOLUSDT"}
    assert df.close_time.max() < 1793494800000
    report = {"dataset_rows": len(df), "dataset_sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
              "source_commits": {}, "results": {}, "scope": "SOURCE SIGNAL TRACE ONLY; NO PNL"}
    with tempfile.TemporaryDirectory(prefix="ember_native_sources_") as td:
        roots = {}
        for key in SOURCES:
            roots[key] = clone_and_check(Path(td), key)
            report["source_commits"][key] = SOURCES[key][1]
        for key, func in (("P07", test_p07), ("P10", test_p10), ("P04", test_p04),
                          ("P05", test_p05), ("P01", test_p01), ("P06", test_p06)):
            try:
                report["results"][key] = func(roots[key], df)
            except Exception as exc:
                report["results"][key] = {"status": "BLOCKED_RUNTIME", "error": repr(exc)}
    out = HERE / "TRACE_RESULT_LOCAL.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("EMBER_PARITY_REPORT=" + json.dumps(report, ensure_ascii=False))
    if not all(report["results"][k].get("first20_match_independent", False) for k in ("P07", "P10")):
        raise AssertionError("P07/P10 exact first20 native-vs-independent comparison failed")


if __name__ == "__main__":
    main()
