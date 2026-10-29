"""C104: preregistered unchanged C93 Route C + native 4H / FTA quality PAPER backtest."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import c93_native3m_raid_bos_route_c_research as c93
import c102_c103_native3m_new_symbol_transfer as prev
import c103_exact_original_c93_baseline_parity as parity
import c104_native3m_source as sources
import c104_structural_quality_rules as quality

class C104Rejected(ValueError):pass
SRC_C93_SHA="a241d8de2691bca6247afbfe5e92b0a6e7df25b10f8a4c71f340b815e515bda0"
SRC_C102_SHA="853e5ee613e00cddbdf39b933c57bab6b6a6a695f1b549e69f29f52a97a01aed"
FOLD=int(datetime(2026,10,15,tzinfo=timezone.utc).timestamp()*1000)
BEGIN=prev.BEGIN_MS+7*prev.DAY_MS
END=prev.END_MS-12*c93.H1
ROUTES=("BASELINE_RAW","BASELINE_PORTFOLIO","QUALITY_RAW","QUALITY_PORTFOLIO")

def check_sha():
    base=Path(__file__).resolve().parent
    for name,sha in (("c93_native3m_raid_bos_route_c_research.py",SRC_C93_SHA),
                     ("c102_c103_native3m_new_symbol_transfer.py",SRC_C102_SHA)):
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=sha:
            raise C104Rejected("UNCHANGED_C93_C102_SOURCE_SHA_REQUIRED_"+name)

def records(rows,sym):
    if sym not in sources.SYMBOLS:raise C104Rejected("UNREGISTERED_SYMBOL")
    old=prev.SYMBOLS
    try:
        prev.SYMBOLS=sources.SYMBOLS
        events,reject=prev.candidate_events(rows,sym)
    finally:
        prev.SYMBOLS=old
    old=c93.SOURCES
    try:
        c93.SOURCES=frozenset(set(old)|set(sources.SYMBOLS))
        original=c93.discover(rows,sym)["trades"]
    finally:
        c93.SOURCES=old
    original=[x for x in original if BEGIN<=x["entry_ms"]<END and
              x["exit_ms"]<=prev.END_MS]
    computed=prev.select_sequential(events,"BASELINE")
    verified=parity.compare(original,computed)
    if not verified["matches"]:
        raise C104Rejected("ORIGINAL_C93_NONPARITY_"+sym)
    hour,four,swings=quality.context(rows)
    events=[{**t,"preentry_quality":quality.asof_quality(t,hour,four,swings)}
            for t in events]
    pass_counts={"candidates":len(events),
        "direction_4h":sum(t["preentry_quality"]["four_hour_direction_ok"] for t in events),
        "fta_reachable":sum(t["preentry_quality"]["fta_12h_range_ok"] for t in events),
        "joint":sum(t["preentry_quality"]["pass"] for t in events)}
    return events,verified,reject,pass_counts

def evaluate(t):
    ordered=sorted(t,key=lambda x:(x["entry_ms"],x["symbol"]))
    early=[x for x in ordered if x["entry_ms"]<FOLD]
    late=[x for x in ordered if x["entry_ms"]>=FOLD]
    scores={str(b):prev.score(ordered,b) for b in prev.COSTS}
    scores.update({"fold_early_n":len(early),"fold_late_n":len(late)})
    return {"trades":ordered,"scores":scores,
        "folds":{"early":{str(b):prev.score(early,b) for b in prev.COSTS},
                 "late":{str(b):prev.score(late,b) for b in prev.COSTS}},
        "by_symbol_n":{s:sum(x["symbol"]==s for x in ordered) for s in sources.SYMBOLS},
        "reasons":dict(sorted(Counter(x["exit_reason"] for x in ordered).items())),
        "side_n":dict(Counter(x["side"] for x in ordered))}

def accept(primary,benchmark):
    z=prev.admit(primary["scores"])
    reasons=z["reasons"][:]
    a=primary["scores"]["25"];b=benchmark["scores"]["25"]
    if not a["sum_r"]>b["sum_r"]:
        reasons.append("NETR25_NOT_BETTER_THAN_SAME_PORTFOLIO_CAP_BASE")
    if a["pf"] is None or b["pf"] is None or not a["pf"]>b["pf"]:
        reasons.append("PF25_NOT_BETTER_THAN_SAME_PORTFOLIO_CAP_BASE")
    return {"passes_historical_screen":not reasons,"reasons":reasons,
        "live_approved":False,"readiness":"PAPER_ONLY_HISTORICAL_NOT_PROSPECTIVE_OOS"}

def research(markets,manifest):
    check_sha()
    if set(markets)!=set(sources.SYMBOLS) or len(manifest)!=sources.EXPECTED:
        raise C104Rejected("ORIGINAL_320_ZIPS_10_MARKETS_REQUIRED")
    if len({(m["symbol"],m["date"]) for m in manifest})!=sources.EXPECTED:
        raise C104Rejected("NONUNIQUE_ORIGINAL_ARCHIVES")
    events={};parities={};rejections={};features={}
    for s in sources.SYMBOLS:
        events[s],parities[s],rejections[s],features[s]=records(markets[s],s)
    base=sorted((t for s in sources.SYMBOLS for t in quality.select_symbol(events[s])),
                key=lambda x:(x["entry_ms"],x["symbol"]))
    good=sorted((t for s in sources.SYMBOLS for t in quality.select_symbol(events[s],True)),
                key=lambda x:(x["entry_ms"],x["symbol"]))
    base_cap,base_block=quality.cap_direction(base)
    good_cap,good_block=quality.cap_direction(good)
    cases={"BASELINE_RAW":evaluate(base),"BASELINE_PORTFOLIO":evaluate(base_cap),
           "QUALITY_RAW":evaluate(good),"QUALITY_PORTFOLIO":evaluate(good_cap)}
    return {"schema":"C104_10COIN_ORIGINAL_NATIVE3M_CONFIRMED_4H_FTA_CAUSAL_QUALITY",
        "precommit":"B1_C104_PRECOMMIT_4H_STRUCTURE_FTA_REACHABILITY_PORTFOLIO_RU.md",
        "sample_type":"HISTORICAL_NEW_SYMBOL_TRANSFER_NOT_TRUE_LIVE_OOS",
        "symbols":list(sources.SYMBOLS),"source_manifest":manifest,
        "source_zip_count":len(manifest),"native3m_bars":sum(len(v) for v in markets.values()),
        "unchanged_c93_sha":SRC_C93_SHA,"unchanged_c102_sha":SRC_C102_SHA,
        "exact_original_c93_trade_parity":parities,
        "per_symbol_candidate_rejections":rejections,
        "quality_feature_pass":features,
        "portfolio_limit":"ONE_CONCURRENT_OPEN_POSITION_PER_DIRECTION",
        "blocked_portfolio_baseline":base_block,
        "blocked_portfolio_quality":good_block,
        "variants":cases,
        "primary_admission":accept(cases["QUALITY_PORTFOLIO"],cases["BASELINE_PORTFOLIO"]),
        "structural_original_sl_tp":True,"rr_target_fixed":False,
        "orders":[],"fills":[],"live_trades":[],
        "status":"PAPER_RESEARCH_NOT_LIVE_READY"}
def dumps(x):
    return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    check_sha()
    market,meta=sources.load()
    x=research(market,meta)
    raw=dumps(x)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)
    print(json.dumps({"witness_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
        "archive_count":x["source_zip_count"],"native3m_bars":x["native3m_bars"],
        "parity_total":sum(q["original_n"] for q in x["exact_original_c93_trade_parity"].values()),
        "variant_net25":{k:{"n":v["scores"]["25"]["n"],"netR25":v["scores"]["25"]["sum_r"],
          "PF25":v["scores"]["25"]["pf"]} for k,v in x["variants"].items()},
        "primary_admission":x["primary_admission"]},sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
