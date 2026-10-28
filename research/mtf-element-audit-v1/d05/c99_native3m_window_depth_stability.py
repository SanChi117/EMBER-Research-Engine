"""C99: original Binance native3m C93 BOS source-window invariance.

Precommitted 2026-10-28 before reloading source. Compare 32d windows ending
Oct10/18/27 with UNCHANGED C93 model over common chronological intervals,
7 fully closed day warm-up and 12h pre-window-end execution embargo.
Fail closed for missing sources; report mismatched outcomes, NOT retune.
PAPER only; research technical stability is NOT trading edge.
"""
from datetime import datetime,timezone,timedelta
from hashlib import sha256
from collections import Counter
import json
from c89_original_native5m_adaptation_backtest import _safe_http,SOURCES
from c93_native3m_raid_bos_route_c_research import load_3m_source,discover as discover_c
from c98_new_oct_original_forward_paper import daily_zip,DAYS,EXPECTED_SYMBOLS
from c21_native3m_source_bridge import THREE,Original3mRow
class C99Rejected(ValueError):pass
DAY=86400000
OCT3=int(datetime(2026,10,3,tzinfo=timezone.utc).timestamp()*1000)
ENDINGS=("2026-10-10","2026-10-18","2026-10-27")
WARMUP_DAYS=7
EXIT_EMBARGO=12*3600000
WINDOW_DAYS=32
WARMUP_PREDECLARED=True
C_SOURCE="ORIGINAL_NATIVE3M_BINANCE_REPLAY_ONLY"
def when(s):
    return int(datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def validate_witness(x):
    if x.get("new_archive_count")!=240 or x.get("period_end_exclusive_ms")!=when("2026-10-27"):
        raise C99Rejected("REQUIRES_FROZEN_OCT_ORIGINAL_SOURCE_EVIDENCE")
    rows=[r for r in x.get("new_source_manifest",[]) if r.get("timeframe")=="3m"]
    if (len(rows)!=120 or len({(r["symbol"],r["date"]) for r in rows})!=120
        or set(r["date"] for r in rows)!=set(DAYS)
        or set(r["symbol"] for r in rows)!=set(SOURCES)):
        raise C99Rejected("ORIGINAL_PINNED_DAILY3M_UNIVERSE_MISMATCH")
    return {(r["symbol"],r["date"]):r for r in rows}
def _new_verified(witness,*,fetch):
    expected=validate_witness(witness)
    out={}
    receipt=[]
    for sym in EXPECTED_SYMBOLS:
        rows=[]
        for date in DAYS:
            part,meta=daily_zip(sym,"3m",date,fetch=fetch)
            old=expected[(sym,date)]
            for key in ("symbol","timeframe","date","bars","zip_sha256","csv_sha256","url"):
                if old[key]!=meta[key]:
                    raise C99Rejected(f"C98_ORIGINAL_ARCHIVE_SOURCE_DIGEST_DRIFT_{sym}_{date}_{key}")
            if rows and rows[-1].known_ms!=part[0].start_ms:
                raise C99Rejected("OCT_NATIVE3M_ARCHIVE_GAP")
            rows.extend(part);receipt.append(meta)
        out[sym]=tuple(rows)
    return out,receipt
def _window(rows,end_ms):
    """Only 32 fully closed UTC days from the same immutable Sep1 anchor."""
    start=end_ms-WINDOW_DAYS*DAY
    starts=rows[0].start_ms
    if start<starts or (start-starts)%THREE or (end_ms-starts)%THREE:
        raise C99Rejected("WINDOW_INCOMPLETE_OR_UNALIGNED")
    left=(start-starts)//THREE
    right=(end_ms-starts)//THREE
    chosen=rows[left:right]
    if (len(chosen)!=WINDOW_DAYS*DAY//THREE or
       chosen[0].start_ms!=start or chosen[-1].known_ms!=end_ms or
       any(a.known_ms!=b.start_ms for a,b in zip(chosen,chosen[1:]))):
        raise C99Rejected("WINDOW_NATIVE3M_ORIGINAL_CLOSED_GAP")
    return chosen
def signature(t):
    keys=("symbol","route","side","entry_ms","exit_ms","entry","stop",
          "target","fta","derived_rr","net_r","exit_reason",
          "raid_fractal_known_ms","bos_close_ms","fta_confirmed_ms")
    if any(k not in t for k in keys):
        raise C99Rejected("SOURCE_C_TRADE_INCOMPLETE")
    return tuple((k,t[k]) for k in keys)
def _sortsig(seq):
    return tuple(sorted((signature(t) for t in seq),key=lambda x:(dict(x)["entry_ms"],dict(x)["symbol"])))
def _within(trades,lower,upper):
    return [t for t in trades if lower<=t["entry_ms"]<upper and t["exit_ms"]<=upper]
def compare(first,second,end_a,end_b,*,minimum=10):
    if end_a==end_b or end_a not in [when(x) for x in ENDINGS] or end_b not in [when(x) for x in ENDINGS]:
        raise C99Rejected("UNREGISTERED_COMPARISON_BOUNDARIES")
    # To avoid missing first source events from start-of-window,
    # reserve 7 fully closed daily bars from later window's 32d beginning.
    lower=max(OCT3,max(end_a,end_b)-WINDOW_DAYS*DAY+WARMUP_DAYS*DAY)
    upper=min(end_a,end_b)-EXIT_EMBARGO
    if upper<=lower:raise C99Rejected("NO_MATURE_OVERLAP")
    a=_sortsig(_within(first,lower,upper))
    b=_sortsig(_within(second,lower,upper))
    sa=set(a);sb=set(b)
    if len(sa)!=len(a) or len(sb)!=len(b):
        raise C99Rejected("DUPLICATED_C_SOURCE_TRADE_SIGNATURE")
    only_a=sorted(sa-sb,key=repr);only_b=sorted(sb-sa,key=repr)
    common=len(sa&sb)
    matched=not only_a and not only_b
    return {"older_window_end_ms":min(end_a,end_b),
        "newer_window_end_ms":max(end_a,end_b),
        "compared_from_ms":lower,"compared_until_exclusive_ms":upper,
        "trades_first":len(a),"trades_second":len(b),
        "identical":matched,"union_trades":len(sa|sb),
        "common_trades":common,"sufficient_n":len(sa|sb)>=minimum,
        "different_first_only":len(only_a),"different_second_only":len(only_b),
        "example_first_only":str(only_a[0]) if only_a else None,
        "example_second_only":str(only_b[0]) if only_b else None,
        "sha_first":sha256(repr(a).encode()).hexdigest(),
        "sha_second":sha256(repr(b).encode()).hexdigest()}
def run(c73,c21,c98_witness,*,fetch=_safe_http):
    if type(c73) is not bytes or type(c21) is not bytes:
        raise C99Rejected("C21_C73_ORIGINAL_SOURCE_REQUIRED")
    old,old_manifest=load_3m_source(c21,c73,fetch=fetch)
    ext,verified_receipts=_new_verified(c98_witness,fetch=fetch)
    if len(verified_receipts)!=120:raise C99Rejected("NO_FULL_OCT_NATIVE3M_SOURCE")
    sets={};comparisons={};trade_counts={}
    for sym in EXPECTED_SYMBOLS:
        timeline=old[sym]+ext[sym]
        if len(timeline)!=15360+24*480 or timeline[0].start_ms!=when("2026-09-01"):
            raise C99Rejected("OLDER_C_SOURCE_CONTEXT_INCOMPLETE")
        if timeline[-1].known_ms!=when("2026-10-27"):
            raise C99Rejected("FUTURE_SOURCE_HORIZON_MISSING")
        calculated={}
        trade_counts[sym]={}
        for date in ENDINGS:
            cutoff=when(date)
            src=_window(timeline,cutoff)
            result=discover_c(src,sym) # UNCHANGED academic-informed module C93
            calculated[date]=result["trades"]
            trade_counts[sym][date]=len(result["trades"])
        sets[sym]=calculated
        comparisons[sym]={}
        for i,a in enumerate(ENDINGS):
            for b in ENDINGS[i+1:]:
                comparisons[sym][a+"_vs_"+b]=compare(calculated[a],calculated[b],when(a),when(b))
    witnesses=[v for x in comparisons.values() for v in x.values()]
    mismatches=[v for v in witnesses if not v["identical"]]
    samples=[v for v in witnesses if v["sufficient_n"]]
    verdict=("CONTEXT_UNSTABLE" if mismatches else
             "NO_POWER" if not samples else "MATCHED_ON_REGISTERED_COMMON_WINDOWS")
    return {"schema":"EMBER_C99_UNCHANGED_C93_NATIVE3M_WINDOW_INVARIANCE",
        "source":"C21_C73_PLUS_C98_120_SHA_PINNED_NATIVE3M_BINANCE_ZIP",
        "original_source_archives":old_manifest,
        "new_source_archives":verified_receipts,
        "model":"C93_UNCHANGED_1H_RAID_THEN_3M_BOS",
        "window_endings":list(ENDINGS),
        "warmup_days":WARMUP_DAYS,
        "execution_embargo_hours":EXIT_EMBARGO//3600000,
        "by_market":comparisons,"counts_by_window":trade_counts,
        "pairwise_source_comparisons":len(witnesses),
        "pairs_sufficient_n":len(samples),
        "total_window_inconsistencies":len(mismatches),
        "verdict":verdict,
        "may_claim_stable_economic_alpha":False,
        "original_entry_tp_sl_modified":False,
        "orders":[],"fills":[],"live_trades":[],
        "status":"PAPER_ONLY_HISTORY_DEPTH_DIAGNOSTIC"}
def dumps(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
