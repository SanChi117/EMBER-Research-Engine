"""Forensic inventory of native three-minute candidate structures."""
from collections import Counter
from c21b_original_3m_raid_break_geometry import _source, _swings, observe_native3m_raid_break

def summarize_pivots(source, *, as_of_ms):
    """Count all historically known rival 3m structural swing candidates."""
    bars=_source(source, as_of_ms)
    all_swings=_swings(bars)
    events=observe_native3m_raid_break(source, as_of_ms=as_of_ms)
    return bars, all_swings, events

def audit_rival_pivots(source, *, as_of_ms):
    bars,swings,events=summarize_pivots(source,as_of_ms=as_of_ms)
    detail=[]
    for e in events.potential_breaks:
        at=(e.break_start_ms-bars[0].start_ms)//180000
        if at<1 or at>=len(bars):
            raise ValueError("INVALID_SOURCE_C22B_BAR_INDEX")
        prior,bar=bars[at-1],bars[at]
        if bar.raw_id!=e.source_original_3m_row_id:
            raise ValueError("SOURCE_3M_BREAK_ID_CHANGED")

        eligible=[]
        for swing in swings:
            if swing.center_ms<e.raid_start_ms:continue
            if swing.known_ms<e.raid_start_ms+3600000:continue
            if swing.known_ms>e.break_start_ms:continue
            if swing.kind!=e.swing.kind:continue
            if e.side=="SHORT" and swing.level>=e.raid_level:continue
            if e.side=="LONG" and swing.level<=e.raid_level:continue
            eligible.append(swing)
        if not eligible or eligible[-1]!=e.swing:
            raise ValueError("LATEST_KNOWN_PROXY_PIVOT_DRIFT")
