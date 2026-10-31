#!/usr/bin/env python3
"""A212 independent genuine two-leg cash-and-carry / selective 9-rate carry replay.
Public Binance Vision SPOT+PERP+MARK+actual settled FUNDING, source SHA for
all ZIP and CSV, NO trade API, NO invented funding-only revenue.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,time,urllib.request,statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile

COINS=("BTC","ETH","SOL","LINK")
YEARS=(2024,2025,2026)
MONTHS=(5,6,7,8,9)
KINDS=("spot","perp","mark","funding")
HOUR=3_600_000
WINDOW_START_DAY=13
SOURCE_START_DAY=1
BASE_SPOT="https://data.binance.vision/data/spot/monthly"
BASE_FUTURES="https://data.binance.vision/data/futures/um/monthly"
FEE_SCENARIOS={
"base":{"spot_fee":.0010,"perp_fee":.0005,"slippage":.0001},
"stress":{"spot_fee":.0015,"perp_fee":.00125,"slippage":.0003}}
MODES=("always","selective")
THRESHOLD=.0001
LOOKBACK_SETTLEMENTS=9
WALLET=1000.
SPOT_NOMINAL=100.
PERP_MARGIN_RESERVE_MULT=3.
MAINT_RESERVE=.015 # 0.5% maintenance + 1.0% stress buffer
def ms(x):
    v=int(x)
    if v>100_000_000_000_000:
        assert v%1000==0
        v//=1000
    assert 1_600_000_000_000<v<1_900_000_000_000,v
    return v
def collect(job):
    year,coin,kind,mon=job;sym=coin+"USDT";m=f"{year}-{mon:02d}"
    if kind=="spot":u=f"{BASE_SPOT}/klines/{sym}/1h/{sym}-1h-{m}.zip"
    elif kind=="perp":u=f"{BASE_FUTURES}/klines/{sym}/1h/{sym}-1h-{m}.zip"
    elif kind=="mark":u=f"{BASE_FUTURES}/markPriceKlines/{sym}/1h/{sym}-1h-{m}.zip"
    elif kind=="funding":u=f"{BASE_FUTURES}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip"
    else:raise ValueError(kind)
    last=None
    for k in range(3):
        try:
            request=urllib.request.Request(u,headers={"User-Agent":"EMBER-A212-REAL-HEDGED-CARRY-PAPER-RESEARCH"})
            with urllib.request.urlopen(request,timeout=120) as r:
                raw=r.read(12_000_000)
                assert r.status==200 and 50<len(raw)<12_000_000,(u,len(raw))
            with ZipFile(io.BytesIO(raw)) as z:
                names=[x for x in z.namelist() if x.endswith(".csv") and not x.startswith("__")]
                assert len(names)==1,(u,names)
                b=z.read(names[0])
            rows=list(csv.reader(io.StringIO(b.decode("utf-8-sig"))))
            assert len(rows)>1
            return job,rows,{"url":u,"zip_sha256":hashlib.sha256(raw).hexdigest(),
                             "csv_sha256":hashlib.sha256(b).hexdigest(),
                             "source_rows":len(rows)}
        except Exception as e:
            last=e
            if k<2:time.sleep(k+1)
    raise RuntimeError(("MISSING_GENUINE_A212_SOURCE",u,str(last)))

def klines(rows,year,coin,kind):
    vals=[]
    for x in rows:
        if not x or x[0].strip().lower().startswith(("open","time","timestamp")):continue
        assert len(x)>=6,(year,coin,kind,x[:3])
        t=ms(x[0]);o,h,l,c,v=map(float,x[1:6])
        assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0,(year,coin,kind,t,o,h,l,c)
        vals.append((t,o,h,l,c,v))
    return vals

def parse_funding(rows,year,coin):
    hd=[str(x).strip().lower().replace("_","") for x in rows[0]]
    def col(keys):
        for key in keys:
            if key in hd:return hd.index(key)
        raise RuntimeError(("BAD_FUNDING_HEADER",year,coin,hd))
    tc=col(("calctime","fundingtime","time","timestamp"))
    fc=col(("lastfundingrate","fundingrate"))
    out=[]
    for x in rows[1:]:
        if not x:continue
        t=ms(x[tc]);rate=float(x[fc])
        assert -0.03<rate<0.03
        out.append((t,rate))
    return out

def repair_mark(rows,year,coin,receipts):
    low=int(datetime(year,5,1,tzinfo=timezone.utc).timestamp()*1000)
    high=int(datetime(year,10,1,tzinfo=timezone.utc).timestamp()*1000)
    vals={t:r for r in rows for t in [r[0]]}
    assert len(vals)==len(rows)
    missing=[low+i*HOUR for i in range((high-low)//HOUR)
             if low+i*HOUR not in vals]
    days=sorted(set(datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m-%d") for t in missing))
    assert len(days)<=45,("TOO_MANY_MARK_GAPS",year,coin,len(days))
    if days:
        def task(day):
            sym=coin+"USDT"
            url=f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/{sym}/1h/{sym}-1h-{day}.zip"
            req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A212-GENUINE-DAILY-MARK-REPAIR"})
            with urllib.request.urlopen(req,timeout=80) as v:
                raw=v.read(6_000_000)
                assert v.status==200 and 60<len(raw)<6_000_000
            with ZipFile(io.BytesIO(raw)) as z:
                fn=[n for n in z.namelist() if n.endswith(".csv")]
                assert len(fn)==1
                b=z.read(fn[0])
            data=klines(list(csv.reader(io.StringIO(b.decode("utf-8-sig")))),year,coin,"daily_mark")
            receipt={"url":url,"zip_sha256":hashlib.sha256(raw).hexdigest(),
                     "csv_sha256":hashlib.sha256(b).hexdigest()}
            return day,data,receipt
        with ThreadPoolExecutor(max_workers=12) as pool:
            for f in as_completed([pool.submit(task,d) for d in days]):
                day,records,receipt=f.result()
                receipts[f"{year}-{coin}-daily-repair-{day}"]=receipt
                for r in records:
                    if r[0] in vals:assert vals[r[0]]==r,("MONTH_DAILY_PRICE_CONFLICT",day)
                    else:vals[r[0]]=r
    assert len(vals)==(high-low)//HOUR,("STILL_MISSING_MARK_HOURS",year,coin,len(vals))
    return [vals[low+i*HOUR] for i in range((high-low)//HOUR)],len(missing)

def load_source():
    jobs=[(year,coin,kind,m) for year in YEARS for coin in COINS for kind in KINDS for m in MONTHS]
    d={};receipts={}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for f in as_completed([pool.submit(collect,j) for j in jobs]):
            job,rows,receipt=f.result()
            d[job]=rows
            receipts[f"{job[0]}-{job[1]}-{job[2]}-{job[3]:02d}"]=receipt
    data={};summary={}
    for year in YEARS:
        for coin in COINS:
            val={};rates=[]
            for kind in KINDS:
                rows=[]
                for m in MONTHS:
                    source=d[(year,coin,kind,m)]
                    if kind=="funding":rows.extend(parse_funding(source,year,coin))
                    else:rows.extend(klines(source,year,coin,kind))
                if kind=="funding":rates=sorted(rows)
                else:val[kind]=rows
            val["mark"],repaired=repair_mark(val["mark"],year,coin,receipts)
            start=int(datetime(year,5,1,tzinfo=timezone.utc).timestamp()*1000)
            finish=int(datetime(year,10,1,tzinfo=timezone.utc).timestamp()*1000)
            nh=(finish-start)//HOUR
            for kind in ("spot","perp","mark"):
                rows=val[kind]
                assert len(rows)==nh,(year,coin,kind,len(rows),nh)
                for i,row in enumerate(rows):
                    assert row[0]==start+i*HOUR,("SOURCE_GAP_DUP",year,coin,kind,i)
            pay={}
            for t,rate in rates:
                base=t-t%HOUR
                assert t%HOUR<=1000,(year,coin,"NOT_GRID_SETTLEMENT",t)
                assert base not in pay,("DUP_SETTLEMENT",year,coin,base)
                pay[base]=rate
            assert len(pay)>350,(year,coin,"NO_GENUINE_FUNDING",len(pay))
            data[(year,coin)]={**val,"funding":pay}
            summary[f"{year}-{coin}"]={
                "hourly_price_rows":nh,"funding_settlements":len(pay),
                "genuine_daily_mark_hour_recoveries":repaired,
                "all_three_leg_hourly_prices_contiguous":True
            }
            print("A212_FOUR_REAL_SOURCE_LEGS",year,coin,nh,len(pay),flush=True)
    return data,receipts,summary

def replay(data,year,coin,mode,scenario):
    sc=FEE_SCENARIOS[scenario]
    sp=data["spot"];fp=data["perp"];mk=data["mark"];pay=data["funding"]
    start=int(datetime(year,5,13,tzinfo=timezone.utc).timestamp()*1000)
    end=int(datetime(year,10,1,tzinfo=timezone.utc).timestamp()*1000)
    all_times=[r[0] for r in sp]
    starting_i=next(i for i,r in enumerate(sp) if r[0]==start)
    assert all_times[-1]==end-HOUR
    prior_rates=[]
    wallet=WALLET;peak=WALLET;maxdd=0
    active=None;trades=[];total_funding=0;total_fees=0;total_price_basis=0
    margin_risk_breach=False;min_perp_margin_ratio=1000.
    marked_equity_first_open=None
    for i in range(len(sp)):
        t=all_times[i]
        spot=sp[i];fut=fp[i];mark=mk[i]
        if t in pay and t<start:prior_rates.append(pay[t])
        if t<start:continue
        if t>=end:break
        # BEFORE this hour's settlement, use only previously observed funding.
        want=(mode=="always" or (len(prior_rates)>=LOOKBACK_SETTLEMENTS and
            statistics.fmean(prior_rates[-LOOKBACK_SETTLEMENTS:])>THRESHOLD))
        if active is not None and not want:
            q=active["qty"];sx=spot[1]*(1-sc["slippage"]);fx=fut[1]*(1+sc["slippage"])
            exitfees=q*sx*sc["spot_fee"]+q*fx*sc["perp_fee"]
            basis=q*((sx-active["entry_spot"])+(active["entry_perp"]-fx))
            pnl=basis+active["funding"]-active["entryfees"]-exitfees
            wallet+=pnl;total_fees+=exitfees;total_price_basis+=basis
            trades.append({"open_ms":active["time"],"close_ms":t,"coin":coin,
                "qty":q,"exit_reason":"selectivity_end","net_pnl_USDT":pnl,
                "price_basis_realized_USDT":basis,"funding_USDT":active["funding"],
                "roundtrip_fees_USDT":active["entryfees"]+exitfees,
                "spot_entry":active["entry_spot"],"perp_entry":active["entry_perp"],
                "spot_exit":sx,"perp_exit":fx})
            active=None
        if active is None and want:
            se=spot[1]*(1+sc["slippage"]);fe=fut[1]*(1-sc["slippage"])
            q=SPOT_NOMINAL/se
            entryfees=q*se*sc["spot_fee"]+q*fe*sc["perp_fee"]
            required=q*se+PERP_MARGIN_RESERVE_MULT*q*fe+entryfees
            if wallet>=required:
                active={"time":t,"qty":q,"entry_spot":se,"entry_perp":fe,
                    "entryfees":entryfees,"funding":0,"margin":PERP_MARGIN_RESERVE_MULT*q*fe}
                total_fees+=entryfees
        # actual settlement as of time t: new position at time t never receives a payment already settled at t
        if t in pay:
            prior_rates.append(pay[t])
            if active is not None and active["time"]<t:
                # Exact spot/short quantity q; mark price approximation at known current-hour OPEN.
                credit=active["qty"]*mark[1]*pay[t]
                active["funding"]+=credit
                total_funding+=credit
        # mark risk once per hour (not only closed trades)
        if active is None:
            equity=wallet
        else:
            q=active["qty"]
            spot_price=spot[4];perp_price=fut[4]
            basis_mark=q*((spot_price-active["entry_spot"])+(active["entry_perp"]-perp_price))
            equity=wallet+basis_mark+active["funding"]-active["entryfees"]
            # Perp collateral kept separate from spot wallet, cannot magically cross-margin after spot rises.
            collateral=active["margin"]+q*(active["entry_perp"]-perp_price)+active["funding"]
            coverage=collateral/(q*perp_price)
            min_perp_margin_ratio=min(min_perp_margin_ratio,coverage)
            if coverage<MAINT_RESERVE:margin_risk_breach=True
        if marked_equity_first_open is None:marked_equity_first_open=equity
        peak=max(peak,equity)
        maxdd=max(maxdd,(peak-equity)/peak)
    # At the end of last full 1h candle exit both legs with conservative taker/slip.
    if active is not None:
        q=active["qty"]
        sx=sp[-1][4]*(1-sc["slippage"]);fx=fp[-1][4]*(1+sc["slippage"])
        exitfees=q*sx*sc["spot_fee"]+q*fx*sc["perp_fee"]
        basis=q*((sx-active["entry_spot"])+(active["entry_perp"]-fx))
        pnl=basis+active["funding"]-active["entryfees"]-exitfees
        wallet+=pnl;total_fees+=exitfees;total_price_basis+=basis
        trades.append({"open_ms":active["time"],"close_ms":end,"coin":coin,
            "qty":q,"exit_reason":"period_final_close","net_pnl_USDT":pnl,
            "price_basis_realized_USDT":basis,"funding_USDT":active["funding"],
            "roundtrip_fees_USDT":active["entryfees"]+exitfees,
            "spot_entry":active["entry_spot"],"perp_entry":active["entry_perp"],
            "spot_exit":sx,"perp_exit":fx})
    assert all(r["open_ms"]<r["close_ms"] for r in trades)
    assert all(trades[i]["open_ms"]>=trades[i-1]["close_ms"] for i in range(1,len(trades)))
    assert abs(sum(t["net_pnl_USDT"] for t in trades)-(wallet-WALLET))<1e-8
    assert abs(sum(t["funding_USDT"] for t in trades)-total_funding)<1e-8
    assert abs(sum(t["roundtrip_fees_USDT"] for t in trades)-total_fees)<1e-8
    assert abs(sum(t["price_basis_realized_USDT"] for t in trades)-total_price_basis)<1e-8
    # 100USDT buy-and-hold spot only over same calendar, with matched spot fees and slippage.
    S_e=sp[starting_i][1]*(1+sc["slippage"])
    S_x=sp[-1][4]*(1-sc["slippage"])
    hold_q=SPOT_NOMINAL/S_e
    spot_hodl=hold_q*(S_x-S_e)-hold_q*S_e*sc["spot_fee"]-hold_q*S_x*sc["spot_fee"]
    source={
      "trades":len(trades),
      "wallet_profit_USDT":round(wallet-WALLET,6),
      "wallet_return_pct":round((wallet/WALLET-1)*100,6),
      "actual_funding_received_USDT":round(total_funding,6),
      "basis_price_pnl_after_slippage_USDT":round(total_price_basis,6),
      "four_leg_fees_paid_USDT":round(total_fees,6),
      "max_1h_marked_to_market_wallet_dd_pct":round(maxdd*100,6),
      "worst_perp_collateral_to_notional_ratio":round(min_perp_margin_ratio,6) if trades else None,
      "perp_margin_risk_breach":margin_risk_breach,
      "spot_only_100USDT_hold_benchmark_net_USDT":round(spot_hodl,6),
      "net_vs_cash_USDT":round(wallet-WALLET,6),
      "net_vs_spot_hold_USDT":round((wallet-WALLET)-spot_hodl,6),
      "winners":sum(t["net_pnl_USDT"]>0 for t in trades),
      "losers":sum(t["net_pnl_USDT"]<0 for t in trades),
      "mean_hold_days":round(statistics.fmean((t["close_ms"]-t["open_ms"])/86_400_000 for t in trades),5) if trades else None,
      "commission_model":sc.copy(),
      "source_mark_at_settlement_approximation":"genuine mark price current-hour OPEN; exact subsecond mark is unavailable",
    }
    return source,trades

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    a=ap.parse_args();folder=Path(a.out);folder.mkdir(parents=True,exist_ok=True)
    datasets,receipts,integrity=load_source()
    results={};ledgers={}
    for year in YEARS:
        results[str(year)]={}
        for coin in COINS:
            results[str(year)][coin]={}
            for mode in MODES:
                results[str(year)][coin][mode]={}
                for scenario in FEE_SCENARIOS:
                    r,t=replay(datasets[(year,coin)],year,coin,mode,scenario)
                    f=folder/f"A212_{year}_{coin}_{mode}_{scenario}_TWO_REAL_LEGS.json"
                    f.write_text(json.dumps(t,sort_keys=True,separators=(",",":"))+"\n")
                    assert len(json.loads(f.read_text()))==len(t)
                    ledgers[f.name]={"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"n":len(t)}
                    results[str(year)][coin][mode][scenario]=r
                    print("A212_REAL_TWO_LEG_REPLAY",year,coin,mode,scenario,r["trades"],r["wallet_return_pct"],flush=True)
    years={}
    for year in YEARS:
        years[str(year)]={}
        for mode in MODES:
            years[str(year)][mode]={}
            for fee in FEE_SCENARIOS:
                cells=[results[str(year)][c][mode][fee] for c in COINS]
                net=sum(r["wallet_profit_USDT"] for r in cells)
                spot=sum(r["spot_only_100USDT_hold_benchmark_net_USDT"] for r in cells)
                years[str(year)][mode][fee]={
                    "independent_4_partition_wallets_4000USDT_return_pct":round(net/40,6),
                    "all_four_wallets_combined_net_USDT":round(net,6),
                    "net_100USDT_each_coin_spot_benchmark_USDT":round(spot,6),
                    "beat_cash":net>0,"beat_spot_100USDT_each":net>spot,
                    "positive_coins":sum(r["wallet_profit_USDT"]>0 for r in cells),
                    "margin_risk_breaches":sum(r["perp_margin_risk_breach"] for r in cells),
                    "total_trade_count":sum(r["trades"] for r in cells),
                    "funding_received_USDT":round(sum(r["actual_funding_received_USDT"] for r in cells),6),
                    "price_basis_pnl_USDT":round(sum(r["basis_price_pnl_after_slippage_USDT"] for r in cells),6),
                    "four_leg_fee_USDT":round(sum(r["four_leg_fees_paid_USDT"] for r in cells),6),
                    "worst_individual_wallet_1h_mark_dd_pct":max(r["max_1h_marked_to_market_wallet_dd_pct"] for r in cells),
                    "PORTFOLIO_MAX_DRAWDOWN_NOT_COMPUTED":True
                }
    main_summary={}
    for mode in MODES:
        passes=all(years[str(y)][mode][scenario]["positive_coins"]>=2
          and years[str(y)][mode][scenario]["margin_risk_breaches"]==0
          and years[str(y)][mode][scenario]["beat_cash"]
          for y in YEARS for scenario in FEE_SCENARIOS)
        main_summary[mode]={"research_economy_gate":passes,
            "execution_approval":False}
    manifest={
      "schema":"A212_GENUINE_BOTH_SPOT_PERP_MARK_SETTLED_FUNDING_CARRY_TEST",
      "research_type":"INDEPENDENT_REPLAY_NOT_FREQTRADE_NATIVE",
      "source_idea":"Kureshi25/cryptobot funding_scan.py and selectivity_test.py, WITHOUT their funding-only engine",
      "param_rule":{"wallet_each_coin":WALLET,"spot_nominal":SPOT_NOMINAL,
        "same_coin_quantity_spot_and_short_perpetual":True,
        "perp_initial_margin_reserve_multiple":PERP_MARGIN_RESERVE_MULT,
        "period":"May13-Sep30 each 2024,2025,2026",
        "signal_funding_last_9_already_settled_greater_than":THRESHOLD,
        "modes":MODES,"fees":FEE_SCENARIOS,"market_order_only":True},
      "source_zip_csv_sha256":receipts,"source_integrity":integrity,
      "results":results,"per_year_4partition_wallet_summary":years,
      "research_gate":main_summary,
      "trade_log_sha256":ledgers,
      "no_full_portfolio_equity_curve":True,"execution_approval":False,
      "caveats":["Already investigated 2024-26 market periods in project, no pristine OOS",
        "Actual 1h mark open approximates subsecond funding settlement mark",
        "Market order slippage scenarios do not capture venue outages or order leg asynchrony",
        "Spot and perp quantities same; notional near 100 and 300USDT perp collateral reserve modeled",
        "Real perp liquidation thresholds and transfer failures are NOT faithfully exchange-modelled",
        "Four partitioned 1000USDT wallets not a unified rebalancing 4000USDT portfolio",
        "Spot baseline different risk exposure; matched spot notional but not risk-matched",
        "Short futures leg can liquidate even if spot leg rises, and collateral may not be transferable"]}
    out=folder/"A212_REAL_TWO_LEG_CARRY_2024_2025_2026_SHA_VERIFIED.json"
    out.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("A212_240_REAL_BINANCE_SPOT_PERP_MARK_FUNDING_SOURCES_AND_48_HEDGES_VERIFIED",
        json.dumps({"summary":years,"gates":main_summary},sort_keys=True),flush=True)
if __name__=="__main__":main()
