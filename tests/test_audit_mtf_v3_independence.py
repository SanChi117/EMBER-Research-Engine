"""Tests for no-hindsight symbol de-overlap and market-synchronous grouping."""
from scripts.audit_mtf_v3_independence import audit, choose_symbol_nonoverlap


def trade(
    event_id: str,
    *,
    symbol: str = "SOLUSDT",
    zone_family: str = "swing",
    entry: int = 0,
    exit: int = 100,
    pnl: float = -2.0,
    variant: str = "PRICE_ONLY",
) -> dict:
    return {
        "event_id": event_id,
        "symbol": symbol,
        "zone_family": zone_family,
        "entry_at": entry,
        "contact_at": entry - 1,
        "exit_at": exit,
        "status": "SIMULATED",
        "research_variant": variant,
        "exit_reason": "STOP" if pnl < 0 else "TIME_24H",
        "stress_proxy_nominal_pct": pnl,
    }


def test_overlap_does_not_use_future_winner() -> None:
    # Same-time OB is selected over the later-listed profitable FVG.
    rows = [
        trade("winner", zone_family="fvg", pnl=12),
        trade("loser", zone_family="order_block", pnl=-8),
        trade("after", entry=100, exit=200, pnl=1),
    ]
    kept, removed = choose_symbol_nonoverlap(rows)
    assert [r["event_id"] for r in kept] == ["loser", "after"]
    assert [r["event_id"] for r in removed] == ["winner"]


def test_parallel_symbols_not_suppressed() -> None:
    rows = [
        trade("a", entry=0, exit=100),
        trade("b", symbol="ETHUSDT", entry=0, exit=100),
        trade("c", entry=50, exit=150),
    ]
    kept, removed = choose_symbol_nonoverlap(rows)
    assert {r["event_id"] for r in kept} == {"a", "b"}
    assert {r["event_id"] for r in removed} == {"c"}


def test_audit_reports_synchronized_market_day_and_denominators() -> None:
    rows = [
        trade("a", symbol="BTCUSDT", entry=0),
        trade("b", symbol="ETHUSDT", entry=0),
        trade("c", symbol="SOLUSDT", entry=0),
    ]
    result = audit(rows)
    p = result["variants"]["PRICE_ONLY"]
    assert p["all_entry_hypotheses"]["events"] == 3
    assert p["all_entry_hypotheses"]["days_with_3plus_symbols"] == 1
    assert p["all_entry_hypotheses"]["hours_with_3plus_symbols"] == 1
    assert p["one_at_a_time_per_symbol"]["events"] == 3
    assert result["variants"]["TAKER_CONFIRMED"]["all_entry_hypotheses"]["events"] == 0
