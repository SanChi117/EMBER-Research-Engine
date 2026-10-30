#!/usr/bin/env python3
"""PRELIMINARY replication of three public Freqtrade signals, not Freqtrade engine.

Run after freezing SCREEN_POLICY.md, with unmodified public Binance USD-M 1h
market records under data/. Costs 14/25/40bps include adverse entry/exit.
No live orders, no funding or bid/ask, no hyperopt. Output always preserves
negative results. Will not create a portfolio equity performance claim.
"""
import hashlib
import json
import math
from pathlib import Path
from statistics import pstdev

HERE=Path(__file__).resolve().parent
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
WINDOWS={"A":("2025-02-01","2025-03-08"),
         "B":("2026-07-01","2026-08-05")}
STRATEGIES=("AdxSmas","BbandRsi","FAdxSmaStrategy")
COST_BPS=(14,25,40)
HOUR_MS=3600000
WARMUP=120
SL={"AdxSmas":0.25,"BbandRsi":0.25,"FAdxSmaStrategy":0.05}
ROI={"AdxSmas":0.10,"BbandRsi":0.10,"FAdxSmaStrategy":0.05}

def rolling_mean(seq,n):
    out=[None]*len(seq)
    for i in range(n-1,len(seq)):
        out[i]=sum(seq[i-n+1:i+1])/n
    return out

def rsi14(close):
    n=14
    x=[None]*len(close)
    changes=[close[i]-close[i-1] for i in range(1,len(close))]
    gain=sum(max(d,0) for d in changes[:n])/n
    loss=sum(max(-d,0) for d in changes[:n])/n
    def calc(a,b):
        if a+b==0: return 0.0
        return 100.0*a/(a+b)
    x[n]=calc(gain,loss)
    for i in range(n+1,len(close)):
        delta=changes[i-1]
        gain=((n-1)*gain+max(delta,0))/n
        loss=((n-1)*loss+max(-delta,0))/n
        x[i]=calc(gain,loss)
    return x

def adx14(high,low,close):
    n=14
    m=len(close)
    tr=[0.0]*m
    dmplus=[0.0]*m
    dmminus=[0.0]*m
    for i in range(1,m):
        up=high[i]-high[i-1]
        down=low[i-1]-low[i]
        dmplus[i]=up if up>down and up>0 else 0
        dmminus[i]=down if down>up and down>0 else 0
        tr[i]=max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
    smtr=sum(tr[1:n+1])
    smplus=sum(dmplus[1:n+1])
    smminus=sum(dmminus[1:n+1])
    dx=[None]*m
    for i in range(n,m):
        if i>n:
            smtr=smtr-smtr/n+tr[i]
            smplus=smplus-smplus/n+dmplus[i]
            smminus=smminus-smminus/n+dmminus[i]
        p=smplus/smtr if smtr>0 else 0.0
        q=smminus/smtr if smtr>0 else 0.0
        dx[i]=100*abs(p-q)/(p+q) if p+q>0 else 0.0
    result=[None]*m
    first=2*n-1
    result[first]=sum(dx[n:first+1])/n
    for i in range(first+1,m):
        result[i]=(result[i-1]*(n-1)+dx[i])/n
    return result

def cross_up(a,b,i):
    return (i>=1 and a[i] is not None and b[i] is not None
            and a[i-1] is not None and b[i-1] is not None
            and a[i-1]<=b[i-1] and a[i]>b[i])

def read_source(window,symbol):
    path=HERE/"data"/f"{window}_{symbol}.json"
    raw=path.read_bytes()
    blob=json.loads(raw)
    expected_start,expected_end=WINDOWS[window]
    assert (blob["symbol"],blob["interval"],blob["start"],
            blob["end_exclusive"])==(symbol,"1h",expected_start+"T00:00:00Z",
                                        expected_end+"T00:00:00Z")
    rows=blob["rows"]
    assert len(rows)==840,("SOURCE_BARS_NOT_840",window,symbol,len(rows))
    from datetime import datetime, timezone
    start=int(datetime.fromisoformat(blob["start"].replace("Z","+00:00")).timestamp()*1000)
    end=int(datetime.fromisoformat(blob["end_exclusive"].replace("Z","+00:00")).timestamp()*1000)
    assert end-start==len(rows)*HOUR_MS
    parsed=[]
    for i,row in enumerate(rows):
        assert len(row)==6 and row[0]==start+i*HOUR_MS
        o,h,l,c,v=map(float,row[1:])
        assert (all(math.isfinite(x) for x in (o,h,l,c,v)) and
                0<l<=min(o,c)<=max(o,c)<=h and v>=0)
        parsed.append((row[0],o,h,l,c,v))
    return parsed,hashlib.sha256(raw).hexdigest()

def signals(rows,strategy):
    close=[x[4] for x in rows]
    high=[x[2] for x in rows]
    low=[x[3] for x in rows]
    adx=adx14(high,low,close)
    long=[False]*len(rows)
    short=[False]*len(rows)
    exit_long=[False]*len(rows)
    exit_short=[False]*len(rows)
    if strategy=="AdxSmas":
        s=rolling_mean(close,3)
        l=rolling_mean(close,6)
        for i in range(WARMUP,len(rows)):
            long[i]=adx[i]>25 and cross_up(s,l,i)
            exit_long[i]=adx[i]<25 and cross_up(l,s,i)
    elif strategy=="FAdxSmaStrategy":
        s=rolling_mean(close,12)
        l=rolling_mean(close,48)
        for i in range(WARMUP,len(rows)):
            long[i]=adx[i]>30 and cross_up(s,l,i)
            short[i]=adx[i]>30 and cross_up(l,s,i)
            exit_long[i]=exit_short[i]=adx[i]<30
    elif strategy=="BbandRsi":
        rsi=rsi14(close)
        typical=[(x[2]+x[3]+x[4])/3 for x in rows]
        for i in range(WARMUP,len(rows)):
            mid=sum(typical[i-19:i+1])/20
            lower=mid-2*pstdev(typical[i-19:i+1])
            long[i]=rsi[i]<30 and close[i]<lower
            exit_long[i]=rsi[i]>70
    else:
        raise ValueError("UNKNOWN_STRATEGY")
    return long,short,exit_long,exit_short

def execute(rows,strategy,cost_bps):
    entry_side_cost=cost_bps/20000  # 14bps round-trip ~7bps each side
    long,short,exit_long,exit_short=signals(rows,strategy)
    trades=[]
    pos=None
    for i in range(WARMUP+1,len(rows)):
        time,o,h,l,c,_=rows[i]
        closed_here=False
        if pos:
            side=pos["side"]
            enter=pos["price"]
            stop=enter*(1-SL[strategy]) if side=="LONG" else enter*(1+SL[strategy])
            target=enter*(1+ROI[strategy]) if side=="LONG" else enter*(1-ROI[strategy])
            is_stop=(l<=stop) if side=="LONG" else (h>=stop)
            is_roi=(h>=target) if side=="LONG" else (l<=target)
            signal_exit=exit_long[i-1] if side=="LONG" else exit_short[i-1]
            reason=None
            if signal_exit:
                raw_exit=o
                reason="EXIT_SIGNAL_NEXT_OPEN"
            elif is_stop:
                raw_exit=min(o,stop) if side=="LONG" else max(o,stop)
                reason="STOP_FIRST_OR_WORSE_GAP"
            elif is_roi:
                raw_exit=target
                reason="ROI_TARGET"
            elif i==len(rows)-1:
                raw_exit=c
                reason="WINDOW_END_MARKED_CLOSED"
            if reason:
                fill=raw_exit*(1-entry_side_cost) if side=="LONG" else raw_exit*(1+entry_side_cost)
                pnl=((fill/enter)-1) if side=="LONG" else (1-fill/enter)
                trades.append({
                    "symbol":pos["symbol"],"side":side,
                    "entry_ts_ms":pos["time"],"exit_ts_ms":time,
                    "entry":round(enter,10),"exit":round(fill,10),
                    "reason":reason,"net_pct":round(pnl*100,8),
                    "net_r":round(pnl/SL[strategy],8)
                })
                pos=None
                closed_here=True
        if pos is None and not closed_here and i<len(rows)-1:
            side="LONG" if long[i-1] else ("SHORT" if short[i-1] else None)
            if side:
                fill=o*(1+entry_side_cost) if side=="LONG" else o*(1-entry_side_cost)
                pos={"symbol":None,"side":side,"price":fill,"time":time}
    return trades

def metrics(trades):
    profit=sum(max(t["net_pct"],0) for t in trades)
    loss=sum(-min(t["net_pct"],0) for t in trades)
    pf=round(profit/loss,5) if loss>0 else ("INF" if profit>0 else None)
    return {"n":len(trades),"wins":sum(t["net_pct"]>0 for t in trades),
            "net_pct_points":round(sum(t["net_pct"] for t in trades),6),
            "net_r":round(sum(t["net_r"] for t in trades),6),
            "pf":pf,"average_trade_pct":round(
                sum(t["net_pct"] for t in trades)/len(trades),6) if trades else None}

def main():
    from argparse import ArgumentParser
    ap=ArgumentParser()
    ap.add_argument("--output",default=str(HERE/"result.json"))
    args=ap.parse_args()
    source={}
    source_data={}
    for win in WINDOWS:
        for sym in SYMBOLS:
            source_data[(win,sym)],digest=read_source(win,sym)
            source[f"{win}/{sym}"]={"rows":840,"source_file_sha256":digest}
    report={"description":"3 public Freqtrade source-strategy signal replications; NOT native Freqtrade or executable fills",
            "scope":"RESEARCH ONLY, NO LIVE, no strategy tuning",
            "parameters":{"symbols":list(SYMBOLS),"window_utc":WINDOWS,"cost_bps_roundtrip":list(COST_BPS),
                "initial_warmup_1h_bars":WARMUP,"stop_fraction":SL,
                "fixed_approx_roi_fraction":ROI},
            "raw_input_source":source,"summary":{},"trades":[]}
    for name in STRATEGIES:
        windows={}
        for win in WINDOWS:
            stresses={}
            for bps in COST_BPS:
                all_trades=[]
                for sym in SYMBOLS:
                    tt=execute(source_data[(win,sym)],name,bps)
                    for t in tt:
                        t["symbol"]=sym
                        if bps==25:
                            report["trades"].append({"strategy":name,"window":win,**t})
                    all_trades.extend(tt)
                stresses[str(bps)]=metrics(all_trades)
            windows[win]=stresses
        a=windows["A"]["25"]
        b=windows["B"]["25"]
        passes=(a["n"]+b["n"]>=30 and isinstance(a["pf"],float)
             and isinstance(b["pf"],float) and a["pf"]>1.2 and b["pf"]>1.2
             and windows["A"]["40"]["net_pct_points"]>0
             and windows["B"]["40"]["net_pct_points"]>0)
        report["summary"][name]={"windows":windows,
            "advance_to_exact_freqtrade":passes,
            "screen_verdict":"NEEDS_EXACT_ENGINE_REPLICATION" if passes
                              else "NO_ECONOMIC_SCREEN_PASS_OR_TOO_SPARSE"}
    encoded=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    Path(args.output).write_text(encoded,encoding="utf-8")
    for name,entry in report["summary"].items():
        a=entry["windows"]["A"]["25"]
        b=entry["windows"]["B"]["25"]
        print(f"{name}: A n={a['n']} PF={a['pf']} net%pts={a['net_pct_points']}; "
              f"B n={b['n']} PF={b['pf']} net%pts={b['net_pct_points']}; "
              f"SCREEN={entry['screen_verdict']}")
    print("ALL_RESULTS=ALWAYS_SAVED, PNL_IS_NOT_PORTFOLIO_EQUITY, NOT_FREQTRADE_NATIVE")
if __name__=="__main__":
    main()
