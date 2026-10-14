#!/usr/bin/env python3
"""Pinned paired experiment: frozen v0.3 vs v0.5 as-of parent lifecycle.

Both periods/FTA/costs fixed ahead of computation. No threshold search.
Inputs must exactly match previously checked Binance USD-M Futures OHLCV SHAs.
No trading APIs or live orders, only candle-touch simulation.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
from mtf_engine import load_csv
from mtf_engine_v05 import route_replay
from paper_portfolio_v03 import portfolio
def scope_row(symbol, original):
    if original.get('symbol') not in (None,symbol):raise ValueError('Symbol mismatch')
    if not original.get('id'):raise ValueError('Missing idea ID')
    return {**original,'symbol':symbol,'source_id':original['id'],'id':f'{symbol}|{original["id"]}'}

def route_stats(trades):
    out={}
    for route in ('A_VC_IMB_SNR','B_IDM','C_BOS_15M_PROXY'):
        a=[x for x in trades if x['route']==route]
        gains=sum(x['pnl_quote'] for x in a if x['pnl_quote']>0)
        losses=-sum(x['pnl_quote'] for x in a if x['pnl_quote']<0)
        out[route]={'trades':len(a),'wins':sum(x['pnl_quote']>0 for x in a),
                    'pnl_quote':round(sum(x['pnl_quote'] for x in a),6),
                    'profit_factor':round(gains/losses,6) if losses else None}
    return out

SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
FTA=('COURSE_PARENT_FTA','V22_FIRST_OBSTACLE')
COSTS=(('BASE',.0005,.0002),('COST_X2',.001,.0004))
BTC_BAD_SIGNAL_AT='2026-05-22T12:15:00Z'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(data_dir,baseline_independent,baseline_portfolio,out,year):
    data_dir=Path(data_dir);baseline_independent=Path(baseline_independent);baseline_portfolio=Path(baseline_portfolio);out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((baseline_independent/'SUMMARY.json').read_text())
    if baseline['status']!='RESEARCH_REPLAY_DONE_NOT_VALIDATED':raise RuntimeError('Baseline independent history not verified')
    if tuple(baseline['universe'])!=SYMBOLS:raise RuntimeError('Unexpected baseline symbol universe')
    if year not in (2025,2026):raise ValueError('year')
    # QA was completed on these archived inputs; additionally assert byte-exact hashes
    # for each symbol and scenario against the independently recorded frozen replay.
    market={}
    for sym in SYMBOLS:
        market[sym]={}
        for tf in ('15m','1d'):
            fp=data_dir/f'{sym}_{tf}.csv';actual=digest(fp)
            for policy in FTA:
                for cost,_,_ in COSTS:
                    expected=baseline['results'][policy+'__'+cost]['symbols'][sym]['data_sha256'][tf]
                    if actual!=expected:raise RuntimeError('USD-M historical input SHA mismatch '+sym+' '+tf)
            bars,_=load_csv(fp,sym,tf)
            market[sym][tf]=bars
        bars=market[sym]['15m'];a=bars[0].start;b=bars[-1].end
        expected_start='2025-02-01T00:00:00Z' if year==2025 else '2026-04-01T00:00:00Z'
        expected_end='2026-01-01T00:00:00Z' if year==2025 else '2026-10-13T00:00:00Z'
        from mtf_engine import ms
        if a!=ms(expected_start) or b!=ms(expected_end):raise RuntimeError('Unexpected date range '+sym)
    final={}
    for policy in FTA:
        for cost,fee,slippage in COSTS:
            key=policy+'__'+cost;ideas=[];by_symbol={};diag=Counter()
            for sym in SYMBOLS:
                inp=market[sym]
                fresh=route_replay(inp['15m'],sym,native={'1d':inp['1d']},fta_policy=policy,fee=fee,slippage=slippage)
                rows=fresh['qualified_ideas']
                prevfile=baseline_independent/key/f'{sym}_ideas.jsonl'
                prev=[json.loads(s) for s in prevfile.read_text().splitlines() if s.strip()]
                oldids={i['id'] for i in prev};newids={i['id'] for i in rows}
                removed=oldids-newids;added=newids-oldids
                changes={'baseline_ideas':len(prev),'new_ideas':len(rows),'removed':len(removed), 'added':len(added),
                         'removed_by_route':dict(Counter(x['route'] for x in prev if x['id'] in removed)),
                         'added_by_route':dict(Counter(x['route'] for x in rows if x['id'] in added)),
                         'invalidated_gate_counts':{k:v for k,v in fresh['diagnostics'].items() if k.endswith('_AT_IDEA')},
                         'removed_examples':[{'id':x['id'],'at':x['at'],'route':x['route'],'parent_id':x['parent_id']} for x in prev if x['id'] in removed][:12],
                         'input_sha256':{tf:digest(data_dir/f'{sym}_{tf}.csv') for tf in ('15m','1d')}}
                by_symbol[sym]=changes
                for k,v in fresh['diagnostics'].items():diag[k]+=v
                ideas.extend(scope_row(sym,x) for x in rows)
                if year==2026 and sym=='BTCUSDT' and key=='COURSE_PARENT_FTA__BASE':
                    was=[x for x in prev if x.get('at')==BTC_BAD_SIGNAL_AT and x['side']=='LONG' and x['parent_id']=='4h:IMB_LONG:1779393600000:']
                    now=[x for x in rows if x.get('at')==BTC_BAD_SIGNAL_AT and x['side']=='LONG' and x['parent_id']=='4h:IMB_LONG:1779393600000:']
                    changes['BTC_MAY22_2026_invalid_parent_regression']={'baseline_ideas':len(was),'repaired_ideas':len(now)}
                    if not was:raise AssertionError('Known BTC 2026-05-22 fixture missing in frozen baseline')
                    if now:raise AssertionError('Known BTC invalid 4H POI still generated as LONG')
            result=portfolio({sym:market[sym]['15m'] for sym in SYMBOLS},ideas,policy=policy,fee=fee,slippage=slippage)
            dst=out/key;dst.mkdir(parents=True,exist_ok=True)
            (dst/'TRADES.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result['trades']))
            (dst/'LEDGER.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result['ledger']))
            (dst/'SUMMARY.json').write_text(json.dumps(result['summary'],ensure_ascii=False,indent=2)+'\n')
            (dst/'EQUITY.json').write_text(json.dumps(result['closed_equity_curve'])+'\n')
            base=json.loads((baseline_portfolio/key/'SUMMARY.json').read_text())
            new=result['summary']
            final[key]={'old':base,'new':new,'return_delta_pp':round(new['closed_equity_return_pct']-base['closed_equity_return_pct'],6),
                        'by_route':route_stats(result['trades']),'by_symbol':by_symbol,'diag_gate':{k:v for k,v in diag.items() if k.endswith('_AT_IDEA')},
                        'idea_count':len(ideas),'trade_sha256':digest(dst/'TRADES.jsonl')}
            print(year,key,'ideas',len(ideas),'trades',new['completed_model_trades'],
                  'return',new['closed_equity_return_pct'],'vs',base['closed_equity_return_pct'],'delta_pp',final[key]['return_delta_pp'],flush=True)
    overall={'status':'V05_LIFECYCLE_COMPARISON_DONE_NOT_COURSE_VALIDATION','year':year,
             'data_source':'Previously SHA-checked Binance USD-M futures/um, byte-exact baseline input, non-synthetic',
             'model':'POI as-of guard; 1H invalidation predicate unchanged from frozen 0.3; other course proxies unchanged',
             'underlying_model':'OHLC touch; no order acknowledgments/funding/liquidations/real bid-ask; no course visual labels',
             'no_parameter_selection':True,'is_prospective_oos':False,'scenarios':final}
    (out/'V05_COMPARISON.json').write_text(json.dumps(overall,ensure_ascii=False,indent=2)+'\n')
    return overall

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('data-dir','baseline-independent','baseline-portfolio','out'):
        p.add_argument('--'+n,required=True)
    p.add_argument('--year',type=int,choices=(2025,2026),required=True)
    x=p.parse_args()
    run(x.data_dir,x.baseline_independent,x.baseline_portfolio,x.out,x.year)
