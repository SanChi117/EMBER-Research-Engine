"""RESET-05 part 2 golden tests: persistent JSONL / recovery / tamper / duplicates."""
from __future__ import annotations

import json
import os
from decimal import Decimal
from multiprocessing import Process

import pytest

from research.platform import sha_ledger
from research.platform.paper_ledger import JsonlPaperLedgerStore

NOW = 1762000000000
EVENTS = ("signals", "trades", "executability")


def sample(i=1):
    return {"observed_at_ms": NOW + i, "symbol": "SOLUSDT", "qty": Decimal("0.125")}


def add(db, stream="signals", i=1):
    prefix = {"signals": "SIGNAL_CREATED", "trades": "TRADE_OPENED",
              "executability": "EXECUTABILITY_CHECKED"}[stream]
    return db.append(stream, event_id=f"{stream}:{i}",
                     event_type=prefix, payload=sample(i))


def _concurrent_writer(root, start, count):
    db = JsonlPaperLedgerStore(root)
    for i in range(start, start + count):
        add(db, "trades", i)


def test_three_streams_are_isolated_and_have_sha_chains(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    for stream in EVENTS:
        result = add(db, stream=stream)
        assert db.verify(stream) == result["record_sha256"]
        assert db.read(stream)[0]["payload"]["qty"] == "0.125"
        assert len(db.read(stream)) == 1
        assert (tmp_path / f"{stream}.jsonl").exists()
    assert len(list(tmp_path.glob("*.jsonl"))) == 3
    assert db.verify_all() == {s: db.verify(s) for s in EVENTS}


def test_restart_recovery_continues_exact_chain(tmp_path):
    one = JsonlPaperLedgerStore(tmp_path)
    first = add(one, i=1)
    second = add(one, i=2)
    assert second["prev_sha256"] == first["record_sha256"]
    del one
    resumed = JsonlPaperLedgerStore(tmp_path)
    assert resumed.verify("signals") == second["record_sha256"]
    third = add(resumed, i=3)
    assert third["seq"] == 3
    assert third["prev_sha256"] == second["record_sha256"]
    assert len(resumed.read("signals")) == 3


def test_reject_duplicate_even_after_restart(tmp_path):
    add(JsonlPaperLedgerStore(tmp_path), i=7)
    other = JsonlPaperLedgerStore(tmp_path)
    with pytest.raises(sha_ledger.LedgerError, match="DUPLICATE_EVENT"):
        add(other, i=7)
    assert len(other.read("signals")) == 1


def test_detect_middle_byte_tamper_and_refuse_next_append(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    add(db, i=1)
    add(db, i=2)
    path = tmp_path / "signals.jsonl"
    raw = path.read_bytes()
    assert b"SOLUSDT" in raw
    altered = raw.replace(b"SOLUSDT", b"NEARUSD", 1)
    path.write_bytes(altered)
    with pytest.raises(sha_ledger.LedgerError, match="BROKEN_PAPER_SHA_CHAIN"):
        db.verify("signals")
    with pytest.raises(sha_ledger.LedgerError):
        add(db, i=3)
    assert path.read_bytes() == altered


def test_torn_tail_is_not_silently_repaired(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    add(db)
    p = tmp_path / "signals.jsonl"
    raw = p.read_bytes()
    p.write_bytes(raw[:-1])
    with pytest.raises(sha_ledger.LedgerError, match="TORN_JSONL_TAIL"):
        db.read("signals")
    with pytest.raises(sha_ledger.LedgerError, match="TORN_JSONL_TAIL"):
        add(db, i=2)
    assert p.read_bytes() == raw[:-1]


def test_external_witness_detects_valid_tail_deletion(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    add(db, i=1)
    add(db, i=2)
    recorded_head = db.verify("signals")
    p = tmp_path / "signals.jsonl"
    p.write_bytes(p.read_bytes().splitlines(keepends=True)[0])
    assert db.verify("signals") != recorded_head
    with pytest.raises(sha_ledger.LedgerError, match="EXTERNAL_HEAD_WITNESS_MISMATCH"):
        db.verify("signals", expected_head=recorded_head)


def test_bad_cross_stream_type_cannot_mix_signals_with_trades(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    with pytest.raises(sha_ledger.LedgerError, match="CROSS_STREAM"):
        db.append("signals", event_id="x", event_type="TRADE_OPENED", payload=sample())
    with pytest.raises(sha_ledger.LedgerError, match="UNKNOWN_PAPER_STREAM"):
        db.read("../trades")
    assert not list(tmp_path.glob("*.jsonl"))


def test_payload_requires_timestamp_and_exact_types(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    with pytest.raises(sha_ledger.LedgerError, match="OBSERVED_AT_MS_REQUIRED"):
        db.append("trades", event_id="x", event_type="TRADE_OPENED",
                  payload={"qty": "1"})
    with pytest.raises(sha_ledger.LedgerError, match="OBSERVED_AT_MS_REQUIRED"):
        db.append("trades", event_id="x", event_type="TRADE_OPENED",
                  payload={"observed_at_ms": True})
    with pytest.raises(sha_ledger.LedgerError, match="NONCANONICAL_PAYLOAD_VALUE"):
        db.append("signals", event_id="x", event_type="SIGNAL_CREATED",
                  payload={"observed_at_ms": NOW, "qty": 0.12})
    with pytest.raises(sha_ledger.LedgerError, match="NONFINITE_DECIMAL"):
        db.append("signals", event_id="x", event_type="SIGNAL_CREATED",
                  payload={"observed_at_ms": NOW, "qty": Decimal("NaN")})


def test_nested_decimal_normalization_and_input_not_mutated(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    payload = {"observed_at_ms": NOW, "meta": {"fees": [Decimal("0.0004")]}}
    result = db.append("executability", event_id="x",
                       event_type="EXECUTABILITY_REJECTED", payload=payload)
    assert isinstance(payload["meta"]["fees"][0], Decimal)
    assert result["payload"]["meta"]["fees"] == ["0.0004"]
    assert db.verify("executability") == result["record_sha256"]


def test_corrupt_duplicate_json_key_is_rejected(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    add(db)
    path = tmp_path / "signals.jsonl"
    row = json.loads(path.read_text())
    line = json.dumps(row, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    path.write_text(line.replace('"seq":1', '"seq":1,"seq":1') + "\n")
    with pytest.raises(sha_ledger.LedgerError, match="DUPLICATE_JSON_KEY"):
        db.read("signals")


@pytest.mark.skipif(os.name != "posix", reason="fcntl POSIX only")
def test_two_processes_append_without_overwriting_sequences(tmp_path):
    a = Process(target=_concurrent_writer, args=(tmp_path, 10, 6))
    b = Process(target=_concurrent_writer, args=(tmp_path, 20, 6))
    a.start()
    b.start()
    a.join(timeout=15)
    b.join(timeout=15)
    assert a.exitcode == 0 and b.exitcode == 0
    entries = JsonlPaperLedgerStore(tmp_path).read("trades")
    assert len(entries) == 12
    assert [record["seq"] for record in entries] == list(range(1, 13))
    assert {record["event_id"] for record in entries} == {
        *(f"trades:{i}" for i in range(10, 16)),
        *(f"trades:{i}" for i in range(20, 26)),
    }


def test_no_network_or_live_adapter_in_contract(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    assert db.verify_all() == {stream: sha_ledger.GENESIS for stream in EVENTS}
    assert not hasattr(db, "place_order")
    assert not hasattr(db, "exchange_client")
