"""Native original source causal prefix and parameter preflight on real UM candles."""
import sys,json,hashlib
from pathlib import Path
import pandas as pd
from freqtrade.resolvers import StrategyResolver
ROOT=Path(sys.argv[1]);HERE=Path(__file__).resolve().parent
raw=(HERE/'sources/TrendRiderStrategy_public.py').read_bytes()
assert hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()=='b7d013a802b45d2dd1cb0b91d4083fb247efac75'
cfg={'strategy':'TrendRiderStrategyPublic','strategy_path':str(HERE/'sources'),'user_data_dir':ROOT/'user','timeframe':'1h','trading_mode':'futures','stake_currency':'USDT','stake_amount':100,'dry_run':True}
s=StrategyResolver.load_strategy(cfg);s.ft_load_hyper_params(False)
class DP:
 def __init__(self,cut):self.cut=cut
 def get_pair_dataframe(self,pair,timeframe):
  name=pair.replace('/','_').replace(':','_')+'-'+timeframe+'-futures.json'
  d=pd.DataFrame(json.loads((ROOT/'data/futures'/name).read_text()),columns=['date','open','high','low','close','volume']);d.date=pd.to_datetime(d.date,unit='ms',utc=True)
  return d[d.date+pd.Timedelta(timeframe.replace('h',' hours').replace('d',' days'))<=self.cut].copy()
 def current_whitelist(self):return ['BTC/USDT:USDT']
rows=[]
for cut in ('2024-03-15T03:00:00Z','2025-06-15T13:00:00Z','2026-09-15T23:00:00Z'):
 cutoff=pd.Timestamp(cut);s.dp=DP(pd.Timestamp('2026-10-01T00:00:00Z'))
 full=s.dp.get_pair_dataframe('BTC/USDT:USDT','1h');a=s.populate_indicators(full.copy(),{'pair':'BTC/USDT:USDT'});a=s.populate_entry_trend(a,{});a=s.populate_exit_trend(a,{})
 s.dp=DP(cutoff);prefix=s.dp.get_pair_dataframe('BTC/USDT:USDT','1h');b=s.populate_indicators(prefix.copy(),{'pair':'BTC/USDT:USDT'});b=s.populate_entry_trend(b,{});b=s.populate_exit_trend(b,{})
 a=a[a.date<cutoff].reset_index(drop=True);b=b.reset_index(drop=True)
 cols=[c for c in b if c!='date'];pd.testing.assert_frame_equal(a[b.columns],b,check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
 rows.append({'cut':cut,'bars':len(b),'all_columns_equal':True})
receipt={'source_blob':'b7d013a802b45d2dd1cb0b91d4083fb247efac75','prefix_tests':rows,'buy_params':{k:getattr(s,k).value for k in s.buy_params},'sell_params':{k:getattr(s,k).value for k in s.sell_params},'status':'PREFIX_PASS_NOT_PROFITABILITY','note':'Full-price history vs closed informative prefixes. Does not establish order callback causality or profitability.'}
(ROOT/'preflight.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
