"""TZ-2: POSIX durable, monthly SHA256-chain JSONL flow journal.

No trading code. No synthetic observations. One SHA chain per monthly shard.
External Git/S3 witnesses are required to detect deletion of a VALID tail.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import sha_ledger
from .market_contract import timestamp
from .paper_ledger import _normalize

STREAMS = ("oi", "liquidations", "funding")
KINDS = {
    "oi": {"OI_SNAPSHOT", "GAP", "COLLECTOR_RESTART", "SCHEMA_DRIFT", "SCHEDULER_JITTER"},
    "funding": {"FUNDING_SCHEDULE", "FUNDING_SETTLED", "GAP", "COLLECTOR_RESTART",
                "SCHEMA_DRIFT", "SCHEDULER_JITTER"},
    "liquidations": {"LIQ_FORCE_ORDER", "LIQ_HEARTBEAT", "LIQ_SNAPSHOT_PARTIAL",
                     "GAP", "COLLECTOR_RESTART", "SCHEMA_DRIFT"},
}
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9:_.-]{0,159}\Z")
SHARD = re.compile(r"(oi|funding|liquidations)_(\d{4})_(0[1-9]|1[0-2])\.jsonl\Z")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise sha_ledger.LedgerError("FLOW_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _bad_constant(_: str) -> None:
    raise sha_ledger.LedgerError("NONFINITE_FLOW_JSON")


def shard_name(stream: str, observed_at_ms: int) -> str:
    if stream not in STREAMS or type(observed_at_ms) is not int:
        raise sha_ledger.LedgerError("INVALID_FLOW_STREAM_OR_TIMESTAMP")
    timestamp(observed_at_ms)
    month = datetime.fromtimestamp(observed_at_ms / 1000, tz=timezone.utc)
    return f"{stream}_{month.year:04d}_{month.month:02d}.jsonl"


def _check_payload(stream: str, kind: str, event_id: str, payload: dict) -> dict:
    if stream not in STREAMS or kind not in KINDS[stream]:
        raise sha_ledger.LedgerError("UNKNOWN_FLOW_KIND")
    if type(event_id) is not str or not NAME.fullmatch(event_id):
        raise sha_ledger.LedgerError("INVALID_FLOW_EVENT_ID")
    if type(payload) is not dict:
        raise sha_ledger.LedgerError("INVALID_FLOW_PAYLOAD")
    value = _normalize(payload)
    if type(value.get("observed_at_ms")) is not int:
        raise sha_ledger.LedgerError("MISSING_OBSERVED_AT_MS")
    timestamp(value["observed_at_ms"])
    if type(value.get("source")) is not str or not value["source"]:
        raise sha_ledger.LedgerError("MISSING_FLOW_SOURCE")
    if type(value.get("symbol")) is not str or not value["symbol"]:
        raise sha_ledger.LedgerError("MISSING_FLOW_SYMBOL")
    return value


@contextmanager
def _lock(path: Path, *, exclusive: bool):
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class FlowStore:
    """Each append validates every existing shard and refuses corrupt history."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)

    def _files(self, stream: str) -> list[Path]:
        if stream not in STREAMS:
            raise sha_ledger.LedgerError("UNKNOWN_FLOW_STREAM")
        if not self.root.exists():
            return []
        return sorted(path for path in self.root.iterdir()
                      if path.name.startswith(stream + "_")
                      and path.name.endswith(".jsonl"))

    def _read_file(self, path: Path) -> tuple[dict, ...]:
        match = SHARD.fullmatch(path.name)
        if not match or not path.is_file() or path.is_symlink():
            raise sha_ledger.LedgerError("INVALID_FLOW_SHARD")
        data = path.read_bytes()
        if data and not data.endswith(b"\n"):
            raise sha_ledger.LedgerError("FLOW_TORN_TAIL")
        records = []
        for line in data.splitlines():
            try:
                item = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_pairs,
                                  parse_constant=_bad_constant)
                if type(item) is not dict or line != sha_ledger.canonical(item):
                    raise sha_ledger.LedgerError("NONCANONICAL_FLOW_JSON")
                value = _check_payload(match[1], item["event_type"],
                                       item["event_id"], item["payload"])
                if shard_name(match[1], value["observed_at_ms"]) != path.name:
                    raise sha_ledger.LedgerError("WRONG_FLOW_SHARD_MONTH")
            except (UnicodeError, TypeError, KeyError, ValueError) as exc:
                raise sha_ledger.LedgerError(f"FLOW_RECORD_INVALID: {exc}") from exc
            records.append(item)
        sha_ledger.verify(records)
        return tuple(records)

    def _read_all_unlocked(self, stream: str) -> dict[str, tuple[dict, ...]]:
        return {p.name: self._read_file(p) for p in self._files(stream)}

    def shards(self, stream: str) -> dict[str, tuple[dict, ...]]:
        self.root.mkdir(parents=True, exist_ok=True)
        with _lock(self.root / f".{stream}.lock", exclusive=False):
            return self._read_all_unlocked(stream)

    def events(self, stream: str) -> tuple[dict, ...]:
        shards = self.shards(stream)
        result = tuple(event for rows in shards.values() for event in rows)
        ids = [row["event_id"] for row in result]
        if len(ids) != len(set(ids)):
            raise sha_ledger.LedgerError("DUPLICATE_FLOW_EVENT_ACROSS_SHARDS")
        return result

    def verify(self, *, expected_heads: dict[str, str] | None = None) -> dict[str, str]:
        heads = {}
        for stream in STREAMS:
            for name, rows in self.shards(stream).items():
                heads[name] = sha_ledger.verify(rows)
        if expected_heads is not None:
            if set(expected_heads) != set(heads):
                raise sha_ledger.LedgerError("FLOW_WITNESS_SHARD_SET_MISMATCH")
            if any(heads[name] != head for name, head in expected_heads.items()):
                raise sha_ledger.LedgerError("FLOW_EXTERNAL_HEAD_MISMATCH")
        return heads

    def append(self, stream: str, *, event_id: str, event_type: str,
               payload: dict) -> dict:
        data = _check_payload(stream, event_type, event_id, payload)
        self.root.mkdir(parents=True, exist_ok=True)
        filename = shard_name(stream, data["observed_at_ms"])
        with _lock(self.root / f".{stream}.lock", exclusive=True):
            all_rows = self._read_all_unlocked(stream)
            flattened = [r for records in all_rows.values() for r in records]
            if any(r["event_id"] == event_id for r in flattened):
                raise sha_ledger.LedgerError("DUPLICATE_FLOW_EVENT")
            if any(r["event_type"] == "SCHEMA_DRIFT" for r in flattened):
                raise sha_ledger.LedgerError("FLOW_HALTED_SCHEMA_DRIFT")
            # Once a newer monthly shard exists, never append to an
            # older shard, even if a caller supplies an old observed clock.
            if all_rows and filename < max(all_rows):
                raise sha_ledger.LedgerError("OLD_FLOW_SHARD_IS_IMMUTABLE")
            current = all_rows.get(filename, ())
            new = sha_ledger.extend(current, event_id=event_id,
                                    event_type=event_type, payload=data)[-1]
            path = self.root / filename
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            created = not path.exists()
            fd = os.open(path, flags, 0o600)
            try:
                data_bytes = sha_ledger.canonical(new) + b"\n"
                while data_bytes:
                    count = os.write(fd, data_bytes)
                    if count <= 0:
                        raise sha_ledger.LedgerError("FLOW_SHORT_WRITE")
                    data_bytes = data_bytes[count:]
                os.fsync(fd)
            finally:
                os.close(fd)
            if created:
                folder_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(folder_fd)
                finally:
                    os.close(folder_fd)
            return new
