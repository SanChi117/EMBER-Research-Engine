#!/usr/bin/env python3
"""A196 causality probe on the exact original source on genuine historical Binance 1h/4h.
Tests whether already-closed historical 1h indicators/entries change when future
1h/4h bars are appended. This IS NOT the entire Freqtrade lookahead-analysis and
cannot fully check custom callback return data boundaries. Academic/PAPER only.
"""
from __future__ import annotations
import argparse,importlib.util,json,math,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
SYMBOLS=("BTC","ETH","SOL","LINK")
CUTS=("2026-05-15T12:00Z","2026-05-29T12:00Z","2026-06-15T12:00Z",
      "2026-06-29T12:00Z","2026-07-12T12:00Z","2026-07-29T12:00Z",
      "2026-08-12T12:00Z","2026-08-29T12:00Z","2026-09-12T12:00Z",
      "2026-09-27T12:00Z")
COLS=("enter_long","enter_short","enter_tag","first_pullback_long","first_pullback_short",
      "pullback_stop_long_line","pullback_stop_short_line","cluster_zone_high",
      "cluster_zone_low","ma_cluster_confirmed","htf_long_ok_4h","htf_short_ok_4h",
      "long_direction_score","short_direction_score","prev_pivot_high","prev_pivot_low",
      "atr_14","ma_width","fast_band_high","fast_band_low")
BLOB="22ca6588bbd056e671783f676f1a4010cbfc1bb6"
def read(datafile):
    a=json.loads(datafile.read_text())
    frame=pd.DataFrame(a,columns=["ts","open","high","low","close","volume"])
    frame["date"]=pd.to_datetime(frame.pop("ts"),unit="ms",utc=True)
    assert frame["date"].is_monotonic_increasing and frame["date"].is_unique
    return frame[["date","open","high","low","close","volume"]]
def same(a,b):
    if pd.isna(a) and pd.isna(b):return True
    if isinstance(a,(int,float,np.integer,np.floating)) and isinstance(b,(int,float,np.integer,np.floating)):
        return math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=1e-9)
    return str(a)==str(b)
class Provider:
    def __init__(self,informative):self.informative=informative
    def get_pair_dataframe(self,pair,timeframe):
        assert timeframe=="4h",(pair,timeframe)
        return self.informative.copy()
def instantiate(strategy_cls,pair,h4):
    s=strategy_cls({"stake_currency":"USDT"})
    s.dp=Provider(h4)
    return s
def run(cls,pair,h1,h4):
    o=instantiate(cls,pair,h4)
    v=o.populate_indicators(h1.copy(),{"pair":pair})
    v=o.populate_entry_trend(v,{"pair":pair})
    assert len(v)==len(h1)
    return v
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--datadir",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    data=Path(args.source).read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
    assert sha==BLOB,("source_changed",sha)
    spec=importlib.util.spec_from_file_location("a196_author_orig",args.source)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls=mod.VideoDoubleMaFuturesStrategy
    outcomes={}
    for sym in SYMBOLS:
        pair=f"{sym}/USDT:USDT"
        d=Path(args.datadir)/"futures"
        h1=read(d/f"{sym}_USDT_USDT-1h-futures.json")
        h4=read(d/f"{sym}_USDT_USDT-4h-futures.json")
        full=run(cls,pair,h1,h4)
        assert all(key in full.columns for key in COLS),(sym,sorted(set(COLS)-set(full)))
        observations=[]
        for cutoff in CUTS:
            t=pd.Timestamp(cutoff)
            prefix=h1.loc[h1.date<=t].copy()
            # Only completed HTF candles available when 1h signal bar ending at t+1h.
            h4_closed=h4.loc[h4.date+pd.Timedelta(hours=4)<=t+pd.Timedelta(hours=1)].copy()
            assert len(prefix)>500 and len(h4_closed)>35
            partial=run(cls,pair,prefix,h4_closed)
            assert len(partial)==len(prefix)
            base=full.loc[full.date==t].iloc[0]
            prev=partial.loc[partial.date==t].iloc[0]
            diff=[{"col":key,"full":str(base[key]),"asof":str(prev[key])}
                  for key in COLS if not same(base[key],prev[key])]
            observations.append({"at_closed_candle_start":str(t),"indicators_checked":len(COLS),
                                 "mismatches":diff,"full_entry":str(base.get("enter_tag","")),
                                 "prefix_entry":str(prev.get("enter_tag",""))})
            print("A196_PREFIX_ORIGINAL_SIGNAL",sym,str(t),"MISMATCHES",len(diff),flush=True)
        outcomes[sym]={"full_rows":len(full),"evaluated_snapshots":len(CUTS),
                       "mismatching_snapshots":sum(bool(x["mismatches"]) for x in observations),
                       "observations":observations}
    output={"schema":"EMBER_A196_ORIGINAL_CODE_PREFIX_CAUSALITY_4_MARKETS_10_SNAPSHOTS",
            "upstream_blob":sha,"markets":SYMBOLS,"probe_columns":list(COLS),
            "closed_1h_full_vs_prefix_probe":outcomes,
            "total_snapshots":len(SYMBOLS)*len(CUTS),
            "mismatching_snapshots":sum(x["mismatching_snapshots"] for x in outcomes.values()),
            "limitations":["Only 40 selected time snapshots, not each bar","Not full Freqtrade lookahead-analysis",
                "Not a custom_stoploss or custom_exit callback causal/recursive test",
                "4h candles only close at 4h boundary, Freqtrade informative shift",
                "No actual portfolio execution here; A196 native 5m result is separate",
                "FROZEN original strategy class with no modifications, no live execution"]}
    Path(args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print("A196_ORIGINAL_CODE_PREFIX_COMPARISON_FINISHED",output["total_snapshots"],
          "MISMATCHES",output["mismatching_snapshots"],flush=True)
if __name__=="__main__":main()
