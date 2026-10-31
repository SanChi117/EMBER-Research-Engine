"""A219: verify original chart pattern source SHA and venue gate; no market orders/PnL."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "2972c880144997ec305dc3dac23d78ee5a831176"
ORIGINALS = {
    "data/fetcher.py": "ce5e3b10752aa9b21ea487520c38662af932e4c9",
    "config.py": "71a8c72b7093d4a10c4479d0a1185a6555533c8b",
    "main.py": "01b9d5a08a905eb39ade5bd32b479edc2dd8a1ff",
    "backtest/portfolio.py": "1ad8d8e850ab692a00ed05af81a6e7f536f4106a",
}


def blob_sha(payload):
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()


def verified_sources():
    sources, receipts = {}, []
    for path, expected in ORIGINALS.items():
        url = f"https://raw.githubusercontent.com/juriok/chart-pattern-backtester/{COMMIT}/{path}"
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        actual = blob_sha(raw)
        if actual != expected:
            raise ValueError(f"pinned source changed: {path} {actual} != {expected}")
        sources[path] = raw.decode("utf-8")
        receipts.append({"path": path, "git_blob": actual, "sha256": hashlib.sha256(raw).hexdigest(), "url": url})
    return sources, receipts


def gate(source):
    data = source["data/fetcher.py"]
    config = source["config.py"]
    main = source["main.py"]
    checks = {
        "default_ccxt_without_futures_option": "getattr(ccxt, config.EXCHANGE)({'enableRateLimit': True})" in data,
        "top_pairs_declared_spot": "Return top-N USDT spot pairs" in data,
        "futures_perp_symbols_excluded": "and ':' not in sym" in data,
        "spot_style_pair_selection": "sym.endswith(f'/{config.QUOTE_CURRENCY}')" in data,
        "unqualified_ohlcv_from_spot_pairs": "ex.fetch_ohlcv(symbol, config.TIMEFRAME," in data,
        "default_binance_exchange": "EXCHANGE        = 'binance'" in config,
        "constant_funding_not_settlements": "FUNDING_RATE_8H  = 0.0001" in config,
        "main_uses_spot_fetcher": "from data.fetcher import top_pairs, fetch_ohlcv" in main,
    }
    if not all(checks.values()):
        raise AssertionError(f"Source verification changed: {checks}")
    return checks


def run():
    mandate = json.loads((ROOT / "config/research_mandate.lock.json").read_text())
    assert mandate["state"] == "LOCKED_USER_ONLY"
    assert mandate["scope"] == "BINANCE_USDT_M_FUTURES"
    sources, receipts = verified_sources()
    checks = gate(sources)
    result = {
        "cycle": "A219",
        "verdict": "REJECTED_SOURCE_VENUE_MISMATCH",
        "futures_trading_dataset": False,
        "original_futures_profit_reproduced": False,
        "economic_test_attempted": False,
        "is_ready_for_paper_or_live": False,
        "original_commit": COMMIT,
        "blob_receipts": receipts,
        "source_gates": checks,
        "reason": "Original chart pattern ranking, CSV and OHLCV ingest are CCXT SPOT not Binance USD-M futures, funding is constant",
    }
    out = ROOT / "research/a219_chart_patterns_venue/evidence.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "sha_verified_files": len(receipts), "checks": len(checks)}))


if __name__ == "__main__":
    run()
