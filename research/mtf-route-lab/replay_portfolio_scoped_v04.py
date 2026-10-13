#!/usr/bin/env python3
"""Replay already computed, frozen v0.3 ideas across five symbols.

Accounting-only fix: idea identity is (symbol, original idea ID), rather than
using an unscoped ID which collides for different trading pairs.
No strategy or signal parameters are changed, and no orders are sent.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path
from mtf_engine import load_csv
from paper_portfolio_v03 import portfolio
from run_research_v03 import SYMBOLS, FTA, COSTS


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def scope_row(symbol, original):
    if original.get('symbol') not in (None, symbol):
        raise ValueError('Symbol mismatch in idea: '+str(original.get('symbol')))
    if not original.get('id'): raise ValueError('Missing source ID')
    # Preserve raw ID as audit evidence, but make portfolio ID pair-scoped.
    return {**original, 'symbol':symbol,'source_id':original['id'],'id':f'{symbol}|{original["id"]}'}


def route_stats(trades):
    out={}
    for route in ('A_VC_IMB_SNR','B_IDM','C_BOS_15M_PROXY'):
        t=[x for x in trades if x['route']==route]
        gain=sum(x['pnl_quote'] for x in t if x['pnl_quote']>0)
        loss=-sum(x['pnl_quote'] for x in t if x['pnl_quote']<0)
        out[route]={'closed_trades':len(t),'wins':sum(x['pnl_quote']>0 for x in t),
                    'net_quote_pnl':round(sum(x['pnl_quote'] for x in t),6),
                    'pf':round(gain/loss,6) if loss else None,
                    'win_rate':round(sum(x['pnl_quote']>0 for x in t)/len(t),6) if t else None}
    return out


def run(root, out):
    data=root/'data'/'history'
    independent=root/'results_04/full_validation/fixed_03_grid/independent_grid'
    doc=json.loads((independent/'SUMMARY.json').read_text(encoding='utf-8'))
    if doc['status']!='RESEARCH_REPLAY_DONE_NOT_VALIDATED':
        raise RuntimeError('No completed independent Futures run')
    from history_gate_v04 import audit_strict
    gate=audit_strict(data)
    if gate['status']!='READY_FOR_RESEARCH':
        raise RuntimeError('Strict gate blocked: '+str(gate['errors'][:3]))
    bars={symbol:load_csv(data/(symbol+'_15m.csv'),symbol,'15m')[0] for symbol in SYMBOLS}
    all_results={}
    for policy in FTA:
        for scenario,fee,slippage in COSTS:
            key=policy+'__'+scenario
            section=doc['results'][key]
            source_dir=independent/key
            ideas=[];source_sha={}
            for symbol in SYMBOLS:
                path=source_dir/(symbol+'_ideas.jsonl')
                source_sha[symbol]=sha(path)
                for interval in ('15m','1d'):
                    actual=sha(data/(symbol+'_'+interval+'.csv'))
                    expected=section['symbols'][symbol]['data_sha256'][interval]
                    if actual!=expected:raise ValueError('File hash differs from recorded independent run: '+symbol+' '+interval)
                for line in path.read_text(encoding='utf-8').splitlines():
                    if line.strip():ideas.append(scope_row(symbol,json.loads(line)))
            result=portfolio(bars,ideas,policy=policy,fee=fee,slippage=slippage)
            target=out/key;target.mkdir(parents=True,exist_ok=True)
            (target/'SUMMARY.json').write_text(json.dumps(result['summary'],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            (target/'TRADES.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in result['trades']),encoding='utf-8')
            (target/'LEDGER.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in result['ledger']),encoding='utf-8')
            (target/'EQUITY.json').write_text(json.dumps(result['closed_equity_curve'],ensure_ascii=False)+'\n',encoding='utf-8')
            all_results[key]={'model':result['summary'],'by_route':route_stats(result['trades']),
                              'source_ideas_sha256':source_sha,'portfolio_idea_count':len(ideas),
                              'portfolio_trades_sha256':sha(target/'TRADES.jsonl')}
            print(key,'closed',result['summary']['completed_model_trades'],
                  'return%',result['summary']['closed_equity_return_pct'],
                  'max_mtm_dd%',result['summary']['max_bar_close_MTM_drawdown_pct'],flush=True)
    summary={'status':'PORTFOLIO_OHLC_PROXY_DONE_NOT_VALIDATED','history_gate':'READY_FOR_RESEARCH',
             'no_order_placement':True,'engine':'unchanged frozen MTF 0.3',
             'portfolio_idea_id_scope':'symbol|source_idea_id',
             'model_fill_not_exchange_ack':True,'no_funding_liquidation':True,
             'course_visual_labels_verified':0,'untouched_oos':False,
             'cash_initial_usd':1000.0,'scenarios':all_results}
    out.mkdir(parents=True,exist_ok=True)
    (out/'FINAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--out',default='results_04/portfolio_scoped_replay')
    a=p.parse_args();run(Path(a.root).resolve(),Path(a.out).resolve())
