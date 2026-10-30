#!/usr/bin/env python3
"""A194 pre-registered final THREE baseline entry mechanisms for a small crypto account.
No indicator optimisation, no changes after first execution, paper research only.
Binance Vision USD-M BTC, ETH, SOL 5m monthly July-Sep 2026; Aug-Sep study.
15m CLOSED signal -> next 5m OPEN; 1h trend context CLOSED only.
Stop-first if 5m candle touches both SL and TP. Fees/slippage applied at BOTH fills.
Fixed R-target is ONLY a shared experiment control, NOT an EMBER 4h-zone strategy.
"""
from __future__ import annotations
import csv,hashlib,io,json,math,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
MONTHS=(7,8,9)
BEGIN=pd.Timestamp("2026-07-01",tz="UTC")
TEST=pd.Timestamp("2026-08-01",tz="UTC")
END=pd.Timestamp("2026-10-01",tz="UTC")
STRATEGIES=("A_TREND_PULLBACK","B_BREAK_RETEST","C_LIQUIDITY_SWEEP")
# FROZEN BEFORE ANY DATA RUN — DO NOT RETUNE against Aug-Sep 2026
RISK_FRACTION=0.01
MAX_NOTIONAL_TO_EQUITY=3.0
MIN_STOP_PCT=0.0025
MAX_STOP_PCT=0.025
TARGET_R=1.75
MAX_HOURS=8
BUFFER_ATR=0.15
LOW_FEE=0.0006
HIGH_FEE=0.00125
LOW_SLIP=0.0002
HIGH_SLIP=0.0005

def read_symbol(symbol,out:Path):
    rows=[]; manifest=[]
    for m in MONTHS:
        name=f"{symbol}-5m-2026-{m:02d}.zip"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/{name}"
        req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A194-three-mechanics-academic-paper"})
        with urllib.request.urlopen(req,timeout=90) as resp:
            body=resp.read(32_000_000)
            assert resp.status==200 and 10000<len(body)<32_000_000,("ZIP_SIZE",url,len(body))
        with ZipFile(io.BytesIO(body)) as z:
            files=[n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__")]
            assert len(files)==1,files
            csv_bytes=z.read(files[0])
        count=0
        for rec in csv.reader(io.StringIO(csv_bytes.decode("utf-8-sig"))):
            if not rec or rec[0].lower().startswith("open"):continue
            assert len(rec)>=6
            ts=int(rec[0])
            if ts>100_000_000_000_000:
                assert ts%1000==0
                ts//=1000
            rows.append([ts,*map(float,rec[1:6])])
            count+=1
        manifest.append({"url":url,"zip_sha256":hashlib.sha256(body).hexdigest(),
                         "csv_sha256":hashlib.sha256(csv_bytes).hexdigest(),"bars":count})
    expect=int((END-BEGIN).total_seconds()//300)
    assert len(rows)==expect,(symbol,len(rows),expect)
    startms=int(BEGIN.timestamp()*1000)
    for i,(ts,o,h,l,c,v) in enumerate(rows):
        assert ts==startms+i*300000,(symbol,"GAP_OR_DUP",i,ts)
        assert l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0,(symbol,"OHLC_INVALID",i)
    df=pd.DataFrame(rows,columns=["ts","open","high","low","close","volume"])
    df.index=pd.to_datetime(df.pop("ts"),unit="ms",utc=True)
    assert df.index.is_unique and df.index.is_monotonic_increasing
    return df,manifest

def feat(df):
    agg={"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
    m15=df.resample("15min",label="left",closed="left").agg(agg).dropna()
    h1=df.resample("1h",label="left",closed="left").agg(agg).dropna()
    assert len(m15)*3==len(df)
    assert len(h1)*12==len(df)
    m15["ema20"]=m15.close.ewm(span=20,adjust=False).mean()
    m15["ema50"]=m15.close.ewm(span=50,adjust=False).mean()
    prevclose=m15.close.shift(1)
    tr=pd.concat([m15.high-m15.low,(m15.high-prevclose).abs(),
                  (m15.low-prevclose).abs()],axis=1).max(axis=1)
    m15["atr"]=tr.ewm(alpha=1/14,adjust=False).mean()
    m15["prior20high"]=m15.high.shift(1).rolling(20).max()
    m15["prior20low"]=m15.low.shift(1).rolling(20).min()
    m15["vol20"]=m15.volume.shift(1).rolling(20).mean()
    m15["prior_ema20"]=m15.ema20.shift(1)
    m15["prior_low"]=m15.low.shift(1)
    m15["prior_high"]=m15.high.shift(1)
    m15["last3low"]=m15.low.rolling(3).min()
    m15["last3high"]=m15.high.rolling(3).max()
    h1["h_ema50"]=h1.close.ewm(span=50,adjust=False).mean()
    h1["h_ema200"]=h1.close.ewm(span=200,adjust=False).mean()
    # Re-label rows to end-of-bar (available immediately after closed candle).
    # Hour EMA at 13:00 includes candles through 12:59, NOT current 13:00..13:59.
    m15.index=m15.index+pd.Timedelta(minutes=15)
    h1.index=h1.index+pd.Timedelta(hours=1)
    context=h1[["h_ema50","h_ema200"]].reindex(m15.index,method="ffill")
    m15=m15.join(context)
    return m15

def signals(m):
    out={k:{} for k in STRATEGIES}
    # B strategy has armed breakout state, max 6 closed 15m bars till retest.
    armed=None
    rows=list(m.itertuples(name="Bar"))
    for i,v in enumerate(rows):
        t=m.index[i]
        if i<250 or t<TEST or t>=END or not math.isfinite(v.vol20) or not math.isfinite(v.atr):
            continue
        atr=float(v.atr)
        if atr<=0 or float(v.vol20)<=0: continue
        bull_h=bool(v.h_ema50>v.h_ema200)
        bear_h=bool(v.h_ema50<v.h_ema200)
        vol=float(v.volume)/float(v.vol20)
        up=v.close>v.open
        down=v.close<v.open
        # A: 1h established trend, 15m same-direction EMA20/50,
        # prior 15m low/high tags EMA20, current close reclaims; reject
        # a displacement >0.8 ATR from EMA20 to avoid late chases.
        long_a=(bull_h and v.ema20>v.ema50 and v.prior_low<=v.prior_ema20
                and up and v.close>v.ema20 and v.close<=v.ema20+0.8*atr
                and vol>=0.75)
        short_a=(bear_h and v.ema20<v.ema50 and v.prior_high>=v.prior_ema20
                 and down and v.close<v.ema20 and v.close>=v.ema20-0.8*atr
                 and vol>=0.75)
        if long_a != short_a:
            side=1 if long_a else -1
            stop=(min(v.last3low,v.ema50)-BUFFER_ATR*atr if side==1
                  else max(v.last3high,v.ema50)+BUFFER_ATR*atr)
            out["A_TREND_PULLBACK"][t]=(side,float(stop))
        # B: closes beyond prior 20-bar 15m range + volume>=1.3,
        # arm breakout level; enter ONLY after RETEST on a subsequent closed bar.
        if armed and (i>armed[2]+6):
            armed=None
        if armed and i>armed[2]:
            side,level,arm_i=armed
            if (side==1 and v.low<=level and v.close>level and up
                and bull_h and vol>=0.7):
                stop=min(v.last3low,level)-BUFFER_ATR*atr
                out["B_BREAK_RETEST"][t]=(side,float(stop));armed=None
            elif (side==-1 and v.high>=level and v.close<level and down
                  and bear_h and vol>=0.7):
                stop=max(v.last3high,level)+BUFFER_ATR*atr
                out["B_BREAK_RETEST"][t]=(side,float(stop));armed=None
            elif ((side==1 and v.close<level-0.5*atr) or
                  (side==-1 and v.close>level+0.5*atr)):
                armed=None
        if armed is None and t not in out["B_BREAK_RETEST"]:
            if bull_h and v.ema20>v.ema50 and v.close>v.prior20high and vol>=1.3:
                armed=(1,float(v.prior20high),i)
            elif bear_h and v.ema20<v.ema50 and v.close<v.prior20low and vol>=1.3:
                armed=(-1,float(v.prior20low),i)
        # C: causal prior20-bar low/high sweep and close back within range;
        # wick rejection, no h1 trend filter (a distinct countertrend family).
        range_=float(v.high-v.low)
        if range_<=0: continue
        sweep_long=(v.low<v.prior20low-0.1*atr and v.close>v.prior20low
                    and up and (v.close-v.low)/range_>=0.60 and vol>=1.0)
        sweep_short=(v.high>v.prior20high+0.1*atr and v.close<v.prior20high
                     and down and (v.high-v.close)/range_>=0.60 and vol>=1.0)
        if sweep_long != sweep_short:
            side=1 if sweep_long else -1
            stop=(float(v.low)-BUFFER_ATR*atr if side==1
                  else float(v.high)+BUFFER_ATR*atr)
            out["C_LIQUIDITY_SWEEP"][t]=(side,stop)
    return out

def execution(df,orders,fee,slip):
    cash=1000.0
    pos=None
    trades=[];equity_closed=[cash]
    for t,v in df.iterrows():
        if t<TEST or t>=END:continue
        if pos is not None:
            side=pos["side"];stop=pos["stop"];tp=pos["tp"]
            # Stop first if OHLC permits both (pessimistic intrabar order).
            price=None;reason=None
            if side==1:
                if v.open<=stop:price=float(v.open);reason="gap_stop"
                elif v.low<=stop:price=stop;reason="stop"
                elif v.open>=tp:price=float(v.open);reason="gap_tp"
                elif v.high>=tp:price=tp;reason="tp"
            else:
                if v.open>=stop:price=float(v.open);reason="gap_stop"
                elif v.high>=stop:price=stop;reason="stop"
                elif v.open<=tp:price=float(v.open);reason="gap_tp"
                elif v.low<=tp:price=tp;reason="tp"
            if price is None and t-pos["entry_time"]>=pd.Timedelta(hours=MAX_HOURS):
                price=float(v.open);reason="time"
            if price is not None:
                # Adverse side of slippage on exit, both sides fees on fills.
                exit_fill=price*(1-side*slip)
                qty=pos["qty"]
                pnl=side*(exit_fill-pos["entry_fill"])*qty
                pnl-=fee*qty*(pos["entry_fill"]+exit_fill)
                cash+=pnl
                trades.append({"entry":str(pos["entry_time"]),"exit":str(t),
                               "direction":"LONG" if side==1 else "SHORT",
                               "reason":reason,"pnl_usdt":round(pnl,8),
                               "net_R":round(pnl/max(pos["gross_stop_dollar"],1e-10),6),
                               "hours":(t-pos["entry_time"]).total_seconds()/3600,
                               "entry_price":round(pos["entry_fill"],7),
                               "exit_price":round(exit_fill,7)})
                equity_closed.append(cash)
                pos=None
            else: continue
        if pos is None and t in orders and cash>0:
            side,stop=orders[t]
            raw_entry=float(v.open)
            fill=raw_entry*(1+side*slip)
            risk=(fill-stop)*side/fill
            if not(MIN_STOP_PCT<=risk<=MAX_STOP_PCT):continue
            notional=min(cash*MAX_NOTIONAL_TO_EQUITY,cash*RISK_FRACTION/risk)
            if notional<=0:continue
            qty=notional/fill
            tp=fill+side*(TARGET_R*abs(fill-stop))
            pos={"side":side,"entry_time":t,"entry_fill":fill,
                 "stop":stop,"tp":tp,"qty":qty,
                 "gross_stop_dollar":qty*abs(fill-stop)}
            # Entry at 5m open; bracket can immediately hit on same
            # 5m candle, but execution checks begin on next loop iteration.
            # This is deliberately pessimistic for reversals; no liquidation simulated.
    if pos is not None:
        t=df.index[-1];p=float(df.close.iloc[-1])*(1-pos["side"]*slip)
        pnl=pos["side"]*(p-pos["entry_fill"])*pos["qty"]-fee*pos["qty"]*(p+pos["entry_fill"])
        cash+=pnl
        trades.append({"entry":str(pos["entry_time"]),"exit":str(t),
                       "direction":"LONG" if pos["side"]==1 else "SHORT",
                       "reason":"end","pnl_usdt":round(pnl,8),
                       "net_R":round(pnl/max(pos["gross_stop_dollar"],1e-10),6),
                       "hours":(t-pos["entry_time"]).total_seconds()/3600,
                       "entry_price":round(pos["entry_fill"],7),
                       "exit_price":round(p,7)})
        equity_closed.append(cash)
    profit=sum(x["pnl_usdt"] for x in trades if x["pnl_usdt"]>0)
    losses=-sum(x["pnl_usdt"] for x in trades if x["pnl_usdt"]<0)
    eq=np.asarray(equity_closed,float)
    peaks=np.maximum.accumulate(eq)
    dd=float(np.min(eq/peaks-1.0)) if len(eq) else 0.0
    return {"N":len(trades),"longs":sum(t["direction"]=="LONG" for t in trades),
            "shorts":sum(t["direction"]=="SHORT" for t in trades),
            "win_pct":round(100*sum(t["pnl_usdt"]>0 for t in trades)/len(trades),3) if trades else None,
            "pnl_usdt":round(cash-1000,4),
            "return_pct":round(100*(cash/1000-1),4),
            "PF":round(profit/losses,4) if losses>0 else None,
            "max_closed_trade_DD_pct":round(dd*100,4),
            "expectancy_net_R":round(float(np.mean([x["net_R"] for x in trades])),4) if trades else None,
            "top3_winners_profit_fraction":round(sum(sorted((x["pnl_usdt"] for x in trades),reverse=True)[:3])/profit,4) if profit>0 else None,
            "trades":trades}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--data-dir",required=True)
    a=p.parse_args()
    root=Path(a.data_dir);root.mkdir(parents=True,exist_ok=True)
    manifest={}
    results={}
    for symbol in SYMBOLS:
        df,receipts=read_symbol(symbol,root)
        manifest[symbol]=receipts
        f=feat(df)
        orders=signals(f)
        for mode in STRATEGIES:
            for scenario,fee,slip in (("base",LOW_FEE,LOW_SLIP),("stress",HIGH_FEE,HIGH_SLIP)):
                key=f"{mode}/{symbol}/{scenario}"
                results[key]=execution(df,orders[mode],fee,slip)
                o=results[key]
                print("A194_RESULT",key,"N",o["N"],"PF",o["PF"],
                      "NET_RETURN_PCT",o["return_pct"],"DD_CLOSED_PCT",o["max_closed_trade_DD_pct"],flush=True)
    condensed=[]
    for mode in STRATEGIES:
        for label in ("base","stress"):
            z=[results[f"{mode}/{s}/{label}"] for s in SYMBOLS]
            n=sum(r["N"] for r in z)
            pnl=sum(r["pnl_usdt"] for r in z)
            alltrades=[t for r in z for t in r["trades"]]
            gp=sum(t["pnl_usdt"] for t in alltrades if t["pnl_usdt"]>0)
            gl=-sum(t["pnl_usdt"] for t in alltrades if t["pnl_usdt"]<0)
            condensed.append({"mode":mode,"scenario":label,"trades":n,
                "return_pct_3_independent_1000usd_accounts":round(100*pnl/3000,4),
                "total_pnl_usdt":round(pnl,4),
                "pooled_PF":round(gp/gl,4) if gl else None,
                "winning_pairs":sum(r["pnl_usdt"]>0 for r in z),
                "mean_net_R":round(float(np.mean([t["net_R"] for t in alltrades])),4) if n else None,
                "max_closed_trade_DD_pct_worst_pair":min(r["max_closed_trade_DD_pct"] for r in z),
                "win_pct":round(sum(t["pnl_usdt"]>0 for t in alltrades)/n*100,3) if n else None})
    receipt={"schema":"EMBER_A194_PREREGISTERED_THREE_MECHANICS","date":"2026-10-31",
             "study":"no-fitting one historical holdout, not prospective true OOS",
             "market":"Binance Vision USD-M real 5m BTC/ETH/SOL",
             "source_months":list(MONTHS),"warmup":"2026-07-01..2026-08-01",
             "test_period":"[2026-08-01,2026-10-01)",
             "entry":"15m candle closed, next 5m open, 1h context last closed",
             "intrabar":"5m OHLC low/high ambiguous: SL priority if both in bar",
             "risk_and_exit":{"account_usdt_per_pair_per_strategy":1000,
                 "account_risk_cap":RISK_FRACTION,"max_notional_to_account":MAX_NOTIONAL_TO_EQUITY,
                 "stop":"previous 3 15m lows/highs for A/B, rejected candle wick for C, with 0.15 ATR pad",
                 "stop_pct_range":[MIN_STOP_PCT,MAX_STOP_PCT],
                 "target_R_frozen_research_control":TARGET_R,"max_hours":MAX_HOURS},
             "fee_slippage_each_side":{"base":[LOW_FEE,LOW_SLIP],"stress":[HIGH_FEE,HIGH_SLIP]},
             "limits":["No actual fills, 5m detail only, no bid/ask, no funding or liquidation modeling",
                       "Closed-trade DD underestimates intraposition DD",
                       "Strategies are new independent experimental BASLINES, not complete original author's profitable strategies",
                       "No parameter optimization, no real-money order placement, historical code written after data period",
                       "No multiple testing correction, 3 hypotheses tested, inspect consistency and concentration"],
             "sources":manifest,"summary":condensed,
             "per_pair_and_all_trades":results}
    Path(a.output).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("A194_THREE_MODELS_ORIGINAL_FROZEN_HYPOTHESES_FINISHED",len(results),flush=True)
    print(json.dumps(condensed,ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__":main()
