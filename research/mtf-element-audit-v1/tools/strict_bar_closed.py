#!/usr/bin/env python3
"""D01 v1.0: fail-closed exchange bar contract, independent of trading engine.

Explicitly does not authenticate provenance or produce trading signals.
This validates each bar's schema, timestamp grid, point-in-time availability
and file continuity. Market/type comes from caller-provided provenance, which
must be authenticated by a *separate* D04 source gate.
"""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator

TF_MS = {'3m':180_000, '5m':300_000, '15m':900_000,
         '1h':3_600_000, '4h':14_400_000, '1d':86_400_000,
         '1w':604_800_000}
UTC_WEEK_ANCHOR_MS = 4 * 86_400_000  # 1970-01-05 Monday 00:00 UTC
REQUIRED = ('open_time', 'close_time', 'open', 'high', 'low', 'close', 'volume', 'symbol')
SYMBOL_RE = re.compile(r'[A-Z0-9]{4,30}\Z')
INTEGRITY_RE = re.compile(r'[0-9a-f]{64}\Z')

class D01Rejected(ValueError):
    def __init__(self, code: str, detail: str = ''):
        self.code = code
        super().__init__(code + (': ' + detail if detail else ''))

@dataclass(frozen=True)
class Provenance:
    exchange: str
    market_type: str
    symbol: str
    timeframe: str
    source_description: str
    expected_csv_sha256: str

    def validate(self):
        if self.exchange != 'BINANCE':
            raise D01Rejected('EXCHANGE_NOT_SUPPORTED', self.exchange)
        if self.market_type != 'FUTURES_UM':
            raise D01Rejected('WRONG_MARKET_TYPE', self.market_type)
        if self.timeframe not in TF_MS:
            raise D01Rejected('UNKNOWN_TIMEFRAME', self.timeframe)
        if not SYMBOL_RE.fullmatch(self.symbol):
            raise D01Rejected('BAD_SYMBOL')
        if not self.source_description or not self.source_description.strip():
            raise D01Rejected('SOURCE_NOT_DECLARED')
        if not INTEGRITY_RE.fullmatch(self.expected_csv_sha256):
            raise D01Rejected('MISSING_OR_BAD_FILE_DIGEST')

@dataclass(frozen=True)
class ClosedBar:
    symbol: str
    timeframe: str
    open_at_ms: int
    close_exclusive_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def utc_ms(value):
    if isinstance(value, bool) or isinstance(value, float):
        raise D01Rejected('BAD_TIME_TYPE')
    if isinstance(value, int):
        result = value
    elif isinstance(value, str):
        if re.fullmatch(r'\d{13}', value):
            result = int(value)
        elif re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?(?:Z|\+00:00)', value):
            try:
                result = int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)
            except ValueError as exc:
                raise D01Rejected('BAD_UTC_TIME') from exc
        else:
            raise D01Rejected('AMBIGUOUS_OR_NON_UTC_TIME')
    else:
        raise D01Rejected('BAD_TIME_TYPE')
    if not (946684800000 <= result < 4102444800000):  # 2000-01-01 through 2100-01-01
        raise D01Rejected('TIME_OUT_OF_SUPPORTED_RANGE')
    return result


def finite_decimal(raw, key):
    if raw is None or isinstance(raw, bool) or not str(raw).strip():
        raise D01Rejected('MISSING_' + key.upper())
    try:
        out = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError) as exc:
        raise D01Rejected('INVALID_' + key.upper()) from exc
    if not out.is_finite():
        raise D01Rejected('NONFINITE_' + key.upper())
    return out


def verify_file_digest(path, expected):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    digest = h.hexdigest()
    if digest != expected:
        raise D01Rejected('CSV_DIGEST_MISMATCH', 'expected ' + expected + ', got ' + digest)
    return digest


def read_closed_bars(path: str | Path, provenance: Provenance, *, as_of_utc, require_contiguous=True) -> list[ClosedBar]:
    provenance.validate()
    as_of = utc_ms(as_of_utc)
    path = Path(path)
    verify_file_digest(path, provenance.expected_csv_sha256)
    period = TF_MS[provenance.timeframe]
    anchor = UTC_WEEK_ANCHOR_MS if provenance.timeframe == '1w' else 0
    bars = []
    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise D01Rejected('EMPTY_OR_NO_HEADER')
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise D01Rejected('DUPLICATE_CSV_HEADER')
        missing = set(REQUIRED).difference(reader.fieldnames)
        if missing:
            raise D01Rejected('MISSING_COLUMNS', ','.join(sorted(missing)))
        for n, row in enumerate(reader, start=2):
            if None in row:
                raise D01Rejected('CSV_EXTRA_FIELDS', 'row ' + str(n))
            for key in REQUIRED:
                if row.get(key) is None or not str(row[key]).strip():
                    raise D01Rejected('MISSING_' + key.upper(), 'row ' + str(n))
            if row['symbol'] != provenance.symbol:
                raise D01Rejected('SYMBOL_MISMATCH', 'row ' + str(n))
            open_ms = utc_ms(row['open_time'])
            if (open_ms - anchor) % period:
                raise D01Rejected('OFF_TIMEFRAME_GRID', 'row ' + str(n))
            close_ms = utc_ms(row['close_time'])
            if close_ms != open_ms + period - 1:
                raise D01Rejected('INCONSISTENT_CLOSE_TIME', 'row ' + str(n))
            if open_ms + period > as_of:
                raise D01Rejected('NOT_CLOSED_AS_OF', 'row ' + str(n))
            o, h, l, c, v = tuple(finite_decimal(row[key], key) for key in ('open', 'high', 'low', 'close', 'volume'))
            if min(o, h, l, c) <= 0 or v < 0 or h < max(o, l, c) or l > min(o, c, h):
                raise D01Rejected('INVALID_OHLCV', 'row ' + str(n))
            if bars:
                previous = bars[-1].open_at_ms
                if open_ms <= previous:
                    raise D01Rejected('UNSORTED_OR_DUPLICATE_TIMESTAMP', 'row ' + str(n))
                if require_contiguous and open_ms - previous != period:
                    raise D01Rejected('MISSING_BARS', 'row ' + str(n))
            bars.append(ClosedBar(provenance.symbol, provenance.timeframe, open_ms,
                                  open_ms + period, o, h, l, c, v))
    if not bars:
        raise D01Rejected('ZERO_BARS')
    return bars