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
