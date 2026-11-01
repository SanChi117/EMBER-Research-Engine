"""Original Binance USD-M monthly kline parser: no substitution or future stamps."""
from datetime import datetime, timezone

import pytest

from scripts.collect_initiative_oos_2025 import (
    FOUR_MONTHS,
    ONE_MONTHS,
    SYMBOLS,
    parse_source,
)


def make_line(month="2025-06"):
    ms=int(datetime.fromisoformat(month+"-01T00:00:00+00:00").timestamp()*1000)
    return (
        str(ms)+",100,105,95,102,1000,"+str(ms+3599999)
        +",101000,42,490,49490,0\n"
    ).encode()


def test_frozen_12_usdm_contracts_and_periods():
    assert len(SYMBOLS)==12
    assert len(set(SYMBOLS))==12
    assert FOUR_MONTHS[0]=="2025-01"
    assert FOUR_MONTHS[-1]=="2025-08"
    assert ONE_MONTHS==("2025-06","2025-07","2025-08")


def test_read_kline_no_header_or_binance_header():
    raw=make_line()
    row=parse_source(raw,"BTCUSDT","1h","2025-06")[0]
    assert row["symbol"]=="BTCUSDT"
    assert row["taker_buy_base"]=="490"
    assert row["volume"]=="1000"
    assert parse_source(
        b"open_time,open,high,low,close,volume,close_time,quote,"
        b"trades,taker_buy_base,taker_buy_quote,ignore\n"+raw,
        "BTCUSDT","1h","2025-06",
    )==[row]


def test_wrong_month_and_malformed_candles_fail_closed():
    with pytest.raises(ValueError,match="wrong venue"):
        parse_source(make_line(),"BTCUSDT","1h","2025-07")
    with pytest.raises(ValueError,match="invalid source"):
        parse_source(
            make_line().replace(b",100,105,95,102",b",100,99,95,102"),
            "BTCUSDT","1h","2025-06",
        )
