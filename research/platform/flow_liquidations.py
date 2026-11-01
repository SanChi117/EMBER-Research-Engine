"""Binance public USD-M liquidation websocket snapshots; read-only.

Only latest one liquidation per symbol / 1000ms is broadcast by Binance.
PONG-confirmed uptime heartbeat; unavailable WS => LIQ_SNAPSHOT_PARTIAL.
Runtime requires optional websocket-client installed separately.
"""
from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .flow_collector import symbols_from_config
from .flow_ledger import FlowStore

WS_BASE = "wss://fstream.binance.com/market/stream?streams="
SOURCE = "wss://fstream.binance.com/market/stream"
MINUTE_MS = 60_000


class LiquidationSchemaDrift(ValueError):
    pass


def ws_url(symbols: tuple[str, ...]) -> str:
    if not symbols or not all(s.endswith("USDT") and s.isalnum() for s in symbols):
        raise LiquidationSchemaDrift("UNAPPROVED_LIQ_SYMBOL")
    return WS_BASE + "/".join(symbol.lower() + "@forceOrder" for symbol in symbols)


def _decimal(value: object) -> str:
    if type(value) is not str:
        raise LiquidationSchemaDrift("LIQ_NONSTRING_DECIMAL")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise LiquidationSchemaDrift("LIQ_INVALID_DECIMAL") from exc
    if not number.is_finite() or number < 0:
        raise LiquidationSchemaDrift("LIQ_INVALID_DECIMAL")
    return format(number, "f")


def force_order_from_message(message: dict, symbols: tuple[str, ...],
                             *, observed_at_ms: int) -> tuple[str, dict]:
    if type(message) is not dict or type(message.get("data")) is not dict:
        raise LiquidationSchemaDrift("LIQ_NOT_COMBINED_STREAM")
    raw = message["data"]
    order = raw.get("o")
    if raw.get("e") != "forceOrder" or type(order) is not dict:
        raise LiquidationSchemaDrift("LIQ_EVENT_SCHEMA_CHANGED")
    symbol = order.get("s")
    if symbol not in symbols or message.get("stream") != symbol.lower() + "@forceOrder":
        raise LiquidationSchemaDrift("LIQ_SYMBOL_STREAM_MISMATCH")
    if raw.get("st", 1) != 1:
        raise LiquidationSchemaDrift("NOT_USD_M_LIQUIDATION")
    side = order.get("S")
    if side not in ("BUY", "SELL"):
        raise LiquidationSchemaDrift("LIQ_INVALID_SIDE")
    ev_time = raw.get("E")
    trade_time = order.get("T")
    if (type(ev_time) is not int or type(trade_time) is not int
        or ev_time <= 0 or trade_time <= 0
        or ev_time > observed_at_ms + 120_000):
        raise LiquidationSchemaDrift("LIQ_INVALID_PROVIDER_TIME")
    payload = {
        "symbol": symbol, "observed_at_ms": observed_at_ms,
        "source": SOURCE + "#" + message["stream"],
        "event_time_ms": ev_time, "trade_time_ms": trade_time, "side": side,
        "price": _decimal(order.get("p")),
        "average_price": _decimal(order.get("ap")),
        "quantity": _decimal(order.get("q")),
        "last_filled_quantity": _decimal(order.get("l")),
        "accumulated_filled_quantity": _decimal(order.get("z")),
        "provider_semantics": "LATEST_ONE_SNAPSHOT_PER_SYMBOL_PER_1000MS",
    }
    return f"liq:{symbol}:{ev_time}:{trade_time}:{side}", payload


def mark_partial(store: FlowStore, *, observed_at_ms: int, reason: str) -> None:
    store.append(
        "liquidations", event_id=f"liq:partial:{observed_at_ms}",
        event_type="LIQ_SNAPSHOT_PARTIAL",
        payload={"symbol": "*", "source": SOURCE,
                 "observed_at_ms": observed_at_ms, "reason": reason,
                 "coverage": "NOT_A_COMPLETE_LIQUIDATION_TAPE"},
    )


def run_liquidation_stream(store: FlowStore, symbols: tuple[str, ...]) -> None:
    try:
        import websocket
    except ImportError as exc:
        mark_partial(store, observed_at_ms=int(time.time() * 1000),
                     reason="WEBSOCKET_CLIENT_NOT_INSTALLED_NO_PUBLIC_REST_TAPE")
        raise RuntimeError("LIQ_SNAPSHOT_PARTIAL: websocket-client missing") from exc

    endpoint = ws_url(symbols)
    while True:
        now = int(time.time() * 1000)
        store.append("liquidations", event_id=f"liq:restart:{now}",
                     event_type="COLLECTOR_RESTART",
                     payload={"symbol": "*", "source": endpoint,
                              "observed_at_ms": now,
                              "reason": "WEBSOCKET_SESSION_START_OR_RECONNECT"})
        try:
            ws = websocket.create_connection(endpoint, timeout=45,
                                             enable_multithread=True)
            try:
                ws.ping(b"ember-collector-ping")
                next_ping = time.monotonic() + 30
                confirmed_minutes = set()
                while True:
                    now = int(time.time() * 1000)
                    if time.monotonic() >= next_ping:
                        ws.ping(b"ember-collector-ping")
                        next_ping = time.monotonic() + 30
                    try:
                        opcode, body = ws.recv_data(control_frame=True)
                    except websocket.WebSocketTimeoutException:
                        ws.ping(b"ember-collector-ping")
                        next_ping = time.monotonic() + 30
                        continue
                    now = int(time.time() * 1000)
                    if opcode == websocket.ABNF.OPCODE_PONG:
                        minute = now // MINUTE_MS * MINUTE_MS
                        if minute not in confirmed_minutes:
                            store.append(
                                "liquidations",
                                event_id=f"liq:heartbeat:{minute}",
                                event_type="LIQ_HEARTBEAT",
                                payload={"symbol": "*", "source": endpoint,
                                         "observed_at_ms": now,
                                         "minute_slot_ms": minute,
                                         "evidence": "WEBSOCKET_PONG_CONFIRMED"},
                            )
                            confirmed_minutes.add(minute)
                    elif opcode == websocket.ABNF.OPCODE_TEXT:
                        try:
                            packet = json.loads(body)
                            event_id, payload = force_order_from_message(
                                packet, symbols, observed_at_ms=now,
                            )
                        except (ValueError, TypeError, UnicodeError) as exc:
                            store.append(
                                "liquidations",
                                event_id=f"liq:drift:{now}",
                                event_type="SCHEMA_DRIFT",
                                payload={"symbol": "*", "source": endpoint,
                                         "observed_at_ms": now,
                                         "reason": str(exc)},
                            )
                            raise LiquidationSchemaDrift("HALT_LIQ_STREAM") from exc
                        try:
                            store.append("liquidations", event_id=event_id,
                                         event_type="LIQ_FORCE_ORDER",
                                         payload=payload)
                        except ValueError as exc:
                            if "DUPLICATE_FLOW_EVENT" not in str(exc):
                                raise
                    elif opcode == websocket.ABNF.OPCODE_CLOSE:
                        raise ConnectionError("BINANCE_WEBSOCKET_CLOSE")
            finally:
                ws.close()
        except LiquidationSchemaDrift:
            raise
        except (OSError, ConnectionError) as exc:
            stamp = int(time.time() * 1000)
            store.append(
                "liquidations", event_id=f"liq:gap:{stamp}",
                event_type="GAP",
                payload={"symbol": "*", "source": endpoint,
                         "observed_at_ms": stamp,
                         "reason": "WEBSOCKET_DISCONNECTED_" + type(exc).__name__},
            )
            time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/flows")
    args = parser.parse_args()
    run_liquidation_stream(FlowStore(Path(args.root)), symbols_from_config())


if __name__ == "__main__":
    main()
