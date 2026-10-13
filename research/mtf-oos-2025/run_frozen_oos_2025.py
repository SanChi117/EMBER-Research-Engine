#!/usr/bin/env python3
"""Frozen 0.3 strategy on previously untested 2025 Futures sample; PAPER only.

The historical period, universe, capital model, entry logic and 2x2 cost policy
are FIXED before looking at results. No alterations to mtf_engine.py or V2.2.
This is a retrospective, temporally separate check, not prospective validation.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from collections import Counter

import mtf_engine
import validate_history_v03 as hv
import run_research_v03 as research
from history_gate_v04 import audit_strict
from check_frozen_engine_v03 import check as core_check
from paper_portfolio_v03 import portfolio
from replay_portfolio_scoped_v04 import scope_row,route_stats

SYMBOLS = ('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
START_15M = '2025-01-01T00:00:00Z'
START_1D = '2024-01-01T00:00:00Z'
END = '2026-01-01T00:00:00Z'
PHASES_2025 = (
    ('JAN_APR','2025-01-01T00:00:00Z','2025-05-01T00:00:00Z'),
    ('MAY_AUG','2025-05-01T00:00:00Z','2025-09-01T00:00:00Z'),
    ('SEP_DEC','2025-09-01T00:00:00Z','2026-01-01T00:00:00Z'),
)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def finite_model(trades):
    wins=[t['pnl_quote'] for t in trades if t['pnl_quote']>0]
    losses=[t['pnl_quote'] for t in trades if t['pnl_quote']<0]
    return {'closed_model_trades':len(trades),'wins':len(wins),
            'pnl_quote':round(sum(wins)+sum(losses),6),
            'profit_factor':round(sum(wins)/(-sum(losses)),6) if losses else None}

def verify_period(data_dir, expected_end=END):
    if expected_end != END:
        raise ValueError('Frozen OOS end changed; no arbitrary windows or optimization')
    data_dir=Path(data_dir)
    if not (data_dir/'manifest_vision.json').exists():
        raise ValueError('OOS requires SHA256-verified Binance USD-M VISION manifest')
    with (data_dir/'manifest_vision.json').open(encoding='utf-8') as f: manifest=json.load(f)
    if len(manifest)!=10:raise ValueError('Expected exactly ten Futures manifest rows')
    if {(r['symbol'],r['tf']) for r in manifest}!={(s,tf) for s in SYMBOLS for tf in ('15m','1d')}:
        raise ValueError('Futures manifest universe/timeframes incorrect')
    if not all(str(src.get('url','')).startswith('https://data.binance.vision/data/futures/um/') for x in manifest for src in x.get('sources',[])):
        raise ValueError('Not sourced strictly from Binance USD-M VISION')
    old=hv.TF_START.copy()
    try:
        hv.TF_START.clear()
        hv.TF_START.update({'15m':mtf_engine.ms(START_15M),'1d':mtf_engine.ms(START_1D)})
        gate=audit_strict(str(data_dir),expected_end,SYMBOLS)
    finally:
        hv.TF_START.clear();hv.TF_START.update(old)
    if gate['status']!='READY_FOR_RESEARCH':
        raise ValueError('Strict OHLCV+manifest gate: '+repr(gate['errors'][:5]))
    for s in SYMBOLS:
        for tf in ('15m','1d'):
            bars,_=mtf_engine.load_csv(data_dir/f'{s}_{tf}.csv',s,tf)
            expected_start=mtf_engine.ms(START_15M if tf=='15m' else START_1D)
            if bars[0].start!=expected_start or bars[-1].end!=mtf_engine.ms(END):
                raise ValueError('OOS interval not frozen '+s+' '+tf)
    return gate

def execute(data_dir,out):
    data_dir=Path(data_dir).resolve();out=Path(out).resolve()
    out.mkdir(exist_ok=True,parents=True)
    c=core_check(Path(mtf_engine.__file__))
    if c['status']!='PASS_CORE_UNCHANGED':raise RuntimeError('Core hash does not match locked MTF 0.3')
    gate=verify_period(data_dir)
    phases_previous=research.PHASES
    starts_previous=hv.TF_START.copy()
    try:
        research.PHASES=PHASES_2025
        hv.TF_START.clear();hv.TF_START.update({'15m':mtf_engine.ms(START_15M),'1d':mtf_engine.ms(START_1D)})
        independent=research.run(str(data_dir),str(out/'independent'),END,SYMBOLS)
    finally:
        research.PHASES=phases_previous
        hv.TF_START.clear();hv.TF_START.update(starts_previous)
    if independent['status']!='RESEARCH_REPLAY_DONE_NOT_VALIDATED':raise RuntimeError('No complete independent replay')
    bars={s:mtf_engine.load_csv(data_dir/f'{s}_15m.csv',s,'15m')[0] for s in SYMBOLS}
    scenarios={}
    for policy in research.FTA:
        for case,fee,slippage in research.COSTS:
            key=policy+'__'+case
            expected=independent['results'][key]['symbols']
            ideas=[];proof={}
            for symbol in SYMBOLS:
                for tf in ('15m','1d'):
                    assert expected[symbol]['data_sha256'][tf]==sha(data_dir/f'{symbol}_{tf}.csv')
                src=out/'independent'/key/f'{symbol}_ideas.jsonl'
                proof[symbol]=sha(src)
                ideas.extend(scope_row(symbol,json.loads(line)) for line in src.read_text(encoding='utf-8').splitlines() if line.strip())
            p=portfolio(bars,ideas,policy=policy,fee=fee,slippage=slippage)
            dst=out/'portfolio'/key;dst.mkdir(exist_ok=True,parents=True)
            (dst/'TRADES.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in p['trades']),encoding='utf-8')
            (dst/'LEDGER.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in p['ledger']),encoding='utf-8')
            (dst/'EQUITY.json').write_text(json.dumps(p['closed_equity_curve'],ensure_ascii=False)+'\n',encoding='utf-8')
            (dst/'SUMMARY.json').write_text(json.dumps(p['summary'],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            phase_stats={name:finite_model([t for t in p['trades'] if mtf_engine.ms(start)<=mtf_engine.ms(t['signal_at'])<mtf_engine.ms(stop)]) for name,start,stop in PHASES_2025}
            scenarios[key]={'portfolio':p['summary'],'by_route':route_stats(p['trades']),
                            'by_signal_phase':phase_stats,'source_idea_sha256':proof,
                            'trade_file_sha256':sha(dst/'TRADES.jsonl'),
                            'independent_route_stats':independent['results'][key]['ALL_SYMBOLS_INDEPENDENT']}
    record={'status':'OOS_2025_RETROSPECTIVE_COMPLETE','historical_split':'previously untested 2025, earlier than 2026 benchmark; not prospective',
            'source':'Binance Data Vision futures/um checked against archived checksums',
            'period_15m':'2025-01-01..2025-12-31 UTC inclusive',
            'period_1d':'2024-01-01..2025-12-31 UTC inclusive',
            'universe':list(SYMBOLS),'frozen_core_check':c,
            'training_or_threshold_fitting_on_2025':False,
            'macro_filter_implemented':False,'course_visual_examples_verified':0,
            'bos_route':'15m PROXY ONLY, not 3–5m course BOS',
            'execution':'15m OHLC candle-touch model; no book spreads/funding/mark-price/forced liquidations',
            'risk':'1000 USD start, 0.5% per idea, max two active, cap 3x equity',
            'strict_history_gate':{'status':gate['status'],'volume_days_checked':gate['cross_checked_daily_volume_days'],
                                  'source_manifest_type':gate['source_manifest_type']},
            'grid_locked_before_results':list(scenarios),'scenarios':scenarios}
    (out/'OOS_2025_SUMMARY.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('OOS_2025_RETROSPECTIVE_COMPLETE')
    for k,v in scenarios.items():
        p=v['portfolio'];print(k,'closed',p['completed_model_trades'],'return%',p['closed_equity_return_pct'],
                               'dd%',p['max_bar_close_MTM_drawdown_pct'],'pf',p.get('PF_resolved'))
    return record

if __name__=='__main__':
    pa=argparse.ArgumentParser()
    pa.add_argument('--data-dir',default='data/oos_2025')
    pa.add_argument('--out',default='results_05/oos_2025')
    args=pa.parse_args()
    execute(args.data_dir,args.out)