#!/usr/bin/env python3
"""Real Binance OHLCV timestamp integration; synthetic event labels only.

Confirms D03 event lineage/as-of chronology using actual exchange candle
boundaries; DOES NOT confirm POI/VC/IDM/BOS pattern identification.
"""
import argparse,csv,io,hashlib,json,pathlib,sys,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from strict_event_lineage_d03 import EventLedger,CausalEvent
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
DAY=86_400_000
H4=14_400_000
END=1791849600000  # 2026-10-13 UTC (recomputed below)
from datetime import datetime,timezone
END=int(datetime(2026,10,13,tzinfo=timezone.utc).timestamp()*1000)
START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp()*1000)

def run(archive):
 output=dict(component='D03',status='VERIFIED_FORMAL_D03_REAL_BAR_TIMESTAMPS',
             symbols=list(SYMBOLS),real_inputs_sha={},per_symbol=[],total_valid_parent_child_pairs=0,
             snapshots_tested=0,mutation_future_visibility_tested=0,
             limits=['D03 source time relies on D01/D02 timestamp contracts',
                     'Associated confirmation kinds are synthetic; no course semantic labels validated',
                     'No actual order acknowledgments, live exchange timing, or signal edge attested'])
 with zipfile.ZipFile(archive) as z:
  files={pathlib.PurePosixPath(p).name:p for p in z.namelist() if '/data/history/' in p and p.endswith('.csv')}
  for symbol in SYMBOLS:
   raw={}
   for tf in ('15m','1d'):
    data=z.read(files[f'{symbol}_{tf}.csv']);raw[tf]=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    output['real_inputs_sha'][f'{symbol}_{tf}']=hashlib.sha256(data).hexdigest()
   dailies=[r for r in raw['1d'] if START<=int(r['open_time']) and int(r['open_time'])+DAY<=END]
   quarter={int(r['open_time']):r for r in raw['15m']}
   g=EventLedger();pairs=0
   for day in dailies:
    dstart=int(day['open_time']);dend=dstart+DAY
    # Native daily candle from exchange is a SOURCE event at bar close.
    uid=f'{symbol}:1d:{dstart}'
    g.add(CausalEvent(uid,'SOURCE',symbol,'BINANCE','USDM_FUTURES','1d',dstart,dend,dend,(),(f'sha:{output["real_inputs_sha"][f"{symbol}_1d"]}:row:{dstart}',)))
    childend=dend+H4
    if childend>END:continue
    actual=[quarter.get(dend+j*900000) for j in range(16)]
    assert all(actual) and int(actual[-1]['close_time'])+1==childend
    # Intentional generic timestamp-only child, NOT a semantic VC/POI signal.
    cid=f'{symbol}:4h:TIME_CHECK:{dend}'
    g.add(CausalEvent(cid,'CONFIRMATION',symbol,'BINANCE','USDM_FUTURES','4h',dend,childend,
                      childend,(uid,),(f'sha:{output["real_inputs_sha"][f"{symbol}_15m"]}:rows:{dend}:{childend}',)))
    assert g.snapshot(dend)[-1].uid==uid
    assert cid not in {e.uid for e in g.snapshot(childend-1)}
    assert g.ancestors(cid,as_of_ms=childend)[0].uid==uid
    output['snapshots_tested']+=2
    pairs+=1
   # Same historical snapshot after later data: audit cannot use suffix.
   firsttime=int(dailies[1]['open_time'])+DAY
   snap=g.snapshot(firsttime)
   copied=EventLedger.replay(g.export())
   assert copied.digest()==g.digest() and copied.snapshot(firsttime)==snap
   output['mutation_future_visibility_tested']+=1
   output['per_symbol'].append(dict(symbol=symbol,native_daily_input=len(dailies),
                                   parent_child_timestamp_pairs=pairs,graph_nodes=len(g.export()),
                                   first_daily_close=dailies[0]['open_time'],last_daily_close=dailies[-1]['open_time'],
                                   graph_sha256=g.digest()))
   output['total_valid_parent_child_pairs']+=pairs
 assert output['total_valid_parent_child_pairs']>=900
 return output

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 res=run(a.archive);pathlib.Path(a.out).write_text(json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(res['status'],res['total_valid_parent_child_pairs'])
