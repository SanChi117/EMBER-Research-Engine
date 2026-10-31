"""Run unchanged source using existing A199 native offline engine, never trading."""
import sys,json,subprocess,zipfile,hashlib,shutil
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
user=ROOT/'user';(user/'backtest_results').mkdir(parents=True,exist_ok=True)
result=ROOT/'results';result.mkdir(exist_ok=True)
for sym in ('BTC','ETH','SOL','LINK'):
 cfg={'bot_name':'A217_OFFLINE_ONLY','dry_run':True,'dry_run_wallet':1000,'stake_currency':'USDT','stake_amount':100,'tradable_balance_ratio':.99,'max_open_trades':1,'trading_mode':'futures','margin_mode':'isolated','entry_pricing':{'price_side':'other','use_order_book':False},'exit_pricing':{'price_side':'other','use_order_book':False},'exchange':{'name':'binance','key':'','secret':'','ccxt_config':{},'ccxt_async_config':{},'pair_whitelist':[f'{sym}/USDT:USDT'],'pair_blacklist':[]},'pairlists':[{'method':'StaticPairList'}],'telegram':{'enabled':False,'token':'','chat_id':'0'},'api_server':{'enabled':False,'listen_ip_address':'127.0.0.1','listen_port':8080,'username':'offline','password':'offline-research-only'}}
 (ROOT/f'config-{sym}.json').write_text(json.dumps(cfg))
for year in (2024,2025,2026):
 for sym in ('BTC','ETH','SOL','LINK'):
  for fee in (.0005,.00125):
   key=f'{year}-{sym}-{fee}'; dest=result/(key+'.zip')
   if dest.exists():continue
   end=f'{year+1}0101' if year<2026 else '20261001'
   cmd=[sys.executable,str(REPO/'research/native_candidate_screen_20261031/a199_native_original_futures_offline.py'),'-c',str(ROOT/f'config-{sym}.json'),'--userdir',str(user),'--datadir',str(ROOT/'data'),'--strategy-path',str(HERE/'sources'),'--strategy','TrendRiderStrategyPublic','--timeframe','1h','--timeframe-detail','5m','--timerange',f'{year}0101-{end}','--data-format-ohlcv','json','--fee',str(fee),'--enable-protections','--export','trades','--cache','none']
   print('START',key,flush=True)
   with (result/(key+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   if r.returncode:raise RuntimeError(('NATIVE_FAILURE',key,r.returncode))
   files=list((user/'backtest_results').glob('*.zip'));assert len(files)==1,files
   shutil.move(files[0],dest);print('FINISHED',key,flush=True)
print('ALL_NATIVE_RUNS_COMPLETE',flush=True)
