"""C20C independent 45-archive original source UTC diagnostics."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c20_original_5m_monthly_cross_15m import original_5m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c20_original_32day_native5m_lineage import reconcile_32day_native5m
from c20c_context_observations import review_calendar_context

def replay():
    result=[]
    for symbol in SYMS:
        originals={}
        for tf in ("15m","1d"):
            originals[tf]=tuple(load_original(symbol,tf,d,start)[0]
                                for d,start in zip(DATES,STARTS))
        prior=extended_32day_prefix(originals["15m"],originals["1d"],END)
        sources=tuple(original_5m(symbol,d)[0] for d in DATES)
        verified=reconcile_32day_native5m(sources,prior,as_of_ms=END)
        observed=review_calendar_context(verified,as_of_ms=END)
        assert observed.symbol==symbol
        assert observed.readiness=="NOT_TRADE_READY"
        result.append(observed)
    return tuple(result)

def to_json_rows(observed):
    return [{
        "symbol":x.symbol,
        "research_price_breaks":x.observed_breaks,
        "raid_pivot_same_utc_day":x.same_utc_day,
        "raid_pivot_previous_utc_day":x.previous_utc_day,
        "raid_pivot_older_utc_day":x.older_utc_day,
        "break_more_than_24h_after_confirmed_raid":x.more_than_24h_after_raid,
        "multiple_raid_parents_same_5m_bar_edges":x.coincident_break_parent_edges,
        "utc_bos_close_09_17_proxy":x.utc_9_17_proxy,
        "author_session_status":x.author_session_status,
        "author_fta_status":x.author_fta_status,
        "author_bos_status":x.author_bos_status,
        "readiness":x.readiness
    } for x in observed]

def result():
    data=to_json_rows(replay())
    assert len(data)==5
    assert sum(x["research_price_breaks"] for x in data)==512
    assert all(x["research_price_breaks"]==
               x["raid_pivot_same_utc_day"]+
               x["raid_pivot_previous_utc_day"]+
               x["raid_pivot_older_utc_day"] for x in data)
    return {
        "schema":"EMBER_C20C_ORIGINAL_45_SOURCE_CALENDAR_DIAGNOSTIC",
        "original_futures_zip_archives":45,
        "period_utc":["2026-09-01","2026-10-02"],
        "5m_native_rows":46080,
        "research_geom_5m_breaks":512,
        "rows":data,
        "author_approved_bos":0,
        "trades":0,
        "readiness":"NOT_TRADE_READY",
        "meaning":"UTC calendar, 24h delay and UTC 09-17 are diagnostics NOT author session or FTA."
    }
