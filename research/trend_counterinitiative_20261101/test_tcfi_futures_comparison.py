"""TCFI causal clocks, source parsing and future-label-exclusion unit tests."""
import math

import pandas as pd

from research.trend_counterinitiative_20261101.tcfi_futures_comparison import (
    SYMS, YEARS, MONTHS, COSTS, aggregate, seeded_ema, daily_direction,
    failed_counterinitiative, settle_funding, replay, summary, boot_week_difference,
)

def hourly_fixture(begin="2025-03-01",hours=24*100):
    idx=pd.date_range(begin,periods=hours,freq="1h",tz="UTC")
    rising=[100+i*.02 for i in range(hours)]
    return pd.DataFrame({
        "open":rising,"high":[x+.15 for x in rising],
        "low":[x-.15 for x in rising],"close":rising,"volume":[100.]*hours,
    },index=idx)


def test_universe_dates_and_fixed_costs():
    assert len(SYMS)==24
    assert YEARS==(2024,2025)
    assert MONTHS==tuple(range(3,12))
    assert COSTS=={"BASE":.004,"STRESS":.0065}


def test_daily_asof_previous_closed_day():
    d=aggregate(hourly_fixture(), "1D", 24)
    closes=d.close.tolist()
    e20=seeded_ema(closes,20)
    e50=seeded_ema(closes,50)
    original=daily_direction(d,pd.Timestamp("2025-05-20T04:00:00Z"),e20,e50)
    d2=d.copy()
    # A changed current incomplete day must not affect trend.
    d2.loc[pd.Timestamp("2025-05-20T00:00:00Z"),"close"]=1e12
    assert daily_direction(d2,pd.Timestamp("2025-05-20T04:00:00Z"),e20,e50)==original


def test_intraday_failed_break_must_reclaim_then_follow_through():
    hr=hourly_fixture(hours=48)
    end=hr.index[-1]+pd.Timedelta(hours=1)
    assert not failed_counterinitiative(hr,end,1)
    # Prior 6h lows ~100.7, create false break and then high recovery.
    t=hr.index[-4]
    low=float(hr.iloc[-10:-4].low.min())
    hr.loc[t,["low","close","high"]]=[low-.2,low+.02,low+.3]
    hr.loc[hr.index[-2],"close"]=low+.5
    assert failed_counterinitiative(hr,end,1)
    # Remove recovery; a break alone must not be "confirmed".
    hr.loc[hr.index[-2],"close"]=low-.6
    hr.loc[hr.index[-1],"close"]=low-.6
    assert not failed_counterinitiative(hr,end,1)


def test_aggregation_never_drops_missing_1h():
    h=hourly_fixture(hours=24)
    assert len(aggregate(h,"4h",4))==6
    assert len(aggregate(h,"1D",24))==1
    try:
        aggregate(h.drop(h.index[5]),"4h",4)
    except ValueError as e:
        assert "incomplete" in str(e)
    else:
        raise AssertionError("future candle loss not detected")


def test_funding_direction_actual_settlements():
    stamps=[1_000,2_000,3_000]
    rates=[.001,-.002,.003]
    assert math.isclose(settle_funding(stamps,rates,1000,3000,1),-.002)
    assert math.isclose(settle_funding(stamps,rates,1000,3000,-1),+.002)


def test_exit_replay_stop_without_lookahead():
    h=hourly_fixture(hours=24*8)
    f=aggregate(h,"4h",4)
    start=f.index[12]
    entry={"entry_time":start,"stop":float(h.open.loc[start])-1.,
           "direction":1,"atr":1.,"depth_atr":.7,"impulse_atr":2}
    r=replay(f,h,entry,[],[],h.index[-1]+pd.Timedelta(hours=1))
    assert r is not None
    assert r["exit_time"]>=start
    assert r["entry_price"]==float(h.open.loc[start])
    assert r["risk_fraction"]>0


def test_week_cluster_omits_open_trades():
    row={"closed":True,"entry_time":"2025-07-01T04:00:00+00:00",
         "year":2025,"confirmed_1h":True,
         "STRESS_net_pct":2.,"STRESS_net_R":1.}
    rows=[row,dict(row,closed=False)]
    assert summary(rows,"STRESS",True)["n"]==1
    assert summary(rows,"STRESS",False)["n"]==2
    assert boot_week_difference(rows,"STRESS")["status"]=="LOW_POWER"
