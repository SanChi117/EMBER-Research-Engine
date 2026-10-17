"""Forensic inventory of native three-minute candidate structures."""
from collections import Counter
from c21b_original_3m_raid_break_geometry import _source, _swings, observe_native3m_raid_break

def summarize_pivots(source, *, as_of_ms):
    """Count all historically known rival 3m structural swing candidates."""
    bars=_source(source, as_of_ms)
    all_swings=_swings(bars)
    events=observe_native3m_raid_break(source, as_of_ms=as_of_ms)
    return bars, all_swings, events
