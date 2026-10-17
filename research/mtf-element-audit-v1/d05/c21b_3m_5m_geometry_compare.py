"""B1/C21B: compare matched 1H first-wick raid parents across 3m and 5m.

Source-only comparison. Never count multiple parent edges as independent
trades; never force 3m/5m equivalence or choose a winner/nearest parent.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import observe_native3m_raid_break
from c20b_five_minute_break_observer import cross_timeframe_raid_break
from c20b_hourly_fractal_source_observer import closed_hourly

@dataclass(frozen=True)
class ParentComparison:
    symbol:str
    at_ms:int
    native3m_cand_edges:int
    native5m_cand_edges:int
    same_parent_with_both:int
    only_3m_parent:int
    only_5m_parent:int
    earliest_3m_before_5m:int
    earliest_5m_before_3m:int
    simultaneous_close:int
    distinct_3m_native_break_bars:int
    distinct_5m_native_break_bars:int
    multi_parent_3m_edges:int
    multi_parent_5m_edges:int
    readiness:str="NOT_TRADE_READY"
    author_trades:int=0

def compare_original_3m_and_5m(three,five,*,as_of_ms):
    if as_of_ms%900000:
        raise ValueError("COMMON_ASOF_NEEDS_CLOSED_15M_BOUNDARY")
    a=observe_native3m_raid_break(three,as_of_ms=as_of_ms)
    b=cross_timeframe_raid_break(five,as_of_ms=as_of_ms)
    if three.symbol!=five.symbol or a.source_hourly_closed!=b.closed1h_bars:
        raise ValueError("ORIGINAL_3M_VS_5M_SYMBOL_HOUR_GRID")
    # 3m and 5m histories MUST agree on *all* source 1h OHLCV.
    from c21b_original_3m_raid_break_geometry import _source,_hours
    h3=_hours(_source(three,as_of_ms))
    h5=closed_hourly(five,as_of_ms)
    for x,y in zip(h3,h5):
        if (x.start_ms,x.close_ms,x.open,x.high,x.low,x.close)!=(
            y.start_ms,y.close_ms,y.open,y.high,y.low,y.close):
            raise ValueError("SOURCE_DERIVED_HOURLY_3M_5M_PARITY_DRIFT")
    def key(x):return (x.pivot_kind,x.pivot_center_ms,x.raid_start_ms,x.side)
    def key5(x):return (x.raid.fractal.kind,x.raid.fractal.center_ms,x.raid.first_breach_ms,x.side)
    three_by={key(x):x.break_known_ms for x in a.potential_breaks}
    five_by={key5(x):x.known_ms for x in b.potential_bos_witnesses}
    akeys=set(three_by);bkeys=set(five_by)
    both=akeys&bkeys
    t3=[x.break_start_ms for x in a.potential_breaks]
    t5=[x.start_ms for x in b.potential_bos_witnesses]
    return ParentComparison(a.symbol,as_of_ms,len(t3),len(t5),len(both),
        len(akeys-bkeys),len(bkeys-akeys),
        sum(three_by[k]<five_by[k] for k in both),
        sum(three_by[k]>five_by[k] for k in both),
        sum(three_by[k]==five_by[k] for k in both),
        len(set(t3)),len(set(t5)),
        len(t3)-len(set(t3)),len(t5)-len(set(t5)))
