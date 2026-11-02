"""RESET-07: frozen prereg, tamper refusal, chop, budget skip, determinism."""
from __future__ import annotations

from decimal import Decimal as D
from pathlib import Path

import pytest

from research.convex_runner import backtest as bt
from research.convex_runner.data_contract import DataIntegrityFailure, load_raw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research/convex_runner/raw"


def test_chop_veto_strict_20th_percentile_and_narrow_30d():
    ratios = [D("0.01")] * bt.YEAR_WINDOW
    assert bt.is_chop(D("0.001"), ratios, D("105"), D("100"), D("104"))
    assert not bt.is_chop(D("0.02"), ratios, D("105"), D("100"), D("104"))
    assert not bt.is_chop(D("0.001"), ratios, D("125"), D("100"), D("104"))


def test_raw_data_tamper_refused_even_on_valid_altered_json(tmp_path):
    from hashlib import sha256

    data = (DATA / "SOLUSDT_4h.json").read_bytes()
    trusted = sha256(data).hexdigest()
    target = tmp_path / "SOLUSDT_4h.json"
    target.write_bytes(data)
    rows, meta = load_raw(tmp_path, "SOLUSDT", "4h", expected_sha=trusted)
    assert rows and meta["sha256"] == trusted
    target.write_bytes(data.replace(b"101.7750", b"101.7751", 1))
    with pytest.raises(DataIntegrityFailure, match="RAW_SHA256_MISMATCH"):
        load_raw(tmp_path, "SOLUSDT", "4h", expected_sha=trusted)


def test_skipped_budget_when_six_concurrent_tickets(monkeypatch):
    bars = [
        bt.Bar(bt.START, D("100"), D("102"), D("98"), D("100")),
        bt.Bar(bt.START + bt.STEP, D("100"), D("102"), D("98"), D("100")),
    ]
    portfolio = {name: bars for name in bt.SYMBOLS}
    def alarm(_bars, _side):
        return {bt.START: {"stop": D("80"), "signal_time": bt.START - bt.STEP,
                           "pivot": D("80")}}
    monkeypatch.setattr(bt, "prepare_signals", alarm)
    result = bt.run_one(portfolio, side="LONG", fraction=D("0.01"))
    assert result["skipped_budget"] == 4
    assert result["trades"] == 6
    assert not result["kill_touch"]


def test_position_size_is_decimal_bounded():
    ticket = bt.size_ticket(
        equity=D("920"), risk_fraction=D("0.01"), entry=D("100"),
        stop=D("90"), sign=1, reserved=D("0"), open_count=0,
    )
    assert ticket is not None
    q, risk = ticket
    assert isinstance(q, D)
    assert q * D("100") <= D("920") * D("15")
    assert risk <= D("9.2")
    assert bt.size_ticket(
        equity=D("920"), risk_fraction=D("0.01"), entry=D("100"),
        stop=D("90"), sign=1, reserved=D("0"), open_count=6,
    ) is None


def test_simulation_identical_for_same_input_without_randomness():
    bars = [
        bt.Bar(bt.START + i * bt.STEP, D("100"), D("101"), D("99"), D("100"))
        for i in range(4)
    ]
    portfolio = {name: bars for name in bt.SYMBOLS}
    a = bt.run_one(portfolio, side="SHORT", fraction=D("0.02"))
    b = bt.run_one(portfolio, side="SHORT", fraction=D("0.02"))
    assert a == b
    assert not hasattr(bt, "place_order")


def test_runner_stop_and_be_fee_levels_are_direction_safe():
    long_be = bt._be_price(D("100"), 1)
    short_be = bt._be_price(D("100"), -1)
    assert long_be > D("100")
    assert short_be < D("100")
    long_p = {"q": D("1"), "entry": D("100"), "sign": 1}
    short_p = {"q": D("1"), "entry": D("100"), "sign": -1}
    assert abs(bt._net_pnl(long_p, long_be)) < D("0.00000000000000000001")
    assert abs(bt._net_pnl(short_p, short_be)) < D("0.00000000000000000001")
