"""RESET-05 part 2: durable, append-only, strategy-neutral PAPER event storage.

Uses the EXISTING sha_ledger.extend/verify chain format. No exchange clients,
no order APIs, no strategy, no trading decisions or external services.
Supported writer host: POSIX/Linux (fcntl lock + fsync).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from . import sha_ledger
from .market_contract import DataUntrusted, timestamp

STREAM_PREFIXES = {
    "signals": "SIGNAL_",
    "trades": "TRADE_",
    "executability": "EXECUTABILITY_",
}
_EVENT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9:_.-]{0,127}\Z")


class PaperLedgerStore(Protocol):
    """Storage-agnostic API; a future Postgres store can implement it unchanged."""

    def append(
        self, stream: str, *, event_id: str, event_type: str, payload: dict
    ) -> dict: ...

    def read(self, stream: str) -> tuple[dict, ...]: ...

    def verify(self, stream: str, *, expected_head: str | None = None) -> str: ...


def _stream_prefix(stream: str) -> str:
    if type(stream) is not str or stream not in STREAM_PREFIXES:
        raise sha_ledger.LedgerError("UNKNOWN_PAPER_STREAM")
    return STREAM_PREFIXES[stream]


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise sha_ledger.LedgerError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_json_nonfinite(value: str) -> None:
    raise sha_ledger.LedgerError("NONFINITE_JSON")


def _normalize(value: object) -> object:
    """JSON-safe immutable snapshot; floats are refused, Decimal stored as string."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise sha_ledger.LedgerError("NONFINITE_DECIMAL")
        return format(value, "f")
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is list:
        return [_normalize(item) for item in value]
    if type(value) is dict:
        if not all(type(key) is str for key in value):
            raise sha_ledger.LedgerError("NONSTRING_JSON_KEY")
        return {key: _normalize(item) for key, item in value.items()}
    raise sha_ledger.LedgerError("NONCANONICAL_PAYLOAD_VALUE")


def _validate_event(
    stream: str, *, event_id: str, event_type: str, payload: object
) -> dict:
    prefix = _stream_prefix(stream)
    if type(event_id) is not str or not _EVENT_ID.fullmatch(event_id):
        raise sha_ledger.LedgerError("INVALID_EVENT_ID")
    if (
        type(event_type) is not str
        or not event_type.startswith(prefix)
        or not re.fullmatch(r"[A-Z0-9_]{2,80}", event_type)
    ):
        raise sha_ledger.LedgerError("CROSS_STREAM_EVENT_TYPE")
    if type(payload) is not dict:
        raise sha_ledger.LedgerError("PAPER_PAYLOAD_DICT_REQUIRED")
    normalized = _normalize(payload)
    try:
        timestamp(normalized["observed_at_ms"])
    except (KeyError, DataUntrusted) as exc:
        raise sha_ledger.LedgerError("OBSERVED_AT_MS_REQUIRED") from exc
    return normalized


@contextmanager
def _stream_lock(lock_path: Path, *, exclusive: bool):
    # Separate stable lock file avoids inode-lock loss during crashes/restarts.
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


class JsonlPaperLedgerStore:
    """One append-only JSONL file per stream, locked over read/verify/append."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)

    def _paths(self, stream: str) -> tuple[Path, Path]:
        _stream_prefix(stream)
        return self.root / f"{stream}.jsonl", self.root / f".{stream}.lock"

    def _read_unlocked(self, stream: str, data_path: Path) -> tuple[dict, ...]:
        if not data_path.exists():
            return ()
        if not data_path.is_file() or data_path.is_symlink():
            raise sha_ledger.LedgerError("INVALID_LEDGER_FILE")
        raw = data_path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            raise sha_ledger.LedgerError("TORN_JSONL_TAIL")
        records: list[dict] = []
        for line_number, line in enumerate(raw.splitlines(), 1):
            if not line:
                raise sha_ledger.LedgerError(f"EMPTY_RECORD_LINE_{line_number}")
            try:
                row = json.loads(
                    line.decode("utf-8"),
                    object_pairs_hook=_pairs_unique,
                    parse_constant=_reject_json_nonfinite,
                )
                if not isinstance(row, dict) or line != sha_ledger.canonical(row):
                    raise sha_ledger.LedgerError("NONCANONICAL_JSONL_RECORD")
                payload = row["payload"]
                _validate_event(
                    stream,
                    event_id=row["event_id"],
                    event_type=row["event_type"],
                    payload=payload,
                )
                records.append(row)
            except (UnicodeError, ValueError, TypeError, KeyError) as exc:
                raise sha_ledger.LedgerError(
                    f"INVALID_JSONL_RECORD_LINE_{line_number}: {exc}"
                ) from exc
        try:
            sha_ledger.verify(records)
        except (KeyError, TypeError, ValueError) as exc:
            raise sha_ledger.LedgerError(f"BROKEN_PAPER_SHA_CHAIN: {exc}") from exc
        return tuple(records)

    def read(self, stream: str) -> tuple[dict, ...]:
        data_path, lock_path = self._paths(stream)
        self.root.mkdir(parents=True, exist_ok=True)
        with _stream_lock(lock_path, exclusive=False):
            return self._read_unlocked(stream, data_path)

    def verify(self, stream: str, *, expected_head: str | None = None) -> str:
        records = self.read(stream)
        head = sha_ledger.verify(records)
        if expected_head is not None and head != expected_head:
            raise sha_ledger.LedgerError("EXTERNAL_HEAD_WITNESS_MISMATCH")
        return head

    def verify_all(self, *, expected_heads: dict[str, str] | None = None) -> dict[str, str]:
        expected_heads = expected_heads or {}
        return {
            stream: self.verify(stream, expected_head=expected_heads.get(stream))
            for stream in STREAM_PREFIXES
        }

    def append(
        self, stream: str, *, event_id: str, event_type: str, payload: dict
    ) -> dict:
        value = _validate_event(
            stream, event_id=event_id, event_type=event_type, payload=payload
        )
        data_path, lock_path = self._paths(stream)
        self.root.mkdir(parents=True, exist_ok=True)
        with _stream_lock(lock_path, exclusive=True):
            previous = list(self._read_unlocked(stream, data_path))
            updated = sha_ledger.extend(
                previous, event_id=event_id, event_type=event_type, payload=value
            )
            record = updated[-1]
            encoded = sha_ledger.canonical(record) + b"\n"
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            first_create = not data_path.exists()
            fd = os.open(data_path, flags, 0o600)
            try:
                offset = 0
                while offset < len(encoded):
                    written = os.write(fd, encoded[offset:])
                    if written <= 0:
                        raise sha_ledger.LedgerError("SHORT_JOURNAL_WRITE")
                    offset += written
                os.fsync(fd)
            finally:
                os.close(fd)
            if first_create:
                dir_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            return record
