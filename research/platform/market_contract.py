"""Zero-lookahead closed-bar/data-source contract.

Do not mistake exchange kline closed_ms for an actually observed real-time feed;
historical reconstruction is separately flagged and cannot authorize live data.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re

class DataUntrusted(ValueError):
    pass

_SYMBOL=re.compile(r"^[A-Z0-9]{2,22}$")
_SHA=re.compile(r"^[0-9a-f]{64}$")

def dec(value, *, positive=False, nonnegative=False):
    try:
        result=Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise DataUntrusted("NONDECIMAL") from exc
    if not result.is_finite():
        raise DataUntrusted("NONFINITE")
    if positive and result<=0: raise DataUntrusted("NONPOSITIVE")
    if nonnegative and result<0: raise DataUntrusted("NEGATIVE")
    return result

def timestamp(x):
    if type(x) is not int or x<=0 or x>=10**15:
        raise DataUntrusted("NONCANONICAL_UNIX_MS")
    return x

@dataclass(frozen=True)
class ClosedBar:
    symbol:str
    venue:str
    market_kind:str
    interval_ms:int
    open_ms:int
    close_ms:int
    available_at_ms:int
    ingested_at_ms:int
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    volume:Decimal
    origin_sha256:str
    provenance:str

    def __post_init__(self):
        if not _SYMBOL.fullmatch(self.symbol) or not self.venue:
            raise DataUntrusted("INVALID_MARKET_ID")
        if self.market_kind not in ("SPOT","PERP_USDM"):
            raise DataUntrusted("UNKNOWN_MARKET_TYPE")
        if type(self.interval_ms) is not int or self.interval_ms<60000 or self.interval_ms%60000:
            raise DataUntrusted("BAD_MINUTE_TIMEFRAME")
        for v in (self.open_ms,self.close_ms,self.available_at_ms,self.ingested_at_ms):
            timestamp(v)
        if (self.open_ms%self.interval_ms or
            self.close_ms-self.open_ms!=self.interval_ms or
            self.available_at_ms<self.close_ms or
            self.ingested_at_ms<self.available_at_ms):
            raise DataUntrusted("BAR_CLOCK_NOT_CAUSAL")
        if not _SHA.fullmatch(self.origin_sha256):
            raise DataUntrusted("SOURCE_SHA_REQUIRED")
        if self.provenance not in ("HISTORICAL_ASSUMED_AT_CLOSE","OBSERVED_LIVE"):
            raise DataUntrusted("PROVENANCE_REQUIRED")
        a,b,c,d=(dec(getattr(self,k),positive=True) for k in
                 ("open","high","low","close"))
        volume=dec(self.volume,nonnegative=True)
        if b<max(a,d) or c>min(a,d) or c>b:
            raise DataUntrusted("INVALID_OHLC")
        for k,v in zip(("open","high","low","close","volume"),(a,b,c,d,volume)):
            object.__setattr__(self,k,v)

def from_c116(row, *, symbol, venue, origin_sha256,
              ingested_at_ms, historical_assumed_close):
    """Adapt *verified* C116 Original1m. Legacy row alone cannot prove live availability."""
    if historical_assumed_close is not True:
        raise DataUntrusted("HISTORICAL_ASOF_ASSUMPTION_MUST_BE_EXPLICIT")
    if row.known_ms-row.start_ms!=60000:
        raise DataUntrusted("BAD_ORIGINAL_C116_MINUTE")
    return ClosedBar(symbol=symbol,venue=venue,market_kind="PERP_USDM",
                     interval_ms=60000,open_ms=row.start_ms,
                     close_ms=row.known_ms,available_at_ms=row.known_ms,
                     ingested_at_ms=ingested_at_ms,
                     open=row.o,high=row.h,low=row.l,close=row.c,
                     volume=row.volume,origin_sha256=origin_sha256,
                     provenance="HISTORICAL_ASSUMED_AT_CLOSE")

def closed_asof(rows, *, decision_at_ms, max_last_bar_lag_ms,
                require_live=False):
    timestamp(decision_at_ms)
    if type(max_last_bar_lag_ms) is not int or max_last_bar_lag_ms<0:
        raise DataUntrusted("BAD_FRESHNESS_POLICY")
    if not rows:raise DataUntrusted("NO_BARS")
    out=[]
    prev=None
    identity=None
    for x in rows:
        if not isinstance(x,ClosedBar):raise DataUntrusted("UNVERIFIED_BAR")
        if require_live and x.provenance!="OBSERVED_LIVE":
            raise DataUntrusted("HISTORICAL_REPLAY_IS_NOT_LIVE")
        if x.available_at_ms>decision_at_ms:
            # As-of cut: future observations are NOT usable.
            break
        if identity is None: identity=(x.symbol,x.venue,x.market_kind,x.interval_ms)
        if (x.symbol,x.venue,x.market_kind,x.interval_ms)!=identity:
            raise DataUntrusted("CROSS_MARKET_SOURCE_MIXED")
        if prev is not None and x.open_ms!=prev.close_ms:
            raise DataUntrusted("GAP_DUPLICATE_OR_OUT_OF_ORDER")
        if x.ingested_at_ms>decision_at_ms and require_live:
            raise DataUntrusted("NOT_ACTUALLY_OBSERVED_AT_DECISION_TIME")
        out.append(x);prev=x
    if not out:raise DataUntrusted("NO_CLOSED_ASOF_BARS")
    if decision_at_ms-out[-1].available_at_ms>max_last_bar_lag_ms:
        raise DataUntrusted("STALE_MARKET_OBSERVATION")
    return tuple(out)
