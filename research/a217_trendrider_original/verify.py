"""Independently reconcile native trade journals, not strategy output assertions."""
import json,zipfile,hashlib,sys,math,csv
from pathlib import Path
from collections import Counter
ROOT=Path(sys.argv[1]);OUT=Path(__file__).resolve().parent/'evidence';OUT.mkdir(exist_ok=True)
rows=[]
for p in sorted((ROOT/'results').glob('*.zip')):
 year,sym,fee=p.stem.split('-');fee=float(fee)
 with zipfile.ZipFile(p) as z:
  names=[n for n in z.namelist() if n.endswith('.json') and '_config' not in n];assert len(names)==1,names
  o=json.loads(z.read(names[0]));s=o['strategy']['TrendRiderStrategyPublic'];ts=s['trades']
 assert len(ts)==s['total_trades']
 pnl=sum(t['profit_abs'] for t in ts);assert abs(pnl-s['profit_total_abs'])<1e-6
 assert all(t['leverage']==1 and not t['is_short'] and t['open_date'].startswith(year) for t in ts)
 wins=sorted([t['profit_abs'] for t in ts if t['profit_abs']>0],reverse=True);loss=-sum(t['profit_abs'] for t in ts if t['profit_abs']<0)
 r={'year':int(year),'symbol':sym,'fee_per_side':fee,'trades':len(ts),'net_usdt':pnl,'wallet_net_pct':pnl/10,'pf':sum(wins)/loss if loss else None,'native_realized_dd_pct':s.get('max_drawdown_account',0)*100,'funding_usdt':sum(t.get('funding_fees',0) or 0 for t in ts),'top3_winner_share':sum(wins[:3])/sum(wins) if wins else None,'exit_reasons':dict(Counter(t['exit_reason'] for t in ts)),'native_zip_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_hash_checked_in_zip':False}
 with zipfile.ZipFile(p) as z:
  srcs=[n for n in z.namelist() if n.endswith('.py') and 'TrendRider' in n]
  for n in srcs:
   b=z.read(n);assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()=='b7d013a802b45d2dd1cb0b91d4083fb247efac75';r['source_hash_checked_in_zip']=True
 (OUT/(p.stem+'-trades.json')).write_text(json.dumps(ts,separators=(',',':')))
 rows.append(r)
assert len(rows)==24,len(rows)
years=[]
for year in (2024,2025,2026):
 for fee in (.0005,.00125):
  rs=[r for r in rows if r['year']==year and r['fee_per_side']==fee]
  years.append({'year':year,'fee_per_side':fee,'trades':sum(r['trades'] for r in rs),'net_usdt_four_separate_wallets':sum(r['net_usdt'] for r in rs),'return_pct_on_4000_segregated_capital':sum(r['net_usdt'] for r in rs)/40,'positive_pairs':sum(r['net_usdt']>0 for r in rs),'cash_usdt_benchmark_return':0})
status='RESEARCH_NEGATIVE' if any(r['net_usdt_four_separate_wallets']<=0 for r in years) else 'INSUFFICIENT_EVIDENCE'
result={'cycle':'A217','strategy_source':'darkvolg/Trading/FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py','source_sha':'b7d013a802b45d2dd1cb0b91d4083fb247efac75','strategy_family':'multi-trigger trend/pullback momentum','futures_mode':'Binance USDT-M isolated long-only 1x','dataset_SHA':hashlib.sha256((ROOT/'source_manifest.json').read_bytes()).hexdigest(),'periods':['2024','2025','2026-01-01/2026-10-01 exclusive'],'execution_assumptions':'Freqtrade2026.4 original code, 1h + 5m detail, original limit candle fills, real mark/funding, static exchange tiers','after_cost_metrics':rows,'year_summaries':years,'drawdown':'per-pair native realized DD only; full mark-to-market portfolio audit not complete','robustness':'three nonoverlapping periods, two cost levels; historical validation, no pristine forward','status':status,'reason':'One or more full-year/cost aggregate results nonpositive' if status=='RESEARCH_NEGATIVE' else 'Historical economic screen positive; execution/MTM/forward evidence still required','limitations':['No measured bid-ask or queue fills','No independent intrabar gap/liquidation proof','No prospective PAPER','No common-wallet portfolio test','Prepublication periods not claimed as pristine OOS']}
(OUT/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps(years,indent=2));print(status)
