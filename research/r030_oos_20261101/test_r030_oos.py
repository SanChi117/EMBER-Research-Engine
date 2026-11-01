"""R030 future holdout freeze and native risk-result record checks."""
import pytest

from research.r030_oos_20261101.r030_prepare import MONTHS, SYMS, rows_candles
from research.r030_oos_20261101.r030_run_oos import BLOB, git_blob, summarize


def test_frozen_holdout_precedes_any_outcome():
    assert MONTHS == tuple((2023,m) for m in range(5,11))
    assert SYMS == ("BTCUSDT","ETHUSDT","SOLUSDT")
    assert BLOB == "15ce2473f3f60bd33c4a67b0b8b228e379850f19"


def test_candle_month_and_utc_rejection():
    raw=[["1685577600000","100","105","95","102","50"]]
    assert len(rows_candles(raw,("kline","BTCUSDT",2023,6)))==1
    with pytest.raises(ValueError,match="unexpected candle month"):
        rows_candles(raw,("kline","BTCUSDT",2023,7))


def test_unmodified_source_sha():
    assert git_blob(b"test\n") == "9daeafb9864cf43055ae93beb0afd6c7d144bfa4"


def test_trade_records_must_reconcile_to_native_count():
    base={"strategy":{"VolatilitySystem":{
        "profit_total_abs":50,
        "total_trades":2,"trades":[{"leverage":2.0,"orders":[1,2]}],
    }}}
    with pytest.raises(ValueError,match="full native trade evidence missing"):
        summarize(base,"fixture",0.0011)


def test_no_verified_label_even_for_positive_native_backtest():
    base={"strategy":{"VolatilitySystem":{
        "profit_total_abs":50,
        "total_trades":1,
        "trades":[{"leverage":2.0,"orders":[1,2]}],
    }}}
    result=summarize(base,"fixture",0.0011)
    assert result["native_after_fee_return_pct"]==5.0
    assert "UNVERIFIED_LIQUIDATION" in result["status"]
