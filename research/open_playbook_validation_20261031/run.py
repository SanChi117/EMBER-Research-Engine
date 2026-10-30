#!/usr/bin/env python3
"""Auditable quick reproduction of two PUBLIC rule-based playbooks, NOT source backtest.
No exchange orders. Read frozen 1h Binance USDM JSON. All costs 14/25/40bps.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"quick_open_strategy_screen_20261031"/"data"
OUT=Path(__file__).resolve().parent/"RESULTS.json"
SPECS={"A":("A_ETHUSDT.json","2025-02-01T00:00:00Z","2025-03-08T00:00:00Z",840),
       "B":("B_ETHUSDT.json","2026-07-01T00:00:00Z","2026-08-05T00:00:00Z",840),
       "C":("C_pre_2024_ETHUSDT.json","2024-05-01T00:00:00Z","2024-08-01T00:00:00Z",2208),
       "D":("D_post_2026_ETHUSDT.json","2026-10-19T00:00:00Z","2026-10-30T00:00:00Z",264)}
COSTS=(14,25,40)
CANDIDATES=("ORB24","BREAKOUT24VOL")

def utc(t):
    return datetime.fromtimestamp(t/1000,timezone.utc)

def source(win):
    filename,start,end,n=SPECS[win]
    raw=(ROOT/filename).read_bytes()
    d=json.loads(raw)
    assert d["symbol"]=="ETHUSDT" and d["interval"]=="1h"
    assert d["start"]==start and d["end_exclusive"]==end
    expect=int(datetime.fromisoformat(start.replace("Z","+00:00")).timestamp()*1000)
    until=int(datetime.fromisoformat(end.replace("Z","+00:00")).timestamp()*1000)
    rows=d["rows"]
    assert len(rows)==n and until-expect==n*3600000
    clean=[]
    for i,r in enumerate(rows):
        t=r[0]
        assert t==expect+i*3600000
        o,h,l,c,v=map(float,r[1:6])
        assert all(math.isfinite(x) for x in (o,h,l,c,v))
        assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
        clean.append((t,o,h,l,c,v))
    return clean,hashlib.sha256(raw).hexdigest()

def avg(values, end, size):
    if end-size+1<0:return None
    return sum(values[end-size+1:end+1])/size

def metrics(trades):
    pos=sum(max(t["net_return"],0.0) for t in trades)
    neg=sum(max(-t["net_return"],0.0) for t in trades)
    pf=pos/neg if neg>0 else ("INF" if pos>0 else None)
    bal=1.0;peak=1.0;dd=0.0
    for t in sorted(trades,key=lambda t:t["exit_ms"]):
        bal*=1+t["net_return"];peak=max(peak,bal)
        dd=max(dd,(peak-bal)/peak)
    return {"n":len(trades),
       "wins":sum(x["net_return"]>0 for x in trades),
       "pf":round(pf,5) if isinstance(pf,float) else pf,
       "sum_notional_return_pct_points":round(100*sum(t["net_return"] for t in trades),5),
       "avg_trade_pct":round(100*sum(t["net_return"] for t in trades)/len(trades),5) if trades else None,
       "hypothetical_compound_1x_pct":round(100*(bal-1),5),
       "hypothetical_trade_to_trade_dd_pct":round(100*dd,5),
       "worst_trade_pct":round(100*min((x["net_return"] for x in trades),default=0.0),5)}

def simulate(rows,candidate,cost):
    close=[r[4] for r in rows];high=[r[2] for r in rows];low=[r[3] for r in rows];vol=[r[5] for r in rows]
    slippage=cost/20000
    trades=[]; position=None
    entered_days=set()
    def exit_position(i,raw,reason):
        nonlocal position
        side=position["side"]
        fill=raw*(1-slippage if side=="LONG" else 1+slippage)
        r=(fill/position["entry"]-1) if side=="LONG" else (1-fill/position["entry"])
        trades.append({"entry_ms":position["entry_ms"],"exit_ms":rows[i][0],
                       "side":side,"entry":round(position["entry"],6),
                       "exit":round(fill,6),"reason":reason,
                       "net_return":round(r,10),
                       "entry_close_signal_ms":position["signal_ms"],
                       "max_intrabar_adverse_pct":round(position["worst"]*100,5)})
        position=None
    for i in range(168,len(rows)):
        t,o,h,l,c,v=rows[i]
        hour=utc(t).hour
        j=i-1  # ONLY last fully closed candle decides trade at hour i open.
        prev24=avg(close,j,24)
        executed_exit=False
        if position:
            if candidate=="ORB24" and hour==0:
                exit_position(i,o,"NEXT_00UTC_OPEN_AFTER_23UTC_CLOSE")
                executed_exit=True
            elif candidate=="BREAKOUT24VOL" and (
                (position["side"]=="LONG" and close[j]<prev24) or
                (position["side"]=="SHORT" and close[j]>prev24)
            ):
                exit_position(i,o,"MA24_PREVIOUS_CLOSE_SIGNAL_NEXT_OPEN")
                executed_exit=True
        if position is None and not executed_exit:
            side=None
            if candidate=="ORB24":
                sigdt=utc(rows[j][0]); day=sigdt.date()
                if 4<=sigdt.hour<=12 and day not in entered_days:
                    first=j-sigdt.hour
                    or_high=max(high[first:first+4])
                    or_low=min(low[first:first+4])
                    if close[j]>or_high and close[j]>prev24:
                        side="LONG"
                    elif close[j]<or_low and close[j]<prev24:
                        side="SHORT"
                    if side:entered_days.add(day)
            elif candidate=="BREAKOUT24VOL":
                ma48=avg(close,j,48)
                ma168=avg(close,j,168)
                v6=avg(vol,j,6)
                v72=avg(vol,j,72)
                if v72 and v6/v72>1:
                    prior_high=max(high[j-24:j])
                    prior_low=min(low[j-24:j])
                    if close[j]>prior_high and ma48>ma168:side="LONG"
                    elif close[j]<prior_low and ma48<ma168:side="SHORT"
            else:raise ValueError(candidate)
            if side:
                entry=o*(1+slippage if side=="LONG" else 1-slippage)
                position={"side":side,"entry":entry,"entry_ms":t,
                          "signal_ms":rows[j][0],"worst":0.0}
        if position:
            adverse=max(0.0,(position["entry"]-l)/position["entry"]) if position["side"]=="LONG" else (
                     max(0.0,(h-position["entry"])/position["entry"]))
            position["worst"]=max(position["worst"],adverse)
    # Never turn an unclosed position into an imaginary target fill.
    if position is not None:
        # This is a separate censored terminal bar close, not an actual next-hour fill.
        i=len(rows)-1
        exit_position(i,rows[-1][4],"CENSORED_WINDOW_END_LAST_CLOSE_PROXY")
    return trades

def main():
    all_data={};source_sha={}
    for win in SPECS:
        rows,sha=source(win)
        all_data[win]=rows
        source_sha[win]={"sha256":sha,"bars":len(rows)}
    report={"timestamp_scope":"2026-10-31 research before new strategy tuning",
            "venue_disclaimer":"Binance USDM ETHUSDT is NOT original ETH-USDC perpetual; original publication performance not independently confirmed",
            "execution_disclaimer":"1h next-open proxy: no bid/ask/funding/liquidation/exchange order logs; cost stress only",
            "original_playbooks":{
                "ORB24":"alphapilot.tech/playbooks/eth-opening-range-breakout-145-6-with-a-24h-trend-filter-ffb184",
                "BREAKOUT24VOL":"alphapilot.tech/playbooks/eth-24-hour-breakout-strategy-83-with-trend-and-volume-filters-495f9d"},
            "frozen_data":source_sha,"costs_roundtrip_bps":list(COSTS),
            "candidates":{},"trades_cost25":[]}
    for candidate in CANDIDATES:
        per={}
        for win in SPECS:
            cost_results={}
            for cost in COSTS:
                trades=simulate(all_data[win],candidate,cost)
                cost_results[str(cost)]=metrics(trades)
                if cost==25:
                    report["trades_cost25"].extend([{"strategy":candidate,"window":win,**x} for x in trades])
            per[win]=cost_results
        threshold=(all(per[x]["25"]["n"]>0 and isinstance(per[x]["25"]["pf"],float)
            and per[x]["25"]["pf"]>1.2 and per[x]["40"]["sum_notional_return_pct_points"]>0
            for x in ("A","B","C"))
            and sum(per[x]["25"]["n"] for x in ("A","B","C"))>=60
            and per["D"]["25"]["worst_trade_pct"]>-10)
        report["candidates"][candidate]={"windows":per,"advance":threshold}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    for name,c in report["candidates"].items():
        print(name, "gate",c["advance"]," ".join(
             f"{k}:n{v['25']['n']}/PF{v['25']['pf']}/sumPctPts{v['25']['sum_notional_return_pct_points']}"
             for k,v in c["windows"].items()))
    print("REPRODUCIBLE_COMPLETE_ALL_NEGATIVE_AND_POSITIVE_SAVED")
if __name__=="__main__":
    main()
