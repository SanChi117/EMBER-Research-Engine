#!/usr/bin/env python3
"""C62: fresh 45 signed original Binance USD-M ZIP 1H SNR/RB/IMB research.

Derived 1H from exact native15m; crosschecked native1d and original native3m.
Each detected SNR, weak MB, RB wick-raid, and 1H three-wick IMB remains
TECHNICAL SOURCE ONLY; none is author-approved POI, VC, StrongHL or trade.
"""
import sys,json,hashlib
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for f in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/f))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
C61=ROOT/"evidence/c61/C61_ORIGINAL45ZIP_DAILY_PRIOR_POI_FIRST_VISIT_STRONGHL_SOURCE_AUDIT.json"
PIN=ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json"
CUT=OCT_START+DAY+TF_MS["1h"]
KINDS=("SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY",
       "SNR_ACCEPTED_CLOSE_WITH_SOURCE_IMB_PROXY",
       "MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION",
       "RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY",
       "RB_WICK_ONLY_IMB_SOURCE_PROXY",
       "RB_TWO_OPPOSITE_HOURLY_CANDLES_WITHOUT_VERIFIED_WICK_RAID")
def run(output=None):
    frozen46=json.loads(C46.read_bytes())
    frozen61=json.loads(C61.read_bytes())
    ref46={x["symbol"]:x for x in frozen46["markets"]}
    assert frozen46["source_candidate_4h_IMB_count"]==153
    assert frozen61["original_4h_classic_imb_source_parents"]==153
    assert set(ref46)==set(SYMS)
    allm=[];counts=Counter()
    for symbol in sorted(SYMS):
        originals={tf:tuple(load_original(symbol,tf,p,t)[0]
          for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(originals["15m"],originals["1d"],END)
        zips=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        native=reconcile_native_3m(zips,htf,as_of_ms=END)
        assert len(native.original_3m_closed)==15360
        assert native.native_15m_ohlcv_equalities==3072
        assert len(htf.derived_1h_closed)==768 and len(htf.native_1d_closed)==32
        original46=inspect_original_4h_imb_source(native,as_of_ms=END)
        assert json.loads(json.dumps(asdict(original46),sort_keys=True))==ref46[symbol]["source_only_4h_classic_imb_first_contact"],"C62_ORIGINAL_C46_DRIFT"
        v=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        actual=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=CUT)
        k=(CUT-htf.derived_1h_closed[0].start_ms)//TF_MS["1h"]
        physical=observe_hourly_source_poi_split(htf.derived_1h_closed[:k],as_of_ms=CUT)
        assert actual==physical,"C62_1H_ORIGINAL_ASOF_PREFIX_FUTURE_LEAK"
        assert v["orders"]==v["trades"]==v["author_goldens"]==0
        assert v["readiness"]=="NOT_TRADE_READY"
        local=Counter()
        records=[]
        for obs in v["technical_1h_snr_rb_separate_cases"]:
            assert obs.source_class in KINDS,obs.source_class
            assert obs.side in ("LONG","SHORT")
            assert obs.fully_known_ms<=END
            assert obs.pair_first_known_ms<obs.fully_known_ms
            assert obs.pair_first_native15m_id in {
                r for bar in htf.derived_1h_closed
                for r in bar.source_native_15m_rows[:1]}
            assert not(obs.author_classified_poi or obs.author_volume_confirmation
                       or obs.author_stronghl or obs.orders or obs.trades)
            local[obs.source_class]+=1
            records.append(asdict(obs))
        gaps=[]
        for gap in v["technical_original_1h_imb_gaps"]:
            assert gap.known_ms<=END and gap.side in ("LONG","SHORT")
            assert gap.status.startswith("TECHNICAL_")
            gaps.append(asdict(gap))
        local["original_1h_technical_classic_gap"]=len(gaps)
        counts.update(local)
        allm.append({
          "symbol":symbol,
          "native15m_decimal_equalities":native.native_15m_ohlcv_equalities,
          "native3m_closed":len(native.original_3m_closed),
          "native1d_closed":len(htf.native_1d_closed),
          "original_1h_closed":len(htf.derived_1h_closed),
          "original_4h_frozen_C46_verified_parent_count":original46.candidate_count,
          "source_cases":records,
          "source_gaps":gaps,
          "case_counts":dict(sorted(local.items())),
          "physical_source_original_1h_asof_prefix_identical":True,
          "author_poI_goldens":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C62",symbol,dict(sorted(local.items())),flush=True)
    assert sum(x["native3m_closed"] for x in allm)==76800
    assert sum(x["native1d_closed"] for x in allm)==160
    assert sum(x["native15m_decimal_equalities"] for x in allm)==15360
    assert sum(x["original_1h_closed"] for x in allm)==3840
    assert sum(x["original_4h_frozen_C46_verified_parent_count"] for x in allm)==153
    assert sum(counts[x] for x in KINDS)==sum(len(x["source_cases"]) for x in allm)
    doc={
       "schema":"EMBER_C62_ORIGINAL_USDM_45ZIP_1H_SNR_RB_MB_IMB_SOURCE_SEPARATE_NO_AUTHOR_LABELS_V1",
       "scope":"CRYPTO_ONLY_FIVE_USDM_PAIRS_PAPER_ONLY",
       "period_utc":["2026-09-01","2026-10-02"],
       "original_signed_zip_counts":{"native_3m":15,"native_15m":15,"native_1d":15,"total":45},
       "original_native3m_closed":76800,
       "original_native1d_closed":160,
       "original_native15m_exact_decimal_equalities":15360,
       "source_derived_closed_1h_bars":3840,
       "original_c46_4h_source_parents_checked":153,
       "original_1h_source_category_totals":{name:counts[name] for name in (*KINDS,"original_1h_technical_classic_gap")},
       "source_first_classification_not_author_POI":True,
       "source_snr_mitigation_without_liquidity_never_vc":True,
       "rb_requires_preknown_unswept_source_liquidity_wick_only_or_preknown_imb_wick_test":True,
       "rb_body_liquidity_breach_never_qualifies_as_wick_raid":True,
       "source_1h_imb_requires_three_fully_closed_candles":True,
       "source_source_15m_exact_original_provenance":True,
       "author_snr_goldens":0,
       "author_rb_goldens":0,
       "author_imb_goldens":0,
       "author_valid_first_POI_test_goldens":0,
       "author_volume_confirmation_goldens":0,
       "author_stronghl_goldens":0,
       "source_limitations":"Adapted 1H wick/body geometry and strict previously confirmed 3-bar fractal represent source-only technical classes. Source 1H historical volume is not order book volume, author-defined traded-area SNR level, named POI, or author BOS. NO signal. Source classification counts are correlated and time-overlapping, not independent trade opportunities.",
       "previous_original_frozen_git_blobs":{
         "C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
         "C61":"305624e592f55bd699e94e45f4316e4efabdb726"},
       "orders":0,"fills":0,"trades":0,"PnL":None,
       "readiness":"NOT_TRADE_READY",
       "markets":allm}
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8"),"C62_1H_SOURCE_IMMUTABLE_DRIFT"
    print("C62_FULL_SOURCE_TOTALS",json.dumps(doc["original_1h_source_category_totals"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
