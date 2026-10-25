"""ISO03 adapted Route C event-driven paper backtest. NOT an author strategy.

No optimization, live orders or trade-readiness promotion. Signals are technical
C56/ISO01 observations; execution, ATR stop, 2R target and costs are explicitly
adapted research assumptions. Conservative same-bar SL/TP handling: stop first.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
from typing import Iterable, Mapping

TF = 180_000
SCHEMA = "EMBER_ISO03_ADAPTED_ROUTE_C_PAPER_BACKTEST_V1"


@dataclass(frozen=True)
class Bar:
    open_ms: int
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        if self.open_ms < 0 or self.open_ms % TF:
            raise ValueError("ISO03_BAD_BAR_OPEN_GRID")
        values = (self.open, self.high, self.low, self.close)
        if any(not isinstance(x, (int, float)) or isinstance(x, bool) or x <= 0 for x in values):
            raise ValueError("ISO03_BAD_BAR_PRICE")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close) or self.low > self.high:
            raise ValueError("ISO03_INCONSISTENT_BAR")


@dataclass(frozen=True)
class Signal:
    parent_id: str
    symbol: str
    known_ms: int
    direction: int  # +1 long, -1 short
    child_timeframe: str

    def __post_init__(self):
        if not self.parent_id or not self.symbol or self.direction not in (-1, 1):
            raise ValueError("ISO03_BAD_SIGNAL")
        if self.known_ms < 0 or self.child_timeframe not in ("3m", "5m"):
            raise ValueError("ISO03_BAD_SIGNAL_KNOWLEDGE")


@dataclass(frozen=True)
class BacktestConfig:
    initial_equity: float = 100_000.0
    risk_fraction: float = 0.01
    max_leverage: float = 3.0
    atr_period: int = 14
    atr_stop_multiple: float = 1.5
    target_r: float = 2.0
    time_stop_bars: int = 120  # six hours on native 3m
    fee_rate: float = 0.0005
    slippage_rate: float = 0.0002

    def __post_init__(self):
        if self.initial_equity <= 0 or not 0 < self.risk_fraction <= 0.05:
            raise ValueError("ISO03_BAD_EQUITY_OR_RISK")
        if not 0 < self.max_leverage <= 10 or self.atr_period < 2:
            raise ValueError("ISO03_BAD_LEVERAGE_OR_ATR")
        if self.atr_stop_multiple <= 0 or self.target_r <= 0 or self.time_stop_bars < 1:
            raise ValueError("ISO03_BAD_EXIT_CONTRACT")
        if not 0 <= self.fee_rate < 0.01 or not 0 <= self.slippage_rate < 0.01:
            raise ValueError("ISO03_BAD_COSTS")


@dataclass
class Position:
    signal: Signal
    entry_ms: int
    entry: float
    quantity: float
    stop: float
    target: float
    entry_fee: float
    bars_held: int = 0


def _fee(price: float, qty: float, rate: float) -> float:
    return price * qty * rate


def _exit_price(raw: float, direction: int, config: BacktestConfig) -> float:
    # Adverse slippage: selling long lower, buying short higher.
    return raw * (1 - direction * config.slippage_rate)


def _metrics(trades: list[dict], equity_curve: list[dict], initial: float, skipped: int, signals: int) -> dict:
    pnl = [t["net_pnl"] for t in trades]
    gross_profit = math.fsum(x for x in pnl if x > 0)
    gross_loss = -math.fsum(x for x in pnl if x < 0)
    peak = initial
    max_dd = 0.0
    max_dd_ms = None
    for point in equity_curve:
        equity = point["equity"]
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak else 0.0
        if dd > max_dd:
            max_dd, max_dd_ms = dd, point["close_ms"]
    final = equity_curve[-1]["equity"] if equity_curve else initial
    return {
        "initial_equity": initial, "final_equity": final, "net_pnl": final - initial,
        "return_fraction": final / initial - 1, "signals": signals, "trades": len(trades),
        "skipped_signals": skipped, "wins": sum(x > 0 for x in pnl), "losses": sum(x < 0 for x in pnl),
        "win_rate": (sum(x > 0 for x in pnl) / len(pnl)) if pnl else None,
        "profit_factor": (gross_profit / gross_loss) if gross_loss else (None if not gross_profit else "INF"),
        "gross_profit": gross_profit, "gross_loss": gross_loss,
        "fees": math.fsum(t["entry_fee"] + t["exit_fee"] for t in trades),
        "max_drawdown_fraction": max_dd, "max_drawdown_close_ms": max_dd_ms,
    }


def run_backtest(bars_by_symbol: Mapping[str, list[Bar]], signals: Iterable[Signal],
                 config: BacktestConfig = BacktestConfig()) -> dict:
    if not bars_by_symbol or any(not bars for bars in bars_by_symbol.values()):
        raise ValueError("ISO03_EMPTY_MARKET")
    ordered_bars = {}
    for symbol, bars in bars_by_symbol.items():
        ordered = sorted(bars, key=lambda b: b.open_ms)
        if len({b.open_ms for b in ordered}) != len(ordered):
            raise ValueError("ISO03_DUPLICATE_BAR")
        if any(b.open_ms + TF != n.open_ms for b, n in zip(ordered, ordered[1:])):
            raise ValueError("ISO03_NONCONTIGUOUS_MARKET")
        ordered_bars[symbol] = ordered
    unique_signals = {}
    for s in signals:
        if s.symbol not in ordered_bars:
            raise ValueError("ISO03_SIGNAL_MARKET_MISMATCH")
        if s.parent_id in unique_signals and unique_signals[s.parent_id] != s:
            raise ValueError("ISO03_CONFLICTING_PARENT_SIGNAL")
        unique_signals[s.parent_id] = s
    signal_list = sorted(unique_signals.values(), key=lambda s: (s.known_ms, s.symbol, s.parent_id))
    by_symbol_signals = {symbol: [s for s in signal_list if s.symbol == symbol] for symbol in ordered_bars}
    indices = {symbol: 0 for symbol in ordered_bars}
    bar_indices = {symbol: {b.open_ms: i for i, b in enumerate(bars)}
                   for symbol, bars in ordered_bars.items()}
    positions: dict[str, Position] = {}
    trades: list[dict] = []
    equity_curve: list[dict] = []
    balance = config.initial_equity
    skipped = 0
    times = sorted({b.open_ms for bars in ordered_bars.values() for b in bars})

    def equity_at(price_map):
        return balance + math.fsum((price_map[s] - p.entry) * p.signal.direction * p.quantity
                                   for s, p in positions.items())

    for now in times:
        current = {symbol: bars[bar_indices[symbol][now]] for symbol, bars in ordered_bars.items()
                   if now in bar_indices[symbol]}
        # All signals whose knowledge time has passed are either executed now or
        # permanently skipped if the symbol was occupied. No look-ahead queue.
        for symbol, bar in current.items():
            pending = []
            symbol_signals = by_symbol_signals[symbol]
            i = indices[symbol]
            while i < len(symbol_signals) and symbol_signals[i].known_ms <= now:
                pending.append(symbol_signals[i]); i += 1
            indices[symbol] = i
            if symbol in positions:
                skipped += len(pending)
                continue
            if not pending:
                continue
            signal = pending[0]
            skipped += len(pending) - 1
            idx = bar_indices[symbol][now]
            bars = ordered_bars[symbol]
            if idx < config.atr_period:
                skipped += 1
                continue
            previous = bars[idx - config.atr_period:idx]
            trs = []
            for j, b in enumerate(previous, start=idx - config.atr_period):
                prior_close = bars[j - 1].close
                trs.append(max(b.high - b.low, abs(b.high - prior_close), abs(b.low - prior_close)))
            atr = math.fsum(trs) / config.atr_period
            if atr <= 0:
                skipped += 1
                continue
            mark_equity = equity_at({s: b.open for s, b in current.items()})
            if mark_equity <= 0:
                skipped += 1
                continue
            entry = bar.open * (1 + signal.direction * config.slippage_rate)
            distance = atr * config.atr_stop_multiple
            risk_qty = mark_equity * config.risk_fraction / distance
            leverage_qty = mark_equity * config.max_leverage / entry
            qty = min(risk_qty, leverage_qty)
            if qty <= 0:
                skipped += 1
                continue
            stop = entry - signal.direction * distance
            target = entry + signal.direction * distance * config.target_r
            if stop <= 0:
                skipped += 1
                continue
            entry_fee = _fee(entry, qty, config.fee_rate)
            balance -= entry_fee
            positions[symbol] = Position(signal, now, entry, qty, stop, target, entry_fee)

        # Existing and just-opened positions see this bar's range. If both levels
        # occur inside one bar, stop wins because intrabar order is unknowable.
        for symbol in list(positions):
            if symbol not in current:
                continue
            p = positions[symbol]; bar = current[symbol]; direction = p.signal.direction
            p.bars_held += 1
            reason = None; raw_exit = None
            stop_hit = bar.low <= p.stop if direction == 1 else bar.high >= p.stop
            target_hit = bar.high >= p.target if direction == 1 else bar.low <= p.target
            if stop_hit:
                reason = "STOP_SAME_BAR_PRIORITY" if target_hit else "STOP"
                gap_through = bar.open < p.stop if direction == 1 else bar.open > p.stop
                raw_exit = bar.open if gap_through else p.stop
            elif target_hit:
                reason, raw_exit = "TARGET", p.target
            elif p.bars_held >= config.time_stop_bars:
                reason, raw_exit = "TIME_STOP", bar.close
            elif now == times[-1]:
                reason, raw_exit = "SOURCE_END", bar.close
            if reason is None:
                continue
            exit_price = _exit_price(raw_exit, direction, config)
            exit_fee = _fee(exit_price, p.quantity, config.fee_rate)
            gross = (exit_price - p.entry) * direction * p.quantity
            balance += gross - exit_fee
            trades.append({
                "parent_id": p.signal.parent_id, "symbol": symbol, "direction": "LONG" if direction == 1 else "SHORT",
                "child_timeframe": p.signal.child_timeframe, "signal_known_ms": p.signal.known_ms,
                "entry_ms": p.entry_ms, "exit_ms": now + TF, "entry": p.entry, "exit": exit_price,
                "quantity": p.quantity, "stop": p.stop, "target": p.target, "bars_held": p.bars_held,
                "exit_reason": reason, "gross_pnl_after_slippage": gross,
                "entry_fee": p.entry_fee, "exit_fee": exit_fee, "net_pnl": gross - p.entry_fee - exit_fee,
            })
            del positions[symbol]
        close_prices = {s: b.close for s, b in current.items()}
        equity_curve.append({"close_ms": now + TF, "equity": equity_at(close_prices),
                             "open_positions": len(positions), "balance": balance})

    result = {
        "schema": SCHEMA, "mode": "ADAPTED_ROUTE_C_PAPER_ONLY", "author_strategy_certified": False,
        "config": asdict(config), "execution_contract": {
            "entry": "NEXT_NATIVE_3M_OPEN_AT_OR_AFTER_SIGNAL_KNOWN",
            "stop": "ATR14_SIMPLE_MEAN_TRUE_RANGE_TIMES_1_5_FROM_ENTRY",
            "target": "2R", "time_stop": "120_NATIVE_3M_BARS",
            "same_bar_stop_target": "STOP_FIRST_CONSERVATIVE",
            "one_position_per_symbol": True, "signals_while_occupied": "SKIPPED_NOT_QUEUED",
            "funding": "EXCLUDED", "liquidation": "NOT_MODELED", "margin_borrow": "NOT_MODELED",
        },
        "metrics": _metrics(trades, equity_curve, config.initial_equity, skipped, len(signal_list)),
        "trades_detail": trades, "equity_curve": equity_curve,
        "readiness": "NOT_TRADE_READY", "orders_live": 0,
    }
    return result


def load_binance_daily_zips(data_dir: Path) -> tuple[dict[str, list[Bar]], dict]:
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    bars: dict[str, list[Bar]] = {}
    for name, receipt in sorted(manifest.items()):
        raw = (data_dir / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt["sha256"] or len(raw) != receipt["bytes"]:
            raise ValueError("ISO03_SOURCE_ARCHIVE_INTEGRITY")
        symbol = name.split("-", 1)[0]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members = z.namelist()
            if len(members) != 1:
                raise ValueError("ISO03_UNEXPECTED_ZIP_CONTENT")
            rows = list(csv.DictReader(io.StringIO(z.read(members[0]).decode())))
        if len(rows) != 480:
            raise ValueError("ISO03_INCOMPLETE_DAILY_SOURCE")
        for row in rows:
            close_ms = int(row["close_time"]) + 1
            open_ms = int(row["open_time"])
            if close_ms != open_ms + TF:
                raise ValueError("ISO03_BAD_ORIGINAL_CLOSE_TIME")
            bars.setdefault(symbol, []).append(Bar(open_ms, float(row["open"]), float(row["high"]),
                                                   float(row["low"]), float(row["close"])))
    for symbol, values in bars.items():
        values.sort(key=lambda b: b.open_ms)
        if len(values) != 15360:
            raise ValueError("ISO03_INCOMPLETE_SYMBOL_SOURCE")
    return bars, manifest


def signals_from_iso01(document: Mapping) -> list[Signal]:
    if document.get("schema") != "EMBER_ISO01_FROZEN_C56_PARENT_OBJECT_STATE_REGISTRY_V1":
        raise ValueError("ISO03_ISO01_SCHEMA")
    signals = []
    for state in document["parent_states"]:
        p = state["parent"]
        candidates = [(p["original_3m_bos_known_ms"], "3m"), (p["original_5m_bos_known_ms"], "5m")]
        known, tf = min((x for x in candidates if x[0] is not None), key=lambda x: (x[0], x[1]))
        direction = -1 if p["raid_type"] == "BSL" else 1
        signals.append(Signal(state["parent_id"], p["symbol"], known, direction, tf))
    return signals


def canonical_bytes(result: Mapping) -> bytes:
    return (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
