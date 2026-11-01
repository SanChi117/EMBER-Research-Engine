"""R030 continuous research: fixture controls for source, wallet continuity and accounting."""
import hashlib
from datetime import datetime, timezone

import pytest

from research.r030_continuous_20261101.prepare_original_continuous import (
    COINS, START, END_EXCL, as_ms, blob_sha, month_iterator,
)
from research.r030_continuous_20261101.run_original_continuous import (
    BLOB, FEES, PERIOD, git_sha, report_from_original,
)


def fixture():
    a={
        "open_date":"2023-10-20 00:00:00+00:00",
        "close_date":"2024-01-03 00:00:00+00:00",
        "exit_reason":"exit_signal",
        "profit_abs":-6.0,"leverage":2.0,
        "orders":[{"ft_order_side":"buy"}],
    }
    b={
        "open_date":"2026-01-02 00:00:00+00:00",
        "close_date":"2026-05-31 22:00:00+00:00",
        "exit_reason":"force_exit",
        "profit_abs":12.0,"leverage":2.0,
        "orders":[{"ft_order_side":"buy"}],
    }
    return {"strategy":{"VolatilitySystem":{
        "trades":[a,b],"total_trades":2,"profit_total_abs":6.0,
        "exit_reason_summary":[
            {"key":"exit_signal","trades":1,"profit_total_abs":-6.0},
            {"key":"force_exit","trades":1,"profit_total_abs":12.0},
            {"key":"TOTAL","trades":2,"profit_total_abs":6.0},
        ],
    }}}


def test_frozen_original_and_complete_months():
    assert COINS==("BTCUSDT","ETHUSDT","SOLUSDT")
    assert START==(2023,5) and END_EXCL==(2026,6)
    assert len(list(month_iterator()))==37
    assert len(list(month_iterator()))*len(COINS)*3==333
    assert PERIOD=="20230601-20260601"
    assert FEES=={"BASE":.0005,"STRESS":.0011}
    assert BLOB=="15ce2473f3f60bd33c4a67b0b8b228e379850f19"


def test_genuine_zip_source_date_including_2023_may():
    assert as_ms("1682899200000")==1682899200000
    assert as_ms("1682899200000000")==1682899200000
    with pytest.raises(ValueError,match="range"):
        as_ms("123")


def test_unchanged_source_git_blob_composition():
    raw=b"abc\n"
    expected=hashlib.sha1(b"blob 4\x00abc\n").hexdigest()
    assert git_sha(raw)==expected
    assert blob_sha(raw)==expected


def test_continuous_wallet_across_december_no_annual_force_exit():
    r=report_from_original(fixture(),"native.zip","STRESS",.0011)
    assert r["net_account_return_pct"]==.6
    assert r["positions_open_across_dec31_2023_2024_2025"][2023]==1
    assert r["only_final_end_force_exit_pnl_usdt"]==12
    assert r["non_terminal_exits_pnl_usdt"]==-6
    assert r["only_final_end_force_exit_count"]==1


def test_reject_force_exit_at_year_end_before_final():
    obj=fixture()
    obj["strategy"]["VolatilitySystem"]["trades"][0]["exit_reason"]="force_exit"
    obj["strategy"]["VolatilitySystem"]["exit_reason_summary"]=[
        {"key":"force_exit","trades":2,"profit_total_abs":6.0},
    ]
    with pytest.raises(ValueError,match="FORCED_EXIT_INSIDE_CONTINUOUS_ACCOUNT"):
        report_from_original(obj,"native.zip","BASE",.0005)


def test_missing_native_order_details_not_accepted():
    obj=fixture()
    obj["strategy"]["VolatilitySystem"]["trades"][0]["orders"]=[]
    with pytest.raises(ValueError,match="orders missing"):
        report_from_original(obj,"native.zip","BASE",.0005)


def test_nonreconciling_native_exit_amount_not_accepted():
    obj=fixture()
    obj["strategy"]["VolatilitySystem"]["exit_reason_summary"][0]["profit_total_abs"]=-16.
    with pytest.raises(ValueError,match="PnL does not reconcile"):
        report_from_original(obj,"native.zip","BASE",.0005)
