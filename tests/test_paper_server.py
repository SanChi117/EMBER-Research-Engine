from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ember.server.paper_server import create_app


def test_virtual_paper_server_lifecycle(tmp_path: Path) -> None:
    db_path = tmp_path / "paper.db"
    client = TestClient(create_app(db_path))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "mode": "virtual_only"}

    opened = client.post(
        "/paper-webhook",
        json={
            "action": "open",
            "symbol": "DOGEUSDT",
            "side": "short",
            "setup_type": "pullback",
            "entry_time": "2024-01-01T00:00:00+00:00",
            "entry_price": 100.0,
            "stop_price": 101.0,
            "target_price": 98.2,
        },
    )
    assert opened.status_code == 200
    trade_id = opened.json()["trade_id"]

    closed = client.post(
        "/paper-webhook",
        json={
            "action": "close",
            "trade_id": trade_id,
            "exit_time": "2024-01-01T01:00:00+00:00",
            "result_r": 1.8,
            "exit_reason": "take_profit",
            "bars_held": 4,
            "mfe_r": 2.0,
            "mae_r": -0.2,
        },
    )
    assert closed.status_code == 200
    assert client.get("/status").json() == {"total": 1, "wins": 1, "avg_r": 1.8}
    assert len(client.get("/trades?limit=20").json()) == 1
    exported = client.get("/export/trades.csv")
    assert exported.status_code == 200
    assert "DOGEUSDT" in exported.text
