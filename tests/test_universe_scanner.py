from __future__ import annotations

from scripts.scan_universe import (
    filter_usdt_perpetual_symbols,
    parse_quote_volumes,
    qualifies,
    rank_symbols_by_volume,
)


def test_futures_universe_filter_is_deterministic() -> None:
    payload = {
        "symbols": [
            {
                "symbol": "AAAUSDT",
                "baseAsset": "AAA",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "BBBUSDT",
                "baseAsset": "BBB",
                "status": "BREAK",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "CCCUSDC",
                "baseAsset": "CCC",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDC",
            },
            {
                "symbol": "DDDUSDT",
                "baseAsset": "DDD",
                "status": "TRADING",
                "contractType": "CURRENT_QUARTER",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "AAAUPUSDT",
                "baseAsset": "AAAUP",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
        ]
    }

    assert filter_usdt_perpetual_symbols(payload, set()) == ["AAAUSDT"]
    assert filter_usdt_perpetual_symbols(payload, {"AAAUSDT"}) == []


def test_volume_ranking_is_descending_and_deterministic() -> None:
    volumes = parse_quote_volumes(
        [
            {"symbol": "AAAUSDT", "quoteVolume": "100"},
            {"symbol": "BBBUSDT", "quoteVolume": "300"},
            {"symbol": "CCCUSDT", "quoteVolume": "300"},
        ]
    )
    assert rank_symbols_by_volume(
        ["AAAUSDT", "CCCUSDT", "BBBUSDT"], volumes
    ) == ["BBBUSDT", "CCCUSDT", "AAAUSDT"]


def test_scanner_thresholds_are_strict() -> None:
    assert qualifies(10, 1.01, 10, 1.0)
    assert not qualifies(9, 2.0, 10, 1.0)
    assert not qualifies(10, 1.0, 10, 1.0)
    assert qualifies(10, "inf", 10, 1.0)
