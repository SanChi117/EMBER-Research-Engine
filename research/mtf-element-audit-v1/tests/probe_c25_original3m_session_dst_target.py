#!/usr/bin/env python3
"""Original 45 source ZIP C25 scenario disagreement, 1H target/SL geometry.

Never claim London/Kyiv/UTC calendar scenario equals author's session.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c25_session_freshness_target_source import inspect_c25,ZONES

METRICS=("original_parent_edges","research_single_parent_cases",
         "previous_day_timezone_disagreements","previous_session_timezone_disagreements",
         "raid_window_timezone_disagreements",
         "no_geometric_preknown_opposing_1h_target",
         "nonpositive_unbuffered_stop_distance")
def replay():
    prior=json.loads((ROOT/"evidence"/"c24"/"C24_ORIGINAL_3M_FAIL_CLOSED_ADMISSION.json").read_text())
    by_symbol={x["symbol"]:x for x in prior["original_source_market_results"]}
    findings=[]
    for symbol in sorted(SYMS):
        candle={}
        for tf in ("15m","1d"):
            candle[tf]=tuple(load_original(symbol,tf,p,start)[0]
                for p,start in zip(DATES,STARTS))
        htf=extended_32day_prefix(candle["15m"],candle["1d"],END)
        original3m=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(original3m,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        early=reconcile_native_3m(original3m,htf,as_of_ms=cut)
        assert inspect_c25(full,as_of_ms=cut)==inspect_c25(early,as_of_ms=cut),"C25_CAUSAL_SOURCE_PREFIX_DRIFT"
        audit=inspect_c25(full,as_of_ms=END)
        assert audit.research_single_parent_cases==by_symbol[symbol]["single_research_without_author_labels"]
        assert audit.original_parent_edges==by_symbol[symbol]["total_original_research_edges"]
        assert audit.author_approved_trades==0 and audit.readiness=="NOT_TRADE_READY"
        assert all(not e.author_approved_trade and not e.author_fta_attested for e in audit.cases)
        row={"symbol":symbol,"original_native3m_bars":len(full.original_3m_closed),
             "native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
             "scenario_zones":list(ZONES),"independent_prefix_equivalent":True}
        row.update({k:getattr(audit,k) for k in METRICS})
        row["previous_day_local"]={k:v for k,v in audit.previous_local_day_by_scenario}
        row["previous_session_09_17_local"]={k:v for k,v in audit.previous_09_17_session_by_scenario}
        row["raid_window_09_17_local"]={k:v for k,v in audit.raid_in_09_17_by_scenario}
        row["first_three_price_and_calendar_witnesses"]=[
          {"raid_ms":c.raid_ms,"break_ms":c.break_ms,
           "source_original3m_break_row_id":c.original_source_row_id,
           "research_raid_extreme":c.raid_extreme,
           "research_break_close":c.research_entry_close,
           "hypothetical_minimum_unbuffered_stop_distance":c.minimum_unbuffered_stop_distance,
           "nearest_preknown_opposing_1h_fractal_price":c.nearest_preknown_opposing_1h_fractal_price,
           "zones":[{"name":x.zone,"previous_day":x.pivot_was_previous_local_day,
                     "prior_session_09_17":x.pivot_in_previous_09_17_session,
                     "raid_window_09_17":x.raid_in_local_09_17_window,
                     "utc_offset_minutes":x.raid_local_utc_offset_minutes} for x in c.zones],
           "author_entry_approved":False} for c in audit.cases[:3]]
        findings.append(row)
        print(symbol,"C24 single research",audit.research_single_parent_cases,
              "previous-day zone disagreement",audit.previous_day_timezone_disagreements,
              "unproven 1h targets",audit.no_geometric_preknown_opposing_1h_target,flush=True)
    return findings

def main(output=None):
    rows=replay()
    totals={k:sum(v[k] for v in rows) for k in METRICS}
    prior={zone:sum(x["previous_day_local"][zone] for x in rows) for zone in ZONES}
    sessions={zone:sum(x["previous_session_09_17_local"][zone] for x in rows) for zone in ZONES}
    raid={zone:sum(x["raid_window_09_17_local"][zone] for x in rows) for zone in ZONES}
    result={
      "schema":"EMBER_C25_UNATTESTED_SESSION_DST_FTA_STOP_SOURCE_V1",
      "source_original_zip":45,
      "source_original_native3m":sum(x["original_native3m_bars"] for x in rows),
      "source_native15m_exact":sum(x["native15m_decimal_equalities"] for x in rows),
      "scenarios_not_author_settings":list(ZONES),
      "totals":totals,"local_prior_day_by_scenario":prior,
      "prior_09_17_local_by_scenario":sessions,
      "raid_09_17_local_by_scenario":raid,
      "markets":rows,"author_timezone_proven":False,
      "author_fta_stop_proven":False,"author_approved_trades":0,
      "readiness":"NOT_TRADE_READY",
      "limits":"Scenarios are hypotheses; 1h target is nearest historical opposing fractal geometry, not certified author FTA. Minimum stop distance excludes unknown buffer and fills."
    }
    assert result["source_original_native3m"]==76800
    assert result["source_native15m_exact"]==15360
    assert totals["original_parent_edges"]==539 and totals["research_single_parent_cases"]==165
    pin=ROOT/"evidence"/"c25"/"C25_ORIGINAL_SESSIONS_TARGET_SOURCE.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==result,"C25_SOURCE_PINNED_DRIFT"
    if output:Path(output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
