#!/usr/bin/env python3
"""C117 true random CLOCK conditional on SAME 4H first-touch parent.

Precommitted before C117 price download. 8 independently sampled 3m OPEN
times within 6h of each t0. T = frozen C114 5m CHoCH policy, 0R without fill.
R = average counterfactual outcome across 8 fixed random policies per t0.
PAPER ONLY. NOT unrestricted all-market random entries.
"""
from bisect import bisect_left,bisect_right
from collections import defaultdict,Counter
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
import argparse,hashlib,json,random
from pathlib import Path

import c114_independent_poi_native5m_choch_research as engine
import c116_single_source_controlled_4h_poi_replay as canonical
import c105_parent4h_structural_geometry as h4
import c93_native3m_raid_bos_route_c_research as swings

class C117Error(ValueError):pass

PRECOMMIT="cycles/B1_C117_PRECOMMIT_RANDOM_CLOCK_4H_PARENT_VS_CHOCH_RU.md"
FROZEN_C114="36d677166f4091f2ce66084dfb75f2407c72cbf735483cb3ee584a687ba41e6f"
WINDOWS=(
    ("WIN_A",datetime(2025,5,5,tzinfo=timezone.utc),
              datetime(2025,6,30,tzinfo=timezone.utc)),
    ("WIN_B",datetime(2026,9,1,tzinfo=timezone.utc),
              datetime(2026,10,27,tzinfo=timezone.utc)))
RANDOM_SEED=11720261030
SIGNFLIP_SEED=11720261031
REPS=2000
RANDOM_OFFSETS_PER_EVENT=8
OFFSETS=range(1,121)
EXPECTED_ZIP=1344
EXPECTED_1M_BARS=1935360
EXPECTED_3M_BARS=645120
EXPECTED_5M_BARS=387072
FOLD_DAYS=28

def frozen():
    if hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest()!=FROZEN_C114:
        raise C117Error("CHANGED_C114_TRADING_CORE")
    if (RANDOM_SEED!=11720261030 or SIGNFLIP_SEED!=11720261031 or
        REPS!=2000 or RANDOM_OFFSETS_PER_EVENT!=8 or
        engine.BPS!=(14,25,40) or engine.LANDMARK!=6*engine.H or
        len(engine.SYMBOLS)!=12 or len(WINDOWS)!=2 or
        any(e-s!=timedelta(days=56) for _,s,e in WINDOWS)):
        raise C117Error("PRECOMMIT_RANDOM_CONTROL_OR_NEW_SOURCE_CHANGED")
    canonical.frozen()
    return True

def random_offsets(symbol,parent_id,t0):
    if not symbol or not parent_id or type(t0) is not int:
        raise C117Error("MISSING_CAUSAL_PARENT_RANDOM_KEY")
    s=f"C117|{RANDOM_SEED}|{symbol}|{parent_id}|{t0}".encode("utf-8")
    rng=random.Random(int.from_bytes(hashlib.sha256(s).digest(),"big"))
    offsets=sorted(rng.sample(OFFSETS,RANDOM_OFFSETS_PER_EVENT))
    if (len(offsets)!=RANDOM_OFFSETS_PER_EVENT or
        len(set(offsets))!=RANDOM_OFFSETS_PER_EVENT or
        not all(1<=o<=120 for o in offsets)):
        raise C117Error("INVALID_RANDOM_TIMING_SELECTION")
    return tuple(offsets)

@contextmanager
def c117_scope():
    frozen()
    previous=(engine.WINDOWS,engine.PRECOMMIT,engine.download,engine.per_symbol)
    try:
        engine.WINDOWS=WINDOWS
        engine.PRECOMMIT=PRECOMMIT
        engine.download=canonical.canonical_download
        engine.per_symbol=canonical.price_lineage_per_symbol
        yield
    finally:
        (engine.WINDOWS,engine.PRECOMMIT,engine.download,engine.per_symbol)=previous

def random_on_same_parent(event, rows, starts, four, closed4ms, sw4, offset):
    """As-of original C105 4H geometry at preselected random 3m OPEN.

    No C114 CHoCH outcome, no future 4H pivots; same parent ID.
    Pre-entry original t0 stop/TP/invalidations count as zeroR, not deletion.
    """
    if offset not in OFFSETS:raise C117Error("OFFSET_OUT_OF_FROZEN_SUPPORT")
    t0=event["t0_touch_known_ms"]
    at=t0+offset*engine.THREE
    if at>event["landmark_ms"] or at<=t0:
        raise C117Error("RANDOM_CLOCK_OUTSIDE_6H")
    idx=bisect_left(starts,at)
    if idx>=len(rows) or rows[idx].start_ms!=at:
        raise C117Error("RANDOM_NATIVE_DERIVED3M_OPEN_MISSING")
    z=h4.Parent(event["side"],D(event["parent_low"]),D(event["parent_high"]),
                event["parent_created_ms"],event["parent_id"])
    if z.created_ms>=t0:
        raise C117Error("PARENT_CREATED_AFTER_FIRST_TOUCH")
    i0=bisect_left(starts,t0-engine.THREE)
    if i0<0 or i0>=len(rows) or rows[i0].known_ms!=t0:
        raise C117Error("MISSING_FIRST_TOUCH_CLOSE")
    n0=bisect_right(closed4ms,t0)
    before=four[:n0]
    if len(before)<15:raise C117Error("RANDOM_H4_HISTORY_MISSING")
    early=engine.early_competing(t0,at,rows[i0],rows,starts,z,before,sw4,four)
    if early["status"]!="SURVIVED_6H_LANDMARK":
        return None,early["status"]
    if any((q.c<z.lower if z.side=="LONG" else q.c>z.upper)
           for q in four if t0<q.close_ms<=at):
        return None,"PARENT_4H_INVALIDATED_BEFORE_RANDOM_OPEN"
    n4=bisect_right(closed4ms,at)
    plan,reason=h4.parent_plan(z,at,rows[idx].open,
                               four[:n4],sw4,rows,starts)
    if plan is None:return None,reason
    trade=h4.simulate(rows,idx,z.side,plan,bps=14)
    if trade["exit_ms"]>rows[-1].known_ms:
        raise C117Error("CENSORED_RANDOM_48H_HOLD")
    if (trade["parent_id"]!=event["parent_id"] or
        trade["parent_tf"]!=trade["stop_source_tf"] or
        trade["stop_source_tf"]!=trade["target_source_tf"] or
        trade["target_source_tf"]!="4H"):
        raise C117Error("RANDOM_LOW_TF_OR_WRONG_PARENT_GEOMETRY")
    trade["symbol"]=event["symbol"]
    return trade,"FILLED"

def event_controls(event,rows,starts,four,closed4ms,sw4):
    offsets=random_offsets(event["symbol"],event["parent_id"],event["t0_touch_known_ms"])
    values=[]
    reasons=Counter()
    choices=[]
    for offset in offsets:
        trade,reason=random_on_same_parent(event,rows,starts,four,closed4ms,sw4,offset)
        reasons[reason]+=1
        choices.append({"offset_3m":offset,
                        "entry_ms":event["t0_touch_known_ms"]+offset*engine.THREE,
                        "status":reason,
                        "trade":trade})
        values.append(trade)
    if len(choices)!=8:raise C117Error("DROPPED_RANDOM_PRESPECIFIED_BRANCH")
    return {"clock_seed_sha256":hashlib.sha256(
        f"C117|{RANDOM_SEED}|{event['symbol']}|{event['parent_id']}|{event['t0_touch_known_ms']}".encode()).hexdigest(),
        "offsets":list(offsets),
        "choices":choices,
        "status_counts":dict(reasons),
        "per_event_avg_random_R25":sum(engine.net_r(x,25) for x in values)/8,
        "per_event_avg_random_R40":sum(engine.net_r(x,40) for x in values)/8}

def build_random_evidence(payload,market,window):
    by_symbol=defaultdict(list)
    for symbol in engine.SYMBOLS:
        for e in payload["per_symbol"][symbol]["events"]:
            by_symbol[symbol].append(e)
    allrows=[]
    for symbol in engine.SYMBOLS:
        rows=market[symbol]
        starts=[x.start_ms for x in rows]
        four=h4.aggregate(rows,h4.H4)
        close4=[x.close_ms for x in four]
        sw4=swings._confirmed(four,h4.H4,int(window[2].timestamp()*1000))
        for e in by_symbol[symbol]:
            random_evidence=event_controls(e,rows,starts,four,close4,sw4)
            t=e["trade"]
            t25=engine.net_r(t,25)
            t40=engine.net_r(t,40)
            rand25=random_evidence["per_event_avg_random_R25"]
            rand40=random_evidence["per_event_avg_random_R40"]
            allrows.append({
                "symbol":symbol,"parent_id":e["parent_id"],
                "t0_touch_known_ms":e["t0_touch_known_ms"],
                "direction":e["side"],"treatment":e["treatment"],
                "t_landmark_ms":e["landmark_ms"],
                "t_trade":t,
                "T_R25":t25,"T_R40":t40,
                "R_avg_R25":rand25,"R_avg_R40":rand40,
                "delta_T_minus_R_25":t25-rand25,
                "delta_T_minus_R_40":t40-rand40,
                "random":random_evidence})
    n=sum(len(z) for z in by_symbol.values())
    if n!=len(allrows):raise C117Error("ITT_FIRST_TOUCH_DROPPED")
    return allrows

def cluster_test(rows):
    if not rows:
        return {"n_events":0,"n_symbol_week_blocks":0,
                "mean_delta_25":None,"bootstrap_low95":None,
                "signflip_p_one_sided":None,"state":"NO_POWER"}
    group=defaultdict(list)
    for r in rows:
        d=datetime.fromtimestamp(r["t0_touch_known_ms"]/1000,timezone.utc)
        iso=d.isocalendar()
        group[(r["symbol"],iso.year,iso.week)].append(r["delta_T_minus_R_25"])
    ids=sorted(group)
    summaries=[(sum(group[k]),len(group[k])) for k in ids]
    obs=sum(x[0] for x in summaries)/len(rows)
    rng=random.Random(RANDOM_SEED)
    boot=[]
    for _ in range(REPS):
        picks=[summaries[rng.randrange(len(summaries))] for __ in summaries]
        boot.append(sum(z[0] for z in picks)/sum(z[1] for z in picks))
    boot.sort()
    low=boot[int(.025*REPS)]
    sign_rng=random.Random(SIGNFLIP_SEED)
    exceed=0
    for _ in range(REPS):
        stat=sum((1 if sign_rng.getrandbits(1) else -1)*num
                  for num,denom in summaries)/len(rows)
        exceed+=stat>=obs-1e-12
    return {"n_events":len(rows),"n_symbol_week_blocks":len(summaries),
            "mean_delta_25":round(obs,8),
            "bootstrap_low95":round(low,8),
            "signflip_p_one_sided":round((exceed+1)/(REPS+1),8),
            "signflip_exceeds":exceed,
            "bootstrap_reps":REPS,"bootstrap_seed":RANDOM_SEED,
            "signflip_reps":REPS,"signflip_seed":SIGNFLIP_SEED,
            "state":"CALCULATED",
            "method":"SYMBOL_WEEK_CLUSTER_BOOTSTRAP_AND_PAIRED_SIGN_FLIP_ALL_ITT"}

def summary_scores(rows,window,baseline):
    treated=[{"trade":r["t_trade"]} for r in rows]
    t25=engine.score(treated,25)
    t40=engine.score(treated,40)
    random_events=[]
    # Each of eight random branch policies is a separate virtual alternative:
    for arm in range(8):
        per=[{"trade":r["random"]["choices"][arm]["trade"]} for r in rows]
        random_events.append({
            "arm_index":arm,
            "25":engine.score(per,25),
            "40":engine.score(per,40)})
    r_net25=sum(z["25"]["net_total_r"] for z in random_events)/8
    r_net40=sum(z["40"]["net_total_r"] for z in random_events)/8
    r_fill=sum(z["25"]["fills"] for z in random_events)/8
    rand_tp=sum(z["25"]["tp_before_sl_n"] for z in random_events)/8
    rand_stop=sum(z["25"]["sl_first_n"] for z in random_events)/8
    start=window[1]
    fold=int((start+timedelta(days=FOLD_DAYS)).timestamp()*1000)
    first=[r for r in rows if r["t0_touch_known_ms"]<fold]
    second=[r for r in rows if r["t0_touch_known_ms"]>=fold]
    t_fill_early=sum(r["t_trade"] is not None for r in first)
    t_fill_late=sum(r["t_trade"] is not None for r in second)
    stats=cluster_test(rows)
    reasons=[]
    if len(rows)<200:reasons.append("NO_POWER_LT_200_FIRST_TOUCH")
    if t25["fills"]<20:reasons.append("NO_POWER_LT_20_TREATMENT_FILLS")
    if t_fill_early<5 or t_fill_late<5:
        reasons.append("NO_POWER_LT_5_T_FILLS_EACH_28DAY_FOLD")
    if stats["n_symbol_week_blocks"]<8:reasons.append("NO_POWER_LT_8_SYMBOL_WEEK_CLUSTERS")
    if t25["net_total_r"]<=0:reasons.append("T_NET25_NONPOSITIVE")
    if t25["pf"] is None or t25["pf"]<=1.2:reasons.append("T_PF25_LE_1_2")
    if t40["pf"] is None or t40["pf"]<=1.1:reasons.append("T_PF40_LE_1_1")
    if stats["mean_delta_25"] is None or stats["mean_delta_25"]<=0:
        reasons.append("RANDOM_TIME_DELTA_NOT_POSITIVE")
    if stats["bootstrap_low95"] is None or stats["bootstrap_low95"]<=0:
        reasons.append("RANDOM_TIME_95CI_NOT_POSITIVE")
    if stats["signflip_p_one_sided"] is None or stats["signflip_p_one_sided"]>=.05:
        reasons.append("RANDOM_TIME_SIGNFLIP_P_NOT_LT_0_05")
    if t25["fills"]==0 or not r_fill or (
        t25["tp_before_sl_n"]/t25["fills"]<=rand_tp/r_fill):
        reasons.append("T_TP_FIRST_RATE_NOT_BETTER_THAN_RANDOM_TIME")
    if baseline["portfolio"]["dd_adverse_wick_pct_upper_bound"]>=10:
        reasons.append("T_CONCURRENT_PORTFOLIO_WICK_DD_GE_10")
    state=("NO_POWER" if any(z.startswith("NO_POWER") for z in reasons) else
            "FAIL" if reasons else "HISTORICAL_SCREEN_PASS_PAPER_ONLY")
    return {
        "state":state,"reasons":reasons,"all_touch_n":len(rows),
        "T_policy_25bps":t25,"T_policy_40bps":t40,
        "random_8_policies":random_events,
        "R_mean_total_net25":round(r_net25,6),
        "R_mean_total_net40":round(r_net40,6),
        "R_mean_fills":r_fill,
        "R_mean_tp_before_sl_n":rand_tp,
        "R_mean_stop_first_n":rand_stop,
        "T_fills_early_fold":t_fill_early,
        "T_fills_late_fold":t_fill_late,
        "T_mean_r_per_itt_event":t25["mean_r_per_itt_event"],
        "R_mean_r_per_itt_event":round(r_net25/len(rows),8) if rows else None,
        "cluster":stats,
        "T_portfolio_dd":baseline["portfolio"],
        "unrestricted_market_random_entry":False,
        "actual_orders_submitted":False,"live_approved":False,
    }

def run():
    frozen()
    windows={}
    with c117_scope():
        for window in WINDOWS:
            three,five,rec3,rec5,parity=engine.download(window)
            core=engine.evaluate(window,three,five,rec3,rec5,parity)
            ledger=build_random_evidence(core,three,window)
            score=summary_scores(ledger,window,core)
            windows[window[0]]={
                "window":window[0],"period_start":window[1].isoformat(),
                "period_end_exclusive":window[2].isoformat(),
                "original_1m_provider_zip_receipts":rec3,
                "source_same_one_minute_sha_receipts_5m":rec5,
                "one_source_derived_15m_parity":parity,
                "original_1m_zip_count":len(rec3),
                "source_original_1m_bars":56*1440*len(engine.SYMBOLS),
                "derived3m_bars":sum(len(x) for x in three.values()),
                "derived5m_bars":sum(len(x) for x in five.values()),
                "cohort":core["cohort"],
                "C114_observational_original_scores":core["scores"],
                "C114_original_admission":core["admission"],
                "C117_precommitted_random_clock_gate":score,
                "same_4h_parent_all_touches_ITT":ledger,
                "per_symbol":core["per_symbol"],
            }
    if (sum(x["original_1m_zip_count"] for x in windows.values())!=EXPECTED_ZIP or
        sum(x["source_original_1m_bars"] for x in windows.values())!=EXPECTED_1M_BARS or
        sum(x["derived3m_bars"] for x in windows.values())!=EXPECTED_3M_BARS or
        sum(x["derived5m_bars"] for x in windows.values())!=EXPECTED_5M_BARS):
        raise C117Error("C117_ORIGINAL_1M_SOURCE_COUNTS_UNTRUSTED")
    return {"schema":"C117_ORIGINAL_NATIVE1M_SAME_PARENT_RANDOM_CLOCK_VS_5M_CHOCH",
            "precommit":PRECOMMIT,
            "frozen_c114_trade_core_sha256":FROZEN_C114,
            "original_1m_zip_total":EXPECTED_ZIP,
            "original_1m_bar_total":EXPECTED_1M_BARS,
            "derived3m_bars_total":EXPECTED_3M_BARS,
            "derived5m_bars_total":EXPECTED_5M_BARS,
            "random_controls_per_4h_first_touch":RANDOM_OFFSETS_PER_EVENT,
            "source_known_not_true_independent_3m5m":True,
            "historical_not_prospective_oos":True,
            "paper_only":True,"live_approved":False,
            "real_orders":[],"real_fills":[],"live_trades":[],
            "both_windows_historical_screen_pass":all(
                w["C117_precommitted_random_clock_gate"]["state"]==
                "HISTORICAL_SCREEN_PASS_PAPER_ONLY" for w in windows.values()),
            "windows":windows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    out=run()
    folder=args.output_dir
    folder.mkdir(parents=True,exist_ok=True)
    rec={}
    for name,z in out["windows"].items():
        fname=f"C117_{name}_ORIGINAL1M_FIRST_TOUCH_RANDOM_CLOCK_ALL_ITT.json"
        raw=(json.dumps(z,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
        (folder/fname).write_bytes(raw)
        rec[name]={"filename":fname,"sha256":hashlib.sha256(raw).hexdigest(),
                   "bytes":len(raw),"admission":z["C117_precommitted_random_clock_gate"],
                   "cohort":z["cohort"],
                   "original_1m_zip_count":z["original_1m_zip_count"]}
    summary={k:v for k,v in out.items() if k!="windows"}
    summary["window_receipts"]=rec
    raw=(json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
    (folder/"C117_SUMMARY.json").write_bytes(raw)
    print(json.dumps({"original_1m_zips":out["original_1m_zip_total"],
        "windows":rec,"both_pass":out["both_windows_historical_screen_pass"],
        "summary_sha256":hashlib.sha256(raw).hexdigest(),"live_approved":False},
        sort_keys=True,ensure_ascii=False))
if __name__=="__main__": main()
