"""C20C observational UTC-calendar analysis of C20B 1h/5m witnesses.

UTC clock is not an author-defined session. No approved signals.
"""
from dataclasses import dataclass
from collections import Counter
from c16_c08_monthly_daily_htf_lineage import DAY
from c20b_five_minute_break_observer import cross_timeframe_raid_break

@dataclass(frozen=True)
class ContextCount:
    symbol:str
    observed_breaks:int
    same_utc_day:int
    previous_utc_day:int
    older_utc_day:int
    more_than_24h_after_raid:int
    coincident_break_parent_edges:int
    utc_9_17_proxy:int
    author_session_status:str="UNKNOWN_SOURCE_TIMEZONE"
    author_fta_status:str="UNKNOWN_SOURCE_FTA"
    author_bos_status:str="UNKNOWN_SOURCE_BOS_LABELS"
    readiness:str="NOT_TRADE_READY"

def review_calendar_context(line,*,as_of_ms:int)->ContextCount:
    """Source-validated diagnostic; never classify UTC as author session."""
    checked=cross_timeframe_raid_break(line,as_of_ms=as_of_ms)
    witnessed=checked.potential_bos_witnesses
    per_bar=Counter(x.start_ms for x in witnessed)
    same=prev=old=late=multi=utcwindow=0
    for x in witnessed:
        days=x.raid.first_breach_ms//DAY-x.raid.fractal.known_ms//DAY
        if days==0:same+=1
        elif days==1:prev+=1
        else:old+=1
        late+=x.known_ms-x.raid.confirmed_at_ms>DAY
        multi+=per_bar[x.start_ms]>1
        hour=x.known_ms//3600000%24
        utcwindow+=9<=hour<17
    assert same+prev+old==len(witnessed)
    return ContextCount(line.symbol,len(witnessed),same,prev,old,
                        late,multi,utcwindow)
