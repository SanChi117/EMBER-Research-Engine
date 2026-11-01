"""TZ-2: provider mock, adversarial SHA, and strict synthetic 7-day QA tests."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from research.platform import flow_collector as c
from research.platform import flow_liquidations as l
from research.platform import verify_flows as v
from research.platform.flow_ledger import FlowStore

TS = 1793491230000
HOUR = 3_600_000


def event(store, stream, kind, name, at=TS, **extra):
    return store.append(stream, event_id=name, event_type=kind,
                        payload={"observed_at_ms": at, "symbol": "SOLUSDT",
                                 "source": "https://fapi.binance.com/fapi/v1/openInterest",
                                 **extra})


def test_owner_universe_is_twelve_and_binance_only():
    symbols = c.symbols_from_config()
    assert len(symbols) == 12
    assert set(("BTCUSDT", "ETHUSDT")).issubset(symbols)
    assert "OPUSDT" not in symbols


def test_monthly_sha_chain_rollover_and_external_heads(tmp_path):
    store = FlowStore(tmp_path)
    november = 1793491230000
    december = 1796083230000
    first = event(store, "oi", "OI_SNAPSHOT", "sol:nov", november, slot_ms=november // HOUR * HOUR)
    second = event(store, "oi", "OI_SNAPSHOT", "sol:dec", december, slot_ms=december // HOUR * HOUR)
    heads = store.verify()
    assert len(heads) == 2
    assert first["seq"] == 1 and second["seq"] == 1
    assert store.verify(expected_heads=heads) == heads
    with pytest.raises(ValueError, match="FLOW_EXTERNAL_HEAD_MISMATCH"):
        store.verify(expected_heads={**heads, "oi_2026_11.jsonl": "0" * 64})


def test_tamper_middle_byte_fails_closed_and_blocks_append(tmp_path):
    store = FlowStore(tmp_path)
    event(store, "oi", "OI_SNAPSHOT", "sol:1")
    event(store, "oi", "OI_SNAPSHOT", "sol:2")
    path = tmp_path / "oi_2026_11.jsonl"
    before = path.read_bytes()
    path.write_bytes(before.replace(b"SOLUSDT", b"LINKUSD", 1))
    with pytest.raises(ValueError):
        v.verify_flows(tmp_path)
    with pytest.raises(ValueError):
        event(store, "oi", "OI_SNAPSHOT", "sol:3")
    assert path.read_bytes() != before


def test_torn_tail_rejected_without_silent_truncation(tmp_path):
    store = FlowStore(tmp_path)
    event(store, "funding", "FUNDING_SETTLED", "settle:1")
    path = tmp_path / "funding_2026_11.jsonl"
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError, match="FLOW_TORN_TAIL"):
        store.verify()


def test_duplicate_event_rejected_across_restart(tmp_path):
    store = FlowStore(tmp_path)
    event(store, "oi", "OI_SNAPSHOT", "same")
    resumed = FlowStore(tmp_path)
    with pytest.raises(ValueError, match="DUPLICATE_FLOW_EVENT"):
        event(resumed, "oi", "OI_SNAPSHOT", "same")


def test_missing_observation_source_and_float_refused(tmp_path):
    store = FlowStore(tmp_path)
    with pytest.raises(ValueError, match="MISSING_OBSERVED_AT_MS"):
        store.append("oi", event_id="x", event_type="OI_SNAPSHOT",
                     payload={"symbol": "SOLUSDT", "source": "binance"})
    with pytest.raises(ValueError, match="MISSING_FLOW_SOURCE"):
        store.append("oi", event_id="x", event_type="OI_SNAPSHOT",
                     payload={"symbol": "SOLUSDT", "observed_at_ms": TS})
    with pytest.raises(ValueError):
        event(store, "oi", "OI_SNAPSHOT", "float", value=0.1)


def test_schema_drift_is_persisted_and_stream_halted(tmp_path):
    store = FlowStore(tmp_path)
    event(store, "oi", "SCHEMA_DRIFT", "drift", reason="TEST_BREAK")
    with pytest.raises(ValueError, match="FLOW_HALTED_SCHEMA_DRIFT"):
        event(store, "oi", "OI_SNAPSHOT", "after")
    with pytest.raises(v.FlowVerificationError, match="SCHEMA_DRIFT_FAIL_CLOSED"):
        v.verify_flows(tmp_path)


def fake_fetch(endpoint, params):
    symbol = params["symbol"]
    if endpoint == c.OI_ENDPOINT:
        return {"symbol": symbol, "openInterest": "105.50", "time": TS - 10}
    if endpoint == c.PREMIUM_ENDPOINT:
        return {"symbol": symbol, "lastFundingRate": "0.00005",
                "nextFundingTime": TS + 8 * HOUR, "time": TS - 10}
    if endpoint == c.SETTLEMENT_ENDPOINT:
        return [{"symbol": symbol, "fundingRate": "-0.00001",
                 "fundingTime": TS - HOUR}]
    raise AssertionError(endpoint)


def test_mock_rest_collect_is_no_credentials_and_deduplicates(tmp_path):
    store = FlowStore(tmp_path)
    symbols = c.symbols_from_config()
    first = c.collect_once(store, symbols, now_ms=TS, fetch=fake_fetch)
    assert first["oi_written"] == 12
    assert first["funding_written"] == 24
    counts = {name: len(store.events(name)) for name in ("oi", "funding")}
    second = c.collect_once(store, symbols, now_ms=TS, fetch=fake_fetch)
    assert second["oi_written"] == 0
    assert second["funding_written"] == 0
    assert {name: len(store.events(name)) for name in counts} == counts
    assert all(r["payload"]["observed_at_ms"] == TS
               for r in store.events("oi"))


def test_http_timeout_yields_gaps_not_oi_synthetic_values(tmp_path):
    def timeout(endpoint, params):
        if endpoint == c.OI_ENDPOINT:
            raise c.TransportFailure("HTTP_451")
        return fake_fetch(endpoint, params)
    store = FlowStore(tmp_path)
    stats = c.collect_once(store, c.symbols_from_config(),
                           now_ms=TS, fetch=timeout)
    assert stats["oi_gap"] == 12
    assert not any(x["event_type"] == "OI_SNAPSHOT" for x in store.events("oi"))
    assert sum(x["event_type"] == "GAP" for x in store.events("oi")) == 12


def test_schema_change_records_event_and_haltes_future_write(tmp_path):
    def bad_fetch(endpoint, params):
        if endpoint == c.OI_ENDPOINT:
            return {"symbol": params["symbol"], "openInterest": 3.2, "time": TS}
        return fake_fetch(endpoint, params)
    store = FlowStore(tmp_path)
    with pytest.raises(c.SourceSchemaDrift):
        c.collect_once(store, c.symbols_from_config(), now_ms=TS, fetch=bad_fetch)
    assert any(x["event_type"] == "SCHEMA_DRIFT" for x in store.events("oi"))


def test_liq_provider_snapshot_normalization():
    packet = {
        "stream": "solusdt@forceOrder",
        "data": {
            "e": "forceOrder", "E": TS - 10, "st": 1,
            "o": {"s": "SOLUSDT", "S": "SELL", "T": TS - 20,
                  "q": "3", "p": "155.2", "ap": "155.19",
                  "l": "0.6", "z": "1.2"},
        },
    }
    event_id, payload = l.force_order_from_message(
        packet, c.symbols_from_config(), observed_at_ms=TS,
    )
    assert "SOLUSDT" in event_id
    assert payload["provider_semantics"].startswith("LATEST_ONE_SNAPSHOT")
    assert payload["quantity"] == "3"
    packet["data"]["st"] = 2
    with pytest.raises(l.LiquidationSchemaDrift, match="NOT_USD_M"):
        l.force_order_from_message(packet, c.symbols_from_config(),
                                   observed_at_ms=TS)


def test_explicit_websocket_partial_is_not_fake_liquidation(tmp_path):
    store = FlowStore(tmp_path)
    l.mark_partial(store, observed_at_ms=TS, reason="HTTP_451_NO_WEBSOCKET")
    entries = store.events("liquidations")
    assert len(entries) == 1
    assert entries[0]["event_type"] == "LIQ_SNAPSHOT_PARTIAL"


class FakeStore:
    def __init__(self, mapping):
        self.mapping = mapping

    def events(self, stream):
        return tuple(self.mapping.get(stream, ()))


def synthetic_week(*, oi_missing=0, mark_gaps=True, partial=False):
    symbols = c.symbols_from_config()
    start = int(datetime(2026, 11, 2, tzinfo=timezone.utc).timestamp() * 1000)
    end = start + 7 * 24 * HOUR
    rows = {"oi": [], "funding": [], "liquidations": []}
    for si, symbol in enumerate(symbols):
        for i in range(168):
            t = start + i * HOUR + 30_000
            if si == 0 and i < oi_missing:
                if mark_gaps:
                    rows["oi"].append({"event_type": "GAP",
                        "payload": {"symbol": symbol, "slot_ms": start + i * HOUR,
                                    "observed_at_ms": t}})
                continue
            rows["oi"].append({"event_type": "OI_SNAPSHOT",
                "payload": {"symbol": symbol, "observed_at_ms": t,
                            "slot_ms": start + i * HOUR}})
            rows["funding"].append({"event_type": "FUNDING_SCHEDULE",
                "payload": {"symbol": symbol, "observed_at_ms": t,
                            "slot_ms": start + i * HOUR,
                            "next_funding_time_ms": start + ((i // 8) + 1) * 8 * HOUR}})
        for period in range(1, 21):
            rows["funding"].append({"event_type": "FUNDING_SETTLED",
                "payload": {"symbol": symbol,
                            "observed_at_ms": start + period * 8 * HOUR + 1_000,
                            "funding_time_ms": start + period * 8 * HOUR}})
    for i in range(7 * 24 * 60):
        minute = start + i * 60_000
        rows["liquidations"].append({"event_type": "LIQ_HEARTBEAT",
            "payload": {"symbol": "*", "observed_at_ms": minute + 1_000,
                        "minute_slot_ms": minute,
                        "evidence": "WEBSOCKET_PONG_CONFIRMED"}})
    if partial:
        rows["liquidations"].append({"event_type": "LIQ_SNAPSHOT_PARTIAL",
            "payload": {"observed_at_ms": start + HOUR}})
    return FakeStore(rows), symbols, start, end


def test_fully_populated_synthetic_7day_week_only_test_fixture():
    store, symbols, start, end = synthetic_week()
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["seven_day_acceptance"] == "PASS"
    assert result["oi"]["observed_slots"] == 2016
    assert result["liquidations"]["confirmed_pong_minutes"] == 10080


def test_less_than_95pct_oi_is_not_accepted_even_if_gaps_explicit():
    store, symbols, start, end = synthetic_week(oi_missing=110)
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["oi"]["status"] == "IN_PROGRESS"
    assert result["seven_day_acceptance"] == "IN_PROGRESS"


def test_unknown_oi_gaps_fail_closed_even_if_above_95pct():
    store, symbols, start, end = synthetic_week(oi_missing=1, mark_gaps=False)
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["oi"]["unmarked_missing_slots"] == 1
    assert result["seven_day_acceptance"] == "IN_PROGRESS"


def test_liquidation_partial_is_explicit_and_not_full_acceptance():
    store, symbols, start, end = synthetic_week(partial=True)
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["seven_day_acceptance"] == "PARTIAL_LIQUIDATIONS"
    assert result["liquidations"]["status"] == "LIQ_SNAPSHOT_PARTIAL"


def test_funding_missing_one_settlement_prevents_acceptance():
    store, symbols, start, end = synthetic_week()
    store.mapping["funding"] = [
        x for x in store.mapping["funding"]
        if not (x["event_type"] == "FUNDING_SETTLED"
                and x["payload"]["symbol"] == "SOLUSDT"
                and x["payload"]["funding_time_ms"] == start + 8 * HOUR)
    ]
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["funding"]["status"] == "IN_PROGRESS"
    assert result["seven_day_acceptance"] == "IN_PROGRESS"


def test_no_trading_order_api_in_collector():
    from research.platform import flow_collector, flow_liquidations

    assert not hasattr(flow_collector, "place_order")
    assert not hasattr(flow_liquidations, "place_order")
    assert Decimal("1.2").is_finite()


def test_single_symbol_under_95pct_rejects_even_when_pool_average_passes():
    store, symbols, start, end = synthetic_week(oi_missing=10)
    result = v.coverage_report(store, symbols, start_ms=start, end_ms=end)
    assert result["oi"]["coverage_rate"] > "0.950000"
    assert result["oi"]["per_symbol"]["SOLUSDT"]["status"] == "IN_PROGRESS"
    assert result["seven_day_acceptance"] == "IN_PROGRESS"


def test_older_month_is_frozen_after_new_month_created(tmp_path):
    store = FlowStore(tmp_path)
    november = 1793491230000
    december = 1796083230000
    event(store, "oi", "OI_SNAPSHOT", "first", november)
    event(store, "oi", "OI_SNAPSHOT", "second", december)
    with pytest.raises(ValueError, match="OLD_FLOW_SHARD_IS_IMMUTABLE"):
        event(store, "oi", "OI_SNAPSHOT", "retroactive", november + 30_000)
