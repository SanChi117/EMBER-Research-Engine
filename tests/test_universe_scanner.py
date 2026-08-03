from __future__ import annotations

from scripts.scan_universe import filter_usdt_perpetual_symbols, qualifies


def test_futures_universe_filter_is_deterministic() -> None:
    payload = {
        "symbols": [
            {
                "symbol": "AAAUSDT",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "BBBUSDT",
                "status": "BREAK",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "CCCUSDC",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDC",
            },
            {
                "symbol": "DDDUSDT",
                "status": "TRADING",
                "contractType": "CURRENT_QUARTER",
                "quoteAsset": "USDT",
            },
        ]
    }

    assert filter_usdt_perpetual_symbols(payload, set()) == ["AAAUSDT"]
    assert filter_usdt_perpetual_symbols(payload, {"AAAUSDT"}) == []


def test_scanner_thresholds_are_strict() -> None:
    assert qualifies(10, 1.01, 10, 1.0)
    assert not qualifies(9, 2.0, 10, 1.0)
    assert not qualifies(10, 1.0, 10, 1.0)
    assert qualifies(10, "inf", 10, 1.0)
