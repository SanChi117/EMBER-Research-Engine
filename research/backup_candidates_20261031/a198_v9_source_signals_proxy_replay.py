#!/usr/bin/env python3
"""A198 source-pinned original V9 StrategyEngine signals with an INDEPENDENT execution proxy.
This is NOT native/original V9 historical backtester (none published).
No live API, no bot instantiated, no credentials, no orders. Strictly causal 1h/4h.
2 fees+slippage models x 2 risk options, no tuning. Real Binance SOL/BTC futures data.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,types,collections,sys
from pathlib import Path
import numpy as np
import pandas as pd

BLOB="b18ac10938e6aa91dfa42293a5da6fb6d545039d"
EVAL_FROM=pd.Timestamp("2026-05-13T00:00:00Z")
EVAL_END=pd.Timestamp("2026-10-01T00:00:00Z")
TIMEDELTA_1H=pd.Timedelta(hours=1)
SOURCES=("SOL","BTC")
DEFAULT_CAPITAL=1000.0
PAIR_FEE={"base":(.0005,.0002),"stress":(.00125,.0005)}
RISK_MODE=("author_original_6pct_target","external_1pct_cap")

def load_source(file):
    raw=Path(file).read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert sha==BLOB,("AUTHOR_SOURCE_BLOB_PIN_MISMATCH",sha)
    spec=importlib.util.spec_from_file_location("a198_original_v9_source_only",file)
    obj=importlib.util.module_from_spec(spec)
    # Python dataclasses requires module registered before evaluating annotations.
    sys.modules[spec.name]=obj
    spec.loader.exec_module(obj)
    return obj,sha

def dataframe(file):
    raw=json.loads(Path(file).read_text())
    df=pd.DataFrame(raw,columns=["ts","Open","High","Low","Close","Volume"])
    assert len(df) and df["ts"].is_unique and df["ts"].is_monotonic_increasing,(file,len(df))
    df["open_time"]=pd.to_datetime(df.pop("ts"),unit="ms",utc=True)
    df["close_time"]=df["open_time"]+pd.Timedelta(milliseconds=3599999)
    return df[["open_time","close_time","Open","High","Low","Close","Volume"]]

def prepare_signals(orig,data):
    cfg=orig.Config()
    cfg.validate()
    assert cfg.enable_pullback and not cfg.enable_breakout
    assert not cfg.enable_compression and not cfg.enable_range_sweep and not cfg.enable_pure_donchian
    assert cfg.pullback_confirm_min_votes==4 and cfg.pullback_confirm_exact
    assert cfg.pullback_stop_atr==1.75 and cfg.pullback_tp1_r==1.50 and cfg.pullback_tp2_r==2.50
    assert cfg.tp1_close_pct==.40 and cfg.post_tp1_lock_r==.10
    assert cfg.target_stop_risk_pct==.06 and cfg.portfolio_margin_cap==.95 and cfg.max_dynamic_leverage==3
    assert cfg.signal_history==600 and cfg.regime_history==600
    assert not cfg.live_trading and not cfg.api_key and not cfg.api_secret

    sol_h1=orig.add_indicators(dataframe(data/"SOL_USDT_USDT-1h-futures.json"),cfg.signal_ema_fast,cfg.signal_ema_slow,cfg.signal_vwap_window,cfg)
    sol_h4=orig.add_indicators(dataframe(data/"SOL_USDT_USDT-4h-futures.json"),cfg.regime_ema_fast,cfg.regime_ema_slow,cfg.regime_vwap_window,cfg)
    btc_h4=orig.add_indicators(dataframe(data/"BTC_USDT_USDT-4h-futures.json"),cfg.regime_ema_fast,cfg.regime_ema_slow,cfg.regime_vwap_window,cfg)
    assert len(sol_h1)>6500 and len(sol_h4)>1600 and len(btc_h4)==len(sol_h4)
    assert sol_h4["open_time"].iloc[0]==pd.Timestamp("2026-01-01T00:00Z")
    engine=orig.StrategyEngine(cfg)
    flow=orig.FlowFeatures() # original OPTIONAL soft features MISSING, not fake retrospective data
    timestamps=sol_h1["open_time"]
    h4_times=sol_h4["open_time"]
    signals={}
    stats=collections.Counter()
    for j in range(1,len(sol_h1)-1):
        t=timestamps.iloc[j]
        if not (EVAL_FROM<=t<EVAL_END):continue
        current4_idx=int(h4_times.searchsorted(t,side="right"))-1
        assert current4_idx>=600,(t,current4_idx,"original V9 600 4h warmup missing")
        assert sol_h4["open_time"].iloc[current4_idx]<=t
        assert current4_idx>=1
        prev_complete_end=sol_h4["open_time"].iloc[current4_idx-1]+pd.Timedelta(hours=4)
        assert prev_complete_end<=t,("FUTURE_4H_CONTEXT",t,prev_complete_end)
        # Origin author fetch_klines returns latest incomplete 1h + incomplete 4h:
        # both original methods use [-2] for last fully closed 1h and 4h.
        one=sol_h1.iloc[max(0,j+1-600):j+1]
        sol_four=sol_h4.iloc[max(0,current4_idx+1-600):current4_idx+1]
        btc_four=btc_h4.iloc[max(0,current4_idx+1-600):current4_idx+1]
        ev=engine.build_evidence(one,sol_four,btc_four,flow)
        stats[f"raw_{ev.signal}"]+=1
        stats[f"reason_{ev.blocked_reason}"]+=1
        if ev.signal in ("LONG","SHORT"):
            assert ev.strategy=="PULLBACK_4",(t,ev.strategy)
            assert ev.pullback_long_confirm_votes==4 if ev.signal=="LONG" else ev.pullback_short_confirm_votes==4
            assert pd.Timestamp(ev.signal_time)==timestamps.iloc[j-1],("BAD_1H_SIGNAL_TIMESTAMP",t,ev.signal_time,timestamps.iloc[j-1])
            stats[f"approved_{ev.signal}"]+=1
        signals[int(t.value//10**6)]={
            "time":t,"evidence":ev,"atr":float(ev.atr),
            "score":float(ev.long_score if ev.signal=="LONG" else ev.short_score),
            "signal_bar_open":ev.signal_time,"closed_4h_bar_start":str(sol_h4["open_time"].iloc[current4_idx-1]),
            "last_closed_1h":str(timestamps.iloc[j-1]),
            "last_closed_4h":str(sol_h4["open_time"].iloc[current4_idx-1]),
            "next_4h_partial":str(sol_h4["open_time"].iloc[current4_idx]),
            "one_frame":one}
    print("A198_ACTUAL_ORIGINAL_AUTHOR_BUILD_EVIDENCE_OUTPUT",dict(stats),flush=True)
    return cfg,engine,signals,dict(stats)

def mark_candle_dict(data):
    rows=json.loads((data/"SOL_USDT_USDT-1h-funding_rate.json").read_text())
    # Original Binance settled funding only on actual settlement hours.
    d={}
    for r in rows:
        t=int(r[0]);v=float(r[1])
        if v!=0:
            assert t%3600000==0 and abs(v)<.03,(t,v)
            d[t]=v
    assert len(d)>400
    return d

def live_state_proxy(orig,cfg,state):
    # Call AUTHOR's update_trailing and evaluate_position_exit, not a copy of their formulas.
    mock=types.SimpleNamespace(cfg=cfg,state=types.SimpleNamespace(trade=state),
       store=types.SimpleNamespace(save=lambda *_:None),
       f=types.SimpleNamespace(tick_size=.01))
    def round_price(side,p):
        return float(math.floor(p*100+1e-8)/100) if side=="LONG" else float(math.ceil(p*100-1e-8)/100)
    def replace_stop(value):
        mock.state.trade.sl_price=value
        return True
    mock.round_price=round_price
    mock.replace_stop=replace_stop
    return mock

def compute_pnl(trade,side,exitprice,qty,fee,slip,reason,at,wallet):
    execution=exitprice*(1-slip if side=="LONG" else 1+slip)
    amount=(execution-trade.entry_price)*qty*(1 if side=="LONG" else -1)
    commission=qty*execution*fee
    wallet+=amount-commission
    trade.remaining_qty-=qty
    trade._realized+=amount-commission
    trade._exit_count+=1
    trade._last_exit=reason
    trade._exit_at=at
    return wallet

def replay(orig,cfg,engine,signals,data,settlements,mode,fee_scenario):
    fee,slip=PAIR_FEE[fee_scenario]
    rows=json.loads((data/"SOL_USDT_USDT-5m-futures.json").read_text())
    # 5m original market rows from Binance Vision. No 5m mark prices currently.
    rows=[r for r in rows if int(EVAL_FROM.value//10**6)<=r[0]<int(EVAL_END.value//10**6)]
    expected=int((EVAL_END-EVAL_FROM).total_seconds()/300)
    assert len(rows)==expected and all(r[0]==rows[0][0]+i*300000 for i,r in enumerate(rows))
    wallet=DEFAULT_CAPITAL
    position=None;vmock=None;entry_data=None
    profits=[];reports=[];wallet_trace=[]
    counters=collections.Counter()
    cooldown=0
    one_h_ms=3600000
    for candle_index,(t,o,high,low,close,vol) in enumerate(rows):
        at=pd.Timestamp(t,unit='ms',tz='UTC')
        assert t%300000==0
        # Funding settles on this hour. Charge ONLY existing position before opening new one.
        if position is not None and t in settlements:
            amt=position.remaining_qty*o*settlements[t]*(1 if position.side=="LONG" else -1)
            wallet-=amt
            position._realized-=amt
            position._funding+=amt
        # Process position-only signal exits at hourly boundary AFTER preceding candle complete.
        sig=signals.get(t)
        if position is not None and sig is not None:
            reason=orig.SOLRegimeBot.evaluate_position_exit(vmock,sig["evidence"],sig["one_frame"])
            if reason is not None:
                wallet=compute_pnl(position,position.side,o,position.remaining_qty,fee,slip,"SOURCE_"+reason,at,wallet)
                counters["exit_"+reason]+=1
        # Finalize closed position and impose author cooldown.
        if position is not None and position.remaining_qty<1e-10:
            d=position
            reports.append({"signal_bar":entry_data["signal_bar_open"],"entry":str(d._entry_at),
              "exit":str(d._exit_at),"direction":d.side,"exit_reason":d._last_exit,
              "pnl":round(d._realized,8),"wallet":round(wallet,6),"leverage":d._leverage,
              "entry_price":d.entry_price,"initial_stop":d._initial_sl,"TP1":d.tp1_price,
              "TP2":d.tp2_price,"atr":d.atr_at_entry,"score":entry_data["score"],
              "tp1_hit":bool(d.tp1_hit),"funding_paid":round(d._funding,6),
              "mfe_r":round(d.max_favorable_r,5),"initial_risk_usdt":round(d._initial_risk,6),
              "source_signal":entry_data["evidence"].strategy})
            profits.append(d._realized)
            cooldown=(cfg.cooldown_after_stop_bars if d._last_exit=="STOP"
               else cfg.cooldown_after_profit_bars if d._last_exit in ("TP2","TP1_TP2")
               else cfg.cooldown_after_signal_exit_bars)
            position=vmock=entry_data=None
        # Signal evaluation executes once at the exact next hour opening price.
        if t%one_h_ms==0 and position is None:
            if cooldown>0:
                cooldown-=1
                counters["cooldown_hour"]+=1
            elif sig is not None and sig["evidence"].signal in ("LONG","SHORT"):
                direction=sig["evidence"].signal
                entry=o*(1+slip if direction=="LONG" else 1-slip)
                atr=sig["atr"]
                if not math.isfinite(entry) or not math.isfinite(atr) or atr<=0:
                    counters["invalid_atr"]+=1
                else:
                    risk_distance=atr*cfg.pullback_stop_atr
                    stop=entry-risk_distance if direction=="LONG" else entry+risk_distance
                    lever=engine.required_leverage(entry,stop)
                    assert cfg.min_dynamic_leverage<=lever<=cfg.max_dynamic_leverage
                    notional=min(wallet*cfg.portfolio_margin_cap*lever,wallet*cfg.portfolio_margin_cap*3)
                    if mode=="external_1pct_cap":
                        notional=min(notional,max(0,wallet)*.01/(risk_distance/entry))
                    qty=notional/entry
                    c=qty*entry*fee
                    target=(1.5*risk_distance)/entry
                    estimated=2*fee+2*slip
                    if target<cfg.cost_gate_multiple*estimated:
                        counters["original_cost_gate_block"]+=1
                    elif notional<5.5 or qty<=0 or wallet-c<=0:
                        counters["low_notional_or_wallet"]+=1
                    else:
                        position=orig.TradeState(in_position=True,side=direction,strategy=sig['evidence'].strategy,
                            entry_price=entry,entry_qty=qty,remaining_qty=qty,tp1_qty=qty*cfg.tp1_close_pct,
                            entry_time=str(at),entry_signal_candle=sig["signal_bar_open"],entry_regime=sig["evidence"].sol_regime,
                            entry_score=sig["score"],atr_at_entry=atr,current_atr=atr,
                            risk_distance=risk_distance,sl_price=stop,
                            tp1_price=entry+(1 if direction=="LONG" else -1)*risk_distance*cfg.pullback_tp1_r,
                            tp2_price=entry+(1 if direction=="LONG" else -1)*risk_distance*cfg.pullback_tp2_r,
                            highest_price=entry,lowest_price=entry,last_mark_price=entry)
                        position._entry_at=at;position._initial_sl=stop
                        position._initial_risk=notional*(risk_distance/entry)
                        position._realized=-c;position._funding=0.0
                        position._last_exit=None;position._exit_count=0;position._leverage=lever
                        position._exit_at=None
                        wallet-=c
                        vmock=live_state_proxy(orig,cfg,position)
                        entry_data=sig
                        counters["trade_entered"]+=1
        # For current 5m bar, STOP takes priority if both stop and a profit target touched.
        if position is not None:
            p=position
            is_long=p.side=="LONG"
            stop_hit=(low<=p.sl_price if is_long else high>=p.sl_price)
            tp1_hit=(high>=p.tp1_price if is_long else low<=p.tp1_price)
            tp2_hit=(high>=p.tp2_price if is_long else low<=p.tp2_price)
            if stop_hit:
                # STOP_MARKET adverse gap model. At already-crossed open, worse fill.
                fill=min(o,p.sl_price) if is_long else max(o,p.sl_price)
                wallet=compute_pnl(p,p.side,fill,p.remaining_qty,fee,slip,"STOP",at,wallet)
                counters["stop"]+=1
            else:
                if tp1_hit and not p.tp1_hit and p.remaining_qty>0:
                    wallet=compute_pnl(p,p.side,p.tp1_price,min(p.tp1_qty,p.remaining_qty),fee,slip,"TP1_PARTIAL",at,wallet)
                    p.tp1_hit=True
                    p.sl_price=max(p.sl_price,p.entry_price+cfg.post_tp1_lock_r*p.risk_distance) if is_long else min(p.sl_price,p.entry_price-cfg.post_tp1_lock_r*p.risk_distance)
                    counters["tp1"]+=1
                if tp2_hit and p.remaining_qty>0:
                    wallet=compute_pnl(p,p.side,p.tp2_price,p.remaining_qty,fee,slip,"TP2",at,wallet)
                    counters["tp2"]+=1
            if p.remaining_qty>1e-10:
                # AUTHOR's source update_trailing called with 5m CLOSE as point-in-time
                # stand-in for actual polled mark (unavailable at historical 15s rate).
                orig.SOLRegimeBot.update_trailing(vmock,close)
        if position is not None and position.remaining_qty<1e-10:
            d=position
            reports.append({"signal_bar":entry_data["signal_bar_open"],"entry":str(d._entry_at),
              "exit":str(d._exit_at),"direction":d.side,"exit_reason":d._last_exit,
              "pnl":round(d._realized,8),"wallet":round(wallet,6),"leverage":d._leverage,
              "entry_price":d.entry_price,"initial_stop":d._initial_sl,"TP1":d.tp1_price,
              "TP2":d.tp2_price,"atr":d.atr_at_entry,"score":entry_data["score"],
              "tp1_hit":bool(d.tp1_hit),"funding_paid":round(d._funding,6),
              "mfe_r":round(d.max_favorable_r,5),"initial_risk_usdt":round(d._initial_risk,6),
              "source_signal":entry_data["evidence"].strategy})
            profits.append(d._realized)
            cooldown=cfg.cooldown_after_stop_bars if d._last_exit=="STOP" else cfg.cooldown_after_profit_bars
            position=vmock=entry_data=None
        equity=wallet + ((close-position.entry_price)*position.remaining_qty*(1 if position.side=="LONG" else -1) if position else 0)
        wallet_trace.append(max(0,equity))
    if position is not None:
        t,o,hi,lo,c,v=rows[-1]
        at=pd.Timestamp(t,unit="ms",tz="UTC")
        wallet=compute_pnl(position,position.side,c,position.remaining_qty,fee,slip,"EOD",at,wallet)
        d=position
        reports.append({"signal_bar":entry_data["signal_bar_open"],"entry":str(d._entry_at),
              "exit":str(d._exit_at),"direction":d.side,"exit_reason":"EOD",
              "pnl":round(d._realized,8),"wallet":round(wallet,6),"leverage":d._leverage,
              "entry_price":d.entry_price,"initial_stop":d._initial_sl,"TP1":d.tp1_price,
              "TP2":d.tp2_price,"atr":d.atr_at_entry,"score":entry_data["score"],
              "tp1_hit":bool(d.tp1_hit),"funding_paid":round(d._funding,6),
              "mfe_r":round(d.max_favorable_r,5),"initial_risk_usdt":round(d._initial_risk,6),
              "source_signal":entry_data["evidence"].strategy})
        profits.append(d._realized)
        wallet_trace[-1]=wallet
    assert abs(DEFAULT_CAPITAL+sum(profits)-wallet)<.005,(mode,fee_scenario,wallet,sum(profits))
    gross_wins=sum(p for p in profits if p>0)
    gross_losses=-sum(p for p in profits if p<0)
    if gross_losses==0:
        PF=float("inf") if gross_wins>0 else 0.0
    else:PF=gross_wins/gross_losses
    top3=sum(sorted((p for p in profits if p>0),reverse=True)[:3])
    drawdown=0.;peak=DEFAULT_CAPITAL
    for value in wallet_trace:
        peak=max(peak,value)
        drawdown=max(drawdown,(peak-value)/peak)
    n=len(profits)
    summary={"schema":"A198_ORIGINAL_V9_SOURCE_SIGNAL_INDEPENDENT_5M_PROXY",
      "mode":mode,"fee_scenario":fee_scenario,"starting_USDT":DEFAULT_CAPITAL,"ending_USDT":round(wallet,4),
      "return_pct":round((wallet/DEFAULT_CAPITAL-1)*100,4),
      "net_USDT":round(sum(profits),4),"trades":n,
      "winrate_pct":round(100*sum(p>0 for p in profits)/max(1,n),3),
      "profit_factor":round(PF,5),"max_drawdown_pct":round(drawdown*100,5),
      "top3_gross_win_fraction":round(top3/gross_wins,5) if gross_wins else None,
      "top3_net_fraction":round(top3/sum(profits),5) if sum(profits)>0 else None,
      "long_PnL":round(sum(t['pnl'] for t in reports if t['direction']=="LONG"),4),
      "short_PnL":round(sum(t['pnl'] for t in reports if t['direction']=="SHORT"),4),
      "average_R":round(sum(t['pnl']/t['initial_risk_usdt'] for t in reports if t['initial_risk_usdt']>0)/max(1,n),5),
      "fee_per_side":fee,"slippage_per_fill":slip,
      "reason_counts":dict(counters),
      "first_entry":reports[0]['entry'] if reports else None,
      "last_entry":reports[-1]['entry'] if reports else None}
    return summary,reports

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--datadir",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    orig,blob=load_source(args.source)
    d=Path(args.datadir)/"futures"
    cfg,engine,signals,stats=prepare_signals(orig,d)
    settlements=mark_candle_dict(d)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    report={"schema":"EMBER_A198_ORIGINAL_SOURCE_SIGNAL_AND_CUSTOM_EXECUTION_V9_4_SCENARIOS",
      "original_repo":"kboranyldz/sol-trading-research",
      "upstream_commit":"df3dcb722f1814f9eccf5ebd72facced13063a3e",
      "upstream_blob":blob,"timeframe":"1h/4h","exec_proxy":"real Binance Vision SOL 5m conservative stop-first",
      "signal_source":"unchanged import StrategyEngine.build_evidence, add_indicators and required_leverage from pinned original source",
      "actual_V9_native_historical_backtester_provided_by_author":False,
      "one_h_signals_checked":len(signals),"signal_funnel":stats,"scenarios":{},
      "limitations":["Historical point-in-time taker OI funding flow SOFT signal modifiers missing, explicit source FlowFeatures None",
      "Historical 5m trade-price proxy for Binance mark STOP triggers (no 5m mark), live may differ",
      "Original author polling every 15sec, proxy checks 5min and source trailing uses 5m close as mark",
      "Regime/indicator values computed from one full causal 1h/4h chronological series rather than source rerun with only 600 candles each poll; warmup checked >=600",
      "No exchange order book, spread, position partial fill, liquidation or API errors modeled",
      "Actual past 2026 history used by author; no untouched genuine OOS",
      "Risk 1pct is separate mechanical sizing overlay, NOT native original risk engine; no strategy optimization",
      "No Binance account, real, paper or simulated scheduled orders"]}
    for mode in RISK_MODE:
        for f in PAIR_FEE:
            summary,receipts=replay(orig,cfg,engine,signals,d,settlements,mode,f)
            assert len(receipts)==summary["trades"]
            check=sum(t['pnl'] for t in receipts)
            assert abs(check-summary["net_USDT"])<0.01
            label=f"{mode}__{f}"
            (out/(label+"__trades.json")).write_text(json.dumps(receipts,indent=2,ensure_ascii=False)+"\n")
            report["scenarios"][label]=summary
            print("A198_ORIGINAL_V9_AUTHOR_SIGNAL_PROXY_RESULT",label,
                "trades",summary["trades"],"net",summary["return_pct"],
                "PF",summary["profit_factor"],"DD",summary["max_drawdown_pct"],flush=True)
    report["pre_registered_basic_gate"]={
      label:bool(z["trades"]>=20 and z["return_pct"]>0 and z["profit_factor"]>=1.2
             and z["max_drawdown_pct"]<=15 and z["top3_gross_win_fraction"] is not None
             and z["top3_gross_win_fraction"]<.60)
      for label,z in report["scenarios"].items()}
    report["robust_both_fee_models_AND_risk_sizing"]=all(report["pre_registered_basic_gate"].values())
    (out/"A198_V9_ORIGINAL_SIGNALS_INDEPENDENT_EXECUTION_PROXY_RESULTS.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("A198_ORIGINAL_SOURCE_SIGNAL_FOUR_INDEPENDENT_PROXY_BACKTESTS_DONE",json.dumps(report["pre_registered_basic_gate"]),flush=True)

if __name__=="__main__":main()
