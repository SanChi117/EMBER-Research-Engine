"""SOURCE/PARITY gate: independently replay original P07/P10 entry/exit timing.

No optimization, no orders, no forward PAPER, no VERIFIED labels.
Signals are obtained from pinned *original* classes, execution is implemented
independently, and native engine ledgers are compared before any cost sensitivity.
P07 defaults have no hard stop or target; never silently add them to ORIGINAL.
Original P10 uses same-close fills; delayed-entry variant is explicitly a STRESS.
Funding uses real *signed* Binance USD-M settlement rows frozen separately.
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from run_trace import HERE, CSV, SOURCES, clone_and_check, prepare

FUND_CSV = HERE / "binance_usdtm_funding_20261101.csv"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def norm_event(row):
    return (row["symbol"], row["side"], int(row["entry_time"]),
            int(row["exit_time"]), round(float(row["entry_price"]), 8),
            round(float(row["exit_price"]), 8), row["reason"])


def cash_sums(rows):
    return {
        "gross_usd": round(sum(x["gross"] for x in rows), 6),
        "fee_usd": round(sum(x["fees"] for x in rows), 6),
        "spread_slip_usd": round(sum(x["spread_slippage"] for x in rows), 6),
        "funding_usd": round(sum(x["funding"] for x in rows), 6),
        "net_usd": round(sum(x["gross"] - x["fees"] - x["spread_slippage"] - x["funding"] for x in rows), 6),
        "trades": len(rows)
    }


def fund_for_trade(fund: pd.DataFrame, sym: str, side: int, notional: float, entry_ms: int, exit_ms: int):
    rows = fund.loc[
        (fund.symbol == sym) &
        (fund.funding_time_ms > entry_ms) & (fund.funding_time_ms < exit_ms)
    ]
    # Holding notional constant is the original source convention, not a mark-to-market margin model.
    return float(sum(side * notional * r for r in rows.funding_rate)), len(rows)


def validate_funding(fund):
    assert len(fund) == 570, len(fund)
    counts = {}
    for sym in SYMBOLS:
        x = fund.loc[fund.symbol == sym].sort_values("funding_time_ms")
        assert len(x) == 190
        assert x.funding_time_ms.is_unique
        diffs = x.funding_time_ms.diff().dropna()
        # Exchange timestamps can jitter a few milliseconds around 8-hour UTC boundaries.
        assert (diffs.sub(8 * 3600 * 1000).abs() < 20).all()
        counts[sym] = {"settlements": len(x),
                       "positive_rates": int((x.funding_rate > 0).sum()),
                       "negative_rates": int((x.funding_rate < 0).sum())}
    return counts


def compare_ledgers(actual, native):
    a = sorted(map(norm_event, actual))
    b = sorted(map(norm_event, native))
    same = len(a) == len(b) and a == b
    mismatches = [{"replay": x, "native": y}
                  for x, y in zip(a, b) if x != y][:5]
    return {"replay_count": len(a), "native_count": len(b),
            "all_events_exact_match": same, "first_mismatches": mismatches,
            "first20_replay": a[:20]}


def p07_replay(sub, orig_signals, funding, *, apply_funding):
    """Original exit precedence/entry timestamps, corrected one-time cash deductions."""
    entries, exits = orig_signals
    x = sub.reset_index(drop=True)
    cash = 10000.
    pos = None
    ledger = []
    for i in range(len(x)):
        if pos is not None and bool(exits.iloc[i]):
            next_bar = i+1 < len(x)
            exit_price = float(x.open.iat[i+1] if next_bar else x.close.iat[i])
            exit_ms = int(x.open_time.iat[i+1] if next_bar else x.close_time.iat[i])
            gross = pos["side"] * pos["units"] * (exit_price-pos["entry_price"])
            exit_fee = 0.0004 * pos["notional"]
            funding_cost, settlements = fund_for_trade(
                funding,pos["symbol"],pos["side"],pos["notional"],
                pos["entry_time"],exit_ms) if apply_funding else (0.,0)
            cash += gross-exit_fee-funding_cost
            ledger.append({
                **pos, "exit_time":exit_ms, "exit_price":exit_price, "gross":gross,
                "fees":pos["entry_fee"]+exit_fee, "spread_slippage":pos["friction"],
                "funding":funding_cost, "funding_settlements":settlements, "reason":"signal",
            })
            pos=None
        if pos is None and int(entries.iloc[i]) != 0 and float(x.volume.iat[i])>0 and i+1<len(x):
            side=int(entries.iloc[i])
            px=float(x.open.iat[i+1])
            notional=cash*.1
            if notional<=0:continue
            fee=notional*.0004
            # Default P07 source CostConfig: 5 bps spread and piecewise 1-2 bps slippage for ~$1k.
            bps=2. if notional>=1000. else 1.
            friction=notional*(5+bps)/10000
            cash-=fee+friction
            pos={"symbol":str(x.symbol.iat[i]),"side":side,
                 "entry_time":int(x.open_time.iat[i+1]),"entry_price":px,
                 "notional":notional,"units":notional/px,
                 "entry_fee":fee,"friction":friction}
    if pos is not None:
        exit_price=float(x.close.iat[-1])
        exit_ms=int(x.close_time.iat[-1])
        gross=pos["side"]*pos["units"]*(exit_price-pos["entry_price"])
        exit_fee=.0004*pos["notional"]
        funding_cost,settlements = fund_for_trade(
            funding,pos["symbol"],pos["side"],pos["notional"],pos["entry_time"],exit_ms
        ) if apply_funding else (0.,0)
        cash+=gross-exit_fee-funding_cost
        ledger.append({**pos,"exit_time":exit_ms,"exit_price":exit_price,
                       "gross":gross,"fees":pos["entry_fee"]+exit_fee,
                       "spread_slippage":pos["friction"],"funding":funding_cost,
                       "funding_settlements":settlements,"reason":"signal"})
    expected=10000.+sum(t["gross"]-t["fees"]-t["spread_slippage"]-t["funding"] for t in ledger)
    assert abs(cash-expected) < 1e-5, (cash,expected)
    return ledger, {"final_cash_usd":round(cash,6),"cash_identity_ok":True, **cash_sums(ledger)}


def p07_original(repo, frame):
    sys.path.insert(0,str(repo/"src"))
    from perplab.strategy.library.pullback_retest import PullbackRetest
    from perplab.engine.cost_model import CostConfig,CostModel
    from perplab.engine.simulator import Simulator
    return PullbackRetest, CostConfig,CostModel, Simulator


def p07_gate(repo,df, funding):
    PullbackRetest,CostConfig,CostModel,Simulator=p07_original(repo,df)
    out={}
    for sym in SYMBOLS:
        sub=prepare(df,sym,"1h")
        sub["symbol"]=sym
        ind=PullbackRetest().indicators(sub)
        signals=(PullbackRetest().entry_signal_vectorized(ind),
                 PullbackRetest().exit_signal_vectorized(ind))
        native_df=sub.copy()
        native_df["open_time"]=pd.to_datetime(native_df.open_time,unit="ms",utc=True)
        native=Simulator(native_df,CostModel(CostConfig()),funding_rates=None).run(
            PullbackRetest(),initial_capital=10000.,position_size_pct=.1)
        native_rows=[{"symbol":sym, "side":1 if t.side=="long" else -1,
                      "entry_time":int(t.entry_time.timestamp()*1000),
                      "exit_time":int(t.exit_time.timestamp()*1000),
                      "entry_price":t.entry_price,"exit_price":t.exit_price,
                      "reason":t.exit_reason} for t in native.trades]
        nofund, zero_stats=p07_replay(sub, signals, funding,apply_funding=False)
        funded, real_stats=p07_replay(sub, signals, funding,apply_funding=True)
        parity=compare_ledgers(nofund,native_rows)
        assert parity["all_events_exact_match"],(sym,parity["first_mismatches"])
        # Native discrepancy: double exit commission on top of trade.net_pnl.
        mismatch=10000.+sum(t.gross_pnl for t in native.trades)-sum(native.cost_breakdown.values())-float(native.equity_curve.equity.iloc[-1])
        assert abs(mismatch-sum(t.costs for t in native.trades))<1e-6
        out[sym]={
            "native_trade_event_parity":parity["all_events_exact_match"],
            "trades":len(nofund),"native_duplicate_exit_fees_usd":round(mismatch,5),
            "corrected_no_funding":zero_stats,"corrected_actual_signed_funding":real_stats,
            "funding_events_accrued":sum(r["funding_settlements"] for r in funded),
            "first2":parity["first20_replay"][:2]
        }
    return out


def p10_original(repo, df):
    sys.path.insert(0, str(repo/"src"))
    from crypto_trade.backtest_models import BacktestConfig, Signal
    # Prevent optional ML registry imports; strategy itself is original code.
    import types
    stub=types.ModuleType("crypto_trade.strategies")
    stub.__path__=[str(repo/"src"/"crypto_trade"/"strategies")]
    stub.NO_SIGNAL=Signal(direction=0,weight=0)
    sys.modules["crypto_trade.strategies"]=stub
    from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy
    import crypto_trade.backtest as nativebt
    master=df.loc[df.interval=="1h"].copy().sort_values(
        ["open_time","symbol"],kind="mergesort",ignore_index=True)
    # Feed original engine the same real OHLCV via a separate in-memory adapter.
    # Do not edit author backtest or substitute fabricated missing trade count fields.
    nativebt._build_master=lambda cfg:master.copy()
    cfg=BacktestConfig(symbols=SYMBOLS,interval="1h",max_amount_usd=1000.,
                       stop_loss_pct=2.,take_profit_pct=3.,timeout_minutes=120,
                       fee_pct=.1)
    native=nativebt.run_backtest(cfg,BbSqueezeStrategy())
    rows=[{"symbol":t.symbol,"side":t.direction,"entry_time":t.open_time,
           "exit_time":t.close_time,"entry_price":t.entry_price,
           "exit_price":t.exit_price,"reason":t.exit_reason} for t in native]
    strat=BbSqueezeStrategy()
    strat.compute_features(master)
    signals=[strat.get_signal(str(row.symbol),int(row.open_time)).direction
             for row in master.itertuples(index=False)]
    return master, signals, rows, len(native),native.total_signals


def p10_replay(master,signals,funding,*,next_open, friction_bps=0.):
    """Independent event-driven reproduction of original 2/3% stops and timeout.

    next_open=False = author idealized same-close fill. next_open=True = causal
    next-open with conservative same-bar SL priority and gap-through stop.
    """
    open_orders={}
    pending={}
    ledger=[]
    for i,bar in enumerate(master.itertuples(index=False)):
        sym=str(bar.symbol)
        op=float(bar.open);hi=float(bar.high);lo=float(bar.low)
        ct=int(bar.close_time);ot=int(bar.open_time)
        cc=float(bar.close); direction=int(signals[i])
        if next_open and sym in pending:
            record=pending.pop(sym)
            if sym not in open_orders:
                record.update({"entry_time":ot,"entry_price":op,
                               "stop":op*(1-.02*record["side"]),
                               "tp":op*(1+.03*record["side"]),
                               "timeout":ot+120*60000})
                open_orders[sym]=record
        record=open_orders.get(sym)
        if record is not None:
            side=record["side"]
            reason=None;exit_price=None;exit_time=ct
            if ot>=record["timeout"]:
                reason="timeout";exit_price=op;exit_time=ot
            else:
                stop=record["stop"];tp=record["tp"]
                if next_open and (side*(op-stop)<=0):
                    reason="stop_loss";exit_price=op;exit_time=ot
                elif next_open and (side*(op-tp)>=0):
                    reason="take_profit";exit_price=tp;exit_time=ot
                else:
                    sl=(lo<=stop if side==1 else hi>=stop)
                    tp_hit=(hi>=tp if side==1 else lo<=tp)
                    if sl and tp_hit:
                        if side==1 and op>=tp or side==-1 and op<=tp:
                            sl=False
                        else:tp_hit=False
                    if sl:reason="stop_loss";exit_price=stop
                    elif tp_hit:reason="take_profit";exit_price=tp
            if reason is not None:
                notional=record["notional"]
                gross=side*notional*(exit_price/record["entry_price"]-1)
                funding_cost,fs=fund_for_trade(funding,sym,side,notional,record["entry_time"],exit_time)
                ledger.append({
                    "symbol":sym,"side":side,
                    "entry_time":record["entry_time"],"exit_time":exit_time,
                    "entry_price":record["entry_price"],"exit_price":exit_price,
                    "reason":reason,"gross":gross,
                    "fees":notional*.001,  # author's README roundtrip fee = 0.1%
                    "spread_slippage":notional*friction_bps/10000.,
                    "funding":funding_cost,"funding_settlements":fs})
                del open_orders[sym]
        if direction !=0 and sym not in open_orders and sym not in pending:
            record={"symbol":sym,"side":direction,"notional":800.}
            if next_open:pending[sym]=record
            else:
                record.update({"entry_time":ct,"entry_price":cc,
                               "stop":cc*(1-.02*direction),
                               "tp":cc*(1+.03*direction),
                               "timeout":ct+120*60000})
                open_orders[sym]=record
    # The original forces end-of-data flatten at final available close per symbol.
    for sym,rec in open_orders.items():
        last=master.loc[master.symbol==sym].iloc[-1]
        ex=float(last["close"]);et=int(last["close_time"])
        gross=rec["side"]*rec["notional"]*(ex/rec["entry_price"]-1)
        f,n=fund_for_trade(funding,sym,rec["side"],rec["notional"],rec["entry_time"],et)
        ledger.append({"symbol":sym,"side":rec["side"],"entry_time":rec["entry_time"],
                       "exit_time":et,"entry_price":rec["entry_price"],
                       "exit_price":ex,"reason":"end_of_data","gross":gross,
                       "fees":rec["notional"]*.001,
                       "spread_slippage":rec["notional"]*friction_bps/10000.,
                       "funding":f,"funding_settlements":n})
    return ledger


def p10_gate(repo,df,funding):
    master,signals,native,count,total_signals=p10_original(repo,df)
    # The all-events comparator includes event/price and fill timing, not just signals.
    same=p10_replay(master,signals,funding,next_open=False)
    parity=compare_ledgers(same,native)
    if not parity["all_events_exact_match"]:
        raise AssertionError("P10 source trade/event parity mismatch: "+str(parity["first_mismatches"]))
    lag=p10_replay(master,signals,funding,next_open=True)
    events=compare_ledgers(lag,same)
    prices_changed=sum(1 for a,b in zip(sorted(same,key=lambda x:(x["symbol"],x["entry_time"])),
                                        sorted(lag,key=lambda x:(x["symbol"],x["entry_time"])))
                       if abs(a["entry_price"]-b["entry_price"])>1e-9)
    return {
        "source_engine_trades":count,"original_signal_events":total_signals,
        "all_trade_events_equal_independent":parity["all_events_exact_match"],
        "first20_original_trades":parity["first20_replay"],
        "same_close_signed_funding_diagnostic":cash_sums(same),
        "next_open_signed_funding_diagnostic":cash_sums(lag),
        "next_open_plus_10bps_extra_friction":cash_sums(
            p10_replay(master,signals,funding,next_open=True,friction_bps=10)),
        "same_vs_next_event_count_diff":len(lag)-len(same),
        "same_vs_next_first5_diffs":events["first_mismatches"],
        "entry_price_diffs_aligned_sort":prices_changed,
        "notice":"No mark liquidation, shared account MTM, liquidity, detailed spread; not a VERIFIED backtest."
    }


def main():
    df=pd.read_csv(CSV)
    df=df.loc[df.interval=="1h"].copy()
    df["symbol"]=df.symbol.astype(str)
    fund=pd.read_csv(FUND_CSV)
    metadata=validate_funding(fund)
    report={"dataset_sha256":hashlib.sha256(CSV.read_bytes()).hexdigest(),
            "funding_sha256":hashlib.sha256(FUND_CSV.read_bytes()).hexdigest(),
            "funding_validation":metadata, "p07":{},"p10":{},
            "status":"DIAGNOSTIC_SOURCE_LEDGER_REPLAY_NOT_ECONOMIC_VERIFICATION"}
    with tempfile.TemporaryDirectory(prefix="ember_originals_") as tmp:
        p07=clone_and_check(Path(tmp),"P07")
        p10=clone_and_check(Path(tmp),"P10")
        report["p07"]=p07_gate(p07,df,fund)
        report["p10"]=p10_gate(p10,df,fund)
    reportfile=HERE/"EXECUTION_REPLAY_LOCAL.json"
    reportfile.write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str))
    print("EMBER_EXECUTION_REPLAY="+json.dumps(report,ensure_ascii=False,default=str))
    assert all(r["native_trade_event_parity"] for r in report["p07"].values())
    assert report["p10"]["all_trade_events_equal_independent"]


if __name__=="__main__":
    main()
