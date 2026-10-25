#!/usr/bin/env python3
"""C56: original Binance USD-M native 3m vs *distinct* native 5m on same 1H raid.

Freshly download 60 checksummed ZIP: 30 prior C08 15m/1d and 15 each of
native 3m and native 5m. Reconstruct 32-day Decimal OHLCV lineage on both
native streams and compare exact immutable C37 LATEST parent events to C20B
5m observed breaks, not the other adapted C37 variants.

All times are CLOSED-bar knowledge times. Distinct original raw row IDs
and 1H parent identity are mandatory. TECHNICAL / ADAPTED ONLY; NO TRADES.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import Counter
from dataclasses import asdict
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tools","tests"):
    sys.path.insert(0,str(ROOT/d))

from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from probe_c20_original_5m_monthly_cross_15m import original_5m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c20_original_32day_native5m_lineage import reconcile_32day_native5m
from c21b_original_3m_raid_break_geometry import _source,_hours
from c20b_hourly_fractal_source_observer import closed_hourly
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted,AdaptedClosedBreak
from c20b_five_minute_break_observer import cross_timeframe_raid_break
from c56_crypto_native5m_1h_raid_bos_cross_tf import (
    c37_parent_key,c20_parent_key,compare_original_3m_5m_same_hourly_raid,
    TYPES,MISSING
)

FROZEN_C37=ROOT/"evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json"
FROZEN_C21B=ROOT/"evidence/c21/C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json"
PINNED_C56=ROOT/"evidence/c56/C56_ORIGINAL_60ZIP_SAME_1H_PARENT_3M_NATIVE5M_COMPLETE_SOURCE.json"
BASELINE="LATEST_CONFIRMED_V1"
CUT=OCT_START+DAY+900_000   # common, complete original 3m + native 5m 15m close

def key3(e):
    return c37_parent_key(e)

def key5(e):
    return c20_parent_key(e)

def _indexed(items,keyer):
    out={}
    for e in items:
        k=keyer(e)
        if k in out:
            raise ValueError("C56_DUPLICATE_SOURCE_1H_PARENT")
        out[k]=e
    return out

def _hour_price_parity(three,five,asof):
    h3=_hours(_source(three,asof))
    h5=closed_hourly(five,asof)
    if len(h3)!=len(h5):
        raise ValueError("C56_HOURLY_PARENT_GRID_DIFFERENT")
    for a,b in zip(h3,h5):
        if (a.start_ms,a.close_ms,a.open,a.high,a.low,a.close)!=(
            b.start_ms,b.close_ms,b.open,b.high,b.low,b.close):
            raise ValueError("C56_NATIVE3M_NATIVE5M_1H_PRICE_DISAGREEMENT")
    return len(h3)

def _rows(e3,e5, symbol, asof):
    by3=_indexed(e3,key3)
    by5=_indexed(e5,key5)
    if any(k[3]>asof for k in (set(by3)|set(by5))):
        raise ValueError("C56_PARENT_FUTURE_RAID_KNOWN_TIME")
    events=[]
    for key in sorted(set(by3)|set(by5)):
        a,b=by3.get(key),by5.get(key)
        x=compare_original_3m_5m_same_hourly_raid(symbol=symbol,e3=a,e5=b)
        if x.raid_closed_known_ms>asof or (
            x.original_3m_bos_known_ms is not None and x.original_3m_bos_known_ms>asof
        ) or (
            x.original_5m_bos_known_ms is not None and x.original_5m_bos_known_ms>asof
        ):
            raise ValueError("C56_FUTURE_CLOSED_EVENT_BEFORE_ASOF")
        if a is not None and b is not None:
            if (Decimal(a.raid_level)!=b.raid_pivot.level or
                Decimal(a.raid_extreme)!=b.raid.extreme or
                a.side!=b.side):
                raise ValueError("C56_FALSE_EQUAL_PARENT_HOURLY_PRICE")
            if a.break_original_native3m_row_id==b.source_row_id:
                raise ValueError("C56_BORROWED_ORIGINAL_3M_ID_AS_5M")
        source=asdict(x)
        source["source_3m_swing_raw_id"]=a.swing_center_native3m_row_id if a else None
        source["source_3m_swing_known_ms"]=a.swing_confirmed_ms if a else None
        source["source_5m_swing_raw_ids"]=list(b.swing.source_ids) if b else None
        source["source_5m_swing_known_ms"]=b.swing.known_ms if b else None
        source["source_1h_liquidity_level"]=a.raid_level if a else str(b.raid_pivot.level)
        source["source_1h_first_wick_extreme"]=a.raid_extreme if a else str(b.raid.extreme)
        source["source_3m_baseline"]=BASELINE if a else None
        events.append(source)
    return events

def run(out=None):
    pinned37=json.loads(FROZEN_C37.read_text(encoding="utf-8"))
    pinned21=json.loads(FROZEN_C21B.read_text(encoding="utf-8"))
    assert pinned37["schema"]=="EMBER_C37_INDEPENDENT_ORIGINAL_45ZIP_ADAPTED_3M_BOS_EVENTS_V1"
    assert pinned37["source_native3m_usdm_ZIP_files"]==45
    assert pinned37["source_closed_original3m_total"]==76800
    assert pinned21["original_total_zip"]==60
    assert pinned21["totals"]["native3m_cand_edges"]==539
    assert pinned21["totals"]["native5m_cand_edges"]==512
    p3={z["symbol"]:z for z in pinned37["markets"]}
    p21={z["symbol"]:z for z in pinned21["observations"]}
    assert set(p3)==set(p21)==set(SYMS)
    market=[];totals=Counter()
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,d,start)[0] for d,start in zip(DATES,STARTS))
                for tf in ("15m","1d")}
        htf=extended_32day_prefix(frames["15m"],frames["1d"],END)
        source3=tuple(native_3m(symbol,p) for p in PERIODS)
        source5=tuple(original_5m(symbol,p) for p in DATES)
        three=reconcile_native_3m(tuple(z[0] for z in source3),htf,as_of_ms=END)
        five=reconcile_32day_native5m(tuple(z[0] for z in source5),htf,as_of_ms=END)
        assert (len(three.original_3m_closed),len(five.original_5m_closed))==(15360,9216)
        assert three.native_15m_ohlcv_equalities==five.original_15m_equalities==3072
        assert three.readiness==five.readiness=="NOT_TRADE_READY"
        hour_count=_hour_price_parity(three,five,END)
        assert hour_count==768
        observed3=scan_original_3m_adapted(three,as_of_ms=END)
        observed5=cross_timeframe_raid_break(five,as_of_ms=END)
        baseline=observed3.routes[0]
        assert baseline.hypothesis_id==BASELINE
        assert baseline.readiness=="NOT_TRADE_READY"
        assert observed5.author_approved_bos==observed5.author_approved_trades==0
        assert observed5.readiness=="NOT_TRADE_READY"
        actual3=[asdict(x) for x in baseline.events]
        expected3=p3[symbol]["adapted_routes"][BASELINE]["native_3m_research_events"]
        # JSON decoding turns dataclass tuple defaults into lists.
        # Compare canonical JSON objects, retaining every original source field.
        normalized3=json.loads(json.dumps(actual3,sort_keys=True))
        assert normalized3==expected3,"C56_FRESH_45ZIP_C37_LATEST_FULL_EVENT_JSON_DRIFT"
        # Each source is physically truncated with known end, then compared with
        # computation over a complete source with exactly the same CLOSED as-of.
        prec3=reconcile_native_3m(tuple(z[0] for z in source3),htf,as_of_ms=CUT)
        prec5=reconcile_32day_native5m(tuple(z[0] for z in source5),htf,as_of_ms=CUT)
        assert _hour_price_parity(prec3,prec5,CUT)==_hour_price_parity(three,five,CUT)
        a3=scan_original_3m_adapted(prec3,as_of_ms=CUT)
        b3=scan_original_3m_adapted(three,as_of_ms=CUT)
        a5=cross_timeframe_raid_break(prec5,as_of_ms=CUT)
        b5=cross_timeframe_raid_break(five,as_of_ms=CUT)
        assert a3==b3,"C56_PHYSICALLY_CUT_3M_PREFIX_LEAK"
        assert a5==b5,"C56_PHYSICALLY_CUT_5M_PREFIX_LEAK"
        _rows(a3.routes[0].events,a5.potential_bos_witnesses,symbol,CUT)
        observed=_rows(baseline.events,observed5.potential_bos_witnesses,symbol,END)
        counts=Counter(x["source_status"] for x in observed)
        assert sum(counts.values())==len(observed)
        a=len(baseline.events);b=len(observed5.potential_bos_witnesses)
        assert a==counts[MISSING[0]]+sum(counts[t] for t in TYPES)
        assert b==counts[MISSING[1]]+sum(counts[t] for t in TYPES)
        old=p21[symbol]
        expected={
            TYPES[0]:old["earliest_3m_before_5m"],
            TYPES[1]:old["earliest_5m_before_3m"],
            TYPES[2]:old["simultaneous_close"],
            MISSING[0]:old["only_3m_parent"],
            MISSING[1]:old["only_5m_parent"],
        }
        assert all(counts[t]==n for t,n in expected.items()),"C56_C21B_60ZIP_PARENT_COUNT_DRIFT"
        assert observed3.source_confirmed_wick_raids==observed5.hourly_first_clean_wick_count==old["1h_first_fractal_wick"]
        assert observed3.source_1h_closed_bars==observed5.closed1h_bars==768
        assert observed3.paper_signals==observed3.author_bos_approved==0
        assert observed3.orders==observed3.trades==()
        assert not any(e["orders"] or e["trades"] or e["readiness"]!="NOT_TRADE_READY" or
                       e["author_bos_approved"] or e["author_fill_approved"] for e in observed)
        totals.update(counts)
        market.append({
            "symbol":symbol,
            "original_zip_sources":{
                "native_3m":[p[1] for p in source3],
                "native_5m":[p[1] for p in source5]},
            "original_3m_bars":15360,"original_5m_bars":9216,
            "both_independently_exact_native15m_decimal_equalities":3072,
            "original_equal_1h_price_sources":hour_count,
            "confirmed_preknown_1h_wick_raid_contexts":observed3.source_confirmed_wick_raids,
            "3m_baseline_source_events":a,
            "5m_distinct_source_events":b,
            "parent_status_counts":dict(sorted(counts.items())),
            "physical_prefix_equal_source_asof_both_timeframes":True,
            "parent_matched_events":observed})
        print("C56",symbol,a,b,dict(sorted(counts.items())),flush=True)
    source_totals=dict(sorted(totals.items()))
    assert {key:totals[key] for key in (*TYPES,*MISSING)}=={
        TYPES[0]:385,TYPES[1]:91,TYPES[2]:33,MISSING[0]:30,MISSING[1]:3}
    assert sum(x["original_3m_bars"] for x in market)==76800
    assert sum(x["original_5m_bars"] for x in market)==46080
    assert sum(x["both_independently_exact_native15m_decimal_equalities"] for x in market)==15360
    assert sum(x["original_equal_1h_price_sources"] for x in market)==3840
    document={
       "schema":"EMBER_C56_FRESH_ORIGINAL_60ZIP_NATIVE3M_NATIVE5M_SAME_HOURLY_FIRST_RAID_PARENT_V1",
       "scope":"BINANCE_USDM_CRYPTO_ONLY",
       "course_chart_market_role":"ILLUSTRATION_OF_LOGIC_ONLY",
       "source_native_zip_count":{"C08_15m_1d":30,"C21_3m":15,"C20_5m":15,"total":60},
       "period_utc":["2026-09-01","2026-10-02"],
       "source_closed_native3m":76800,"source_closed_native5m":46080,
       "source_native15m_decimal_parity_per_timeframe":15360,
       "source_hourly_OHLC_parities":3840,
       "3m_variant":"LATEST_CONFIRMED_V1",
       "baseline_hypothesis_pre_registered":True,
       "source_3m_candidate_contexts":539,
       "source_5m_candidate_contexts":512,
       "source_shared_1h_parents":509,
       "source_unique_1h_parents":542,
       "status_counts":source_totals,
       "original_all_parent_row_sha_and_closed_times_included":True,
       "physical_prefix_no_future_suffix_3m_5m":True,
       "readiness":"NOT_TRADE_READY",
       "author_1h_level_verified":False,
       "author_3m_BOS_verified":False,"author_5m_BOS_verified":False,
       "author_confirmed_signals":0,
       "fills":0,"orders":0,"trades":0,"PnL":None,
       "markets":market}
    assert document["source_shared_1h_parents"]==sum(totals[t] for t in TYPES)
    assert document["source_unique_1h_parents"]==sum(totals.values())
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(document,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if PINNED_C56.exists():
        assert PINNED_C56.read_bytes()==(
            json.dumps(document,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
        ).encode("utf-8"),"C56_FROZEN_FULL_ORIGINAL_60ZIP_BYTES_DRIFT"
    print("C56_NATIVE_3M_5M_PARENTS",json.dumps(source_totals,sort_keys=True),flush=True)
    return document

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
