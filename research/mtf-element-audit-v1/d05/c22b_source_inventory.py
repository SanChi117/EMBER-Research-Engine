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

        simultaneous=[]
        for swing in eligible:
            if e.side=="SHORT":
                crossed=prior.close>=swing.level and bar.close<swing.level
            else:
                crossed=prior.close<=swing.level and bar.close>swing.level
            if crossed:simultaneous.append(swing)
        if e.swing not in simultaneous:
            raise ValueError("SOURCE_SELECTED_SWING_NOT_CROSSED")
        alternatives=[s for s in simultaneous if s!=e.swing]
        detail.append({
            "raid_start_ms":e.raid_start_ms,
            "break_start_ms":e.break_start_ms,
            "selected_center_ms":e.swing.center_ms,
            "eligible_pivot_count":len(eligible),
            "simultaneous_alternative_count":len(alternatives),
            "eligible_centers":[s.center_ms for s in eligible],
            "crossed_alternative_centers":[s.center_ms for s in alternatives],
            "author_status":"AUTHOR_TIMESTAMPED_GOLDEN_MISSING"
        })

    return {
      "symbol":source.symbol,
      "observed_parent_edges":len(detail),
      "multiple_eligible_parent_edges":sum(d["eligible_pivot_count"]>1 for d in detail),
      "same_bar_multiple_crossings":sum(d["simultaneous_alternative_count"]>0 for d in detail),
      "eligible_pivot_options":sum(d["eligible_pivot_count"] for d in detail),
      "alternate_pivot_options":sum(d["eligible_pivot_count"]-1 for d in detail),
      "simultaneous_extra_crossings":sum(d["simultaneous_alternative_count"] for d in detail),
      "first_ten_research_cases":detail[:10],
      "source_author_goldens":0,
      "author_approved_trades":0,
      "readiness":"NOT_TRADE_READY"
    }
