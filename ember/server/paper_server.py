"""FastAPI paper-trading journal. Virtual trades only."""

from __future__ import annotations

import csv
import io
import sqlite3
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, model_validator

SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    setup_type TEXT,
    entry_time TEXT,
    exit_time TEXT,
    entry_price REAL,
    stop_price REAL,
    target_price REAL,
    planned_rr REAL,
    result_r REAL,
    exit_reason TEXT,
    bars_held INTEGER,
    mfe_r REAL,
    mae_r REAL,
    status TEXT DEFAULT 'open',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class PaperWebhook(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["open", "close"]
    trade_id: int | None = None
    symbol: str | None = None
    side: Literal["long", "short"] | None = None
    setup_type: str | None = None
    entry_time: str | None = None
    exit_time: str | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    planned_rr: float | None = None
    result_r: float | None = None
    exit_reason: str | None = None
    bars_held: int = 0
    mfe_r: float = 0.0
    mae_r: float = 0.0

    @model_validator(mode="after")
    def validate_action_fields(self) -> "PaperWebhook":
        if self.action == "open":
            required = {
                "symbol": self.symbol,
                "side": self.side,
                "setup_type": self.setup_type,
                "entry_time": self.entry_time,
                "entry_price": self.entry_price,
                "stop_price": self.stop_price,
                "target_price": self.target_price,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(f"open action missing fields: {missing}")
        elif self.trade_id is None:
            raise ValueError("close action requires trade_id")
        return self


class PaperStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def open_trade(self, payload: PaperWebhook) -> int:
        planned_rr = payload.planned_rr
        if planned_rr is None:
            assert payload.entry_price is not None
            assert payload.stop_price is not None
            assert payload.target_price is not None
            risk = abs(payload.entry_price - payload.stop_price)
            planned_rr = abs(payload.target_price - payload.entry_price) / risk if risk > 0 else 0.0
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paper_trades (
                    symbol, side, setup_type, entry_time, entry_price,
                    stop_price, target_price, planned_rr, bars_held, mfe_r, mae_r, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
                """,
                (
                    payload.symbol,
                    payload.side,
                    payload.setup_type,
                    payload.entry_time,
                    payload.entry_price,
                    payload.stop_price,
                    payload.target_price,
                    planned_rr,
                    payload.bars_held,
                    payload.mfe_r,
                    payload.mae_r,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def close_trade(self, payload: PaperWebhook) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE paper_trades
                SET exit_time = ?, result_r = ?, exit_reason = ?, bars_held = ?,
                    mfe_r = ?, mae_r = ?, status = 'closed'
                WHERE id = ? AND status = 'open'
                """,
                (
                    payload.exit_time,
                    payload.result_r,
                    payload.exit_reason,
                    payload.bars_held,
                    payload.mfe_r,
                    payload.mae_r,
                    payload.trade_id,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

    def status(self) -> dict[str, float | int]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN result_r > 0 THEN 1 ELSE 0 END) AS wins,
                    AVG(CASE WHEN status = 'closed' THEN result_r END) AS avg_r
                FROM paper_trades
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "wins": int(row["wins"] or 0),
            "avg_r": float(row["avg_r"] or 0.0),
        }

    def trades(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM paper_trades ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def all_trades(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM paper_trades ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def create_app(db_path: Path | str = Path("paper_trades.db")) -> FastAPI:
    store = PaperStore(Path(db_path))
    app = FastAPI(title="EMBER Paper Server", version="0.2.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "virtual_only"}

    @app.get("/status")
    def status() -> dict[str, float | int]:
        return store.status()

    @app.get("/trades")
    def trades(limit: int = Query(default=20, ge=1, le=1000)) -> list[dict[str, Any]]:
        return store.trades(limit)

    @app.get("/export/trades.csv")
    def export_trades() -> StreamingResponse:
        rows = store.all_trades()
        buffer = io.StringIO()
        if rows:
            writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        response = StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=paper_trades.csv"
        return response

    @app.post("/paper-webhook")
    def paper_webhook(payload: PaperWebhook) -> dict[str, Any]:
        if payload.action == "open":
            trade_id = store.open_trade(payload)
            return {"status": "opened", "trade_id": trade_id, "mode": "virtual_only"}
        closed = store.close_trade(payload)
        if not closed:
            raise HTTPException(status_code=404, detail="open paper trade not found")
        return {"status": "closed", "trade_id": payload.trade_id, "mode": "virtual_only"}

    app.state.paper_store = store
    return app


app = create_app()
