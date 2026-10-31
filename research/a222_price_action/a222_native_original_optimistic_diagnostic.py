"""A222: optimistic NATIVE AUTHOR source backtest diagnostic on real USD-M BTC.

Explicitly INSUFFICIENT for futures profitability: author's same-close fill,
fixed $8 BTC cost, funding omitted, stop path simplified, margin absent.
Use only to reject obviously failing sources before full independent replay.
"""
import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/a222_price_action"))
import a222_original_sweep_bos_signal_preflight as pa  # noqa: E402

SOURCE = pa.binance_source


def run():
    manifest = json.loads(
        (ROOT / "research/a217_trendrider_original/evidence/source_manifest.json").read_text()
    )
    with tempfile.TemporaryDirectory(prefix="a222-original-native-") as td:
        tmp = Path(td)
        original_files = pa.fetch_original(tmp)
        sys.path.insert(0, td)
        config = importlib.import_module("config")
        strategy = importlib.import_module("src.strategy")
        simulator = importlib.import_module("src.backtester")
        assert config.DEFAULT_STRATEGY["pivot_lookback"] == 5
        assert config.ASSETS["BTCUSD"]["cost_price"] == 8.0
        btc, _, receipts = SOURCE.load_all(manifest)
        candles = btc["BTCUSDT"]
        signals = pa.generate(strategy,config,candles)
        periods = {}
        for year, start, end in (
            ("2024", "2024-01-01", "2025-01-01"),
            ("2025", "2025-01-01", "2026-01-01"),
            ("2026_JAN_SEP", "2026-01-01", "2026-10-01"),
        ):
            s = signals.loc[(signals.entry_time >= start)&(signals.entry_time < end)]
            c = candles.loc[candles.index < end]
            result = simulator.run(
                c, s, config.ASSETS["BTCUSD"]["exit"],
                risk_per_trade=0.02, cost_price=8.0, initial_equity=10000.0)
            t = result["trades"]
            curve = result["equity"]
            final = float(curve.iloc[-1]) if len(curve) else 10000.0
            highwater = curve.cummax().clip(lower=10000)
            drawdown = float(((curve/highwater)-1).min()) if len(curve) else 0.0
            periods[year] = {
                "raw_original_signals": len(s),
                "source_simulated_completed_trades": len(t),
                "native_optimistic_pseudoreturn_pct": round((final/10000-1)*100,5),
                "closed_trade_only_max_dd_pct": round(drawdown*100,5),
                "year_held_funding_cashflow_included": False,
                "native_same_signal_close_fill": True,
                "uses_realistic_futures_execution": False,
                "uses_full_margin_ledger": False,
            }
        out={
            "cycle":"A222","check":"original-author-unmodified-backtester-diagnostic",
            "market_data":"genuine Binance USD-M BTCUSDT 1h", "zip_sha_verified_count":len(receipts),
            "original_source_commit":pa.SHA, "source_receipts":original_files,
            "original_fixed_btc_cost_price_usd":8.0,
            "unsupported_for_profit_claim":True,
            "reason":"same-bar-close entry, fixed $8 BTC cost, zero genuine funding charges, closed-trade DD",
            "periods":periods,"verified_candidate":False,"no_orders":True,
        }
    folder = ROOT / "research/a222_price_action/evidence"
    folder.mkdir(exist_ok=True)
    (folder/"A222_ORIGINAL_NATIVE_SAME_CLOSE_DIAGNOSTIC.json").write_text(
        json.dumps(out, indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"diagnostic_only":True,"periods":periods},ensure_ascii=False))


if __name__=="__main__":
    run()
