#!/usr/bin/env python3
"""Convert frozen Binance USD-M ETH OHLCV and settled funding to Freqtrade 2026.4 JSON.

Trade rules stay in upstream 40af5c7 original Freqtrade class, not here.
No network, no order API. Rates before settlement are not used for strategy features.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"data"
BEGIN=int(datetime(2026,3,15,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,30,tzinfo=timezone.utc).timestamp()*1000)
H=3600000

def read(path):
    b=path.read_bytes()
    return json.loads(b),hashlib.sha256(b).hexdigest()

def load_parts(glob,tf,step,expected):
    paths=sorted(SOURCE.glob(glob))
    if not paths:raise ValueError("SOURCE_NOT_PRESENT:"+glob)
    rows=[];sha={}
    for p in paths:
        obj,digest=read(p)
        if obj["interval"]!=tf or obj["symbol"]!="ETHUSDT":
            raise ValueError("WRONG_MARKET")
        rows.extend(obj["rows"])
        sha[p.name]=digest
    if len(rows)!=expected:
        raise ValueError(f"SOURCE_INCOMPLETE_{tf}:{len(rows)}/{expected}")
    for i,r in enumerate(rows):
        if r[0]!=BEGIN+i*step or len(r)!=6:
            raise ValueError(f"NONCAUSAL_DUPLICATE_OR_GAP_{tf}:{i}")
        o,hi,lo,c,v=map(float,r[1:])
        if not (0<lo<=min(o,c)<=max(o,c)<=hi and v>=0):
            raise ValueError("INVALID_OHLCV")
    return rows,sha

def rates_as_1h():
    obj,sha=read(SOURCE/"ETHUSDT_funding_history.json")
    raw=obj["records"]
    rates=[0.0]*((END-BEGIN)//H)
    seen=set()
    for x in raw:
        t=int(x["fundingTime"])
        k=(t-BEGIN)//H
        if t<BEGIN or t>=END or k<0 or k>=len(rates) or k in seen:
            raise ValueError("INVALID_OR_DUP_FUNDING")
        seen.add(k)
        rates[k]=float(x["fundingRate"])
    # Legacy Freqtrade 2026.4 funding JSON format stores rate in OHLCV.open.
    # Funding is a POST-SETTLEMENT ACCOUNTING input. Never feed future realized
    # funding rates to the original entry/exit decision indicators.
    return [[BEGIN+i*H,r,r,r,r,0] for i,r in enumerate(rates)],sha,len(raw)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--datadir",required=True)
    args=ap.parse_args()
    d=Path(args.datadir)/"futures"
    d.mkdir(parents=True,exist_ok=True)
    series={}
    sha={}
    for tf,gl,step in (("1h","ETHUSDT_1h_part*.json",H),
                       ("4h","ETHUSDT_4h.json",4*H),
                       ("1d","ETHUSDT_1d.json",24*H),
                       ("mark","ETHUSDT_mark_1h_part*.json",H)):
        source_tf="1h" if tf=="mark" else tf
        rows,sh=load_parts(gl,source_tf,step,(END-BEGIN)//step)
        filename=f"ETH_USDT_USDT-{'1h-mark' if tf=='mark' else tf+'-futures'}.json"
        (d/filename).write_text(json.dumps(rows,separators=(",",":")))
        series[tf]={"count":len(rows),"first_ms":rows[0][0],"last_ms":rows[-1][0],"filename":filename}
        sha.update(sh)
    funding,rate_sha,n=rates_as_1h()
    filename="ETH_USDT_USDT-1h-funding_rate.json"
    (d/filename).write_text(json.dumps(funding,separators=(",",":")))
    series["funding"]={"count":len(funding),"settled_nonzero_count":n,"filename":filename,
                       "settled_future_values_not_available_at_signal_time":True}
    sha["ETHUSDT_funding_history.json"]=rate_sha
    summary={"first_time":BEGIN,"end_exclusive":END,"series":series,"source_sha256":sha,
             "warning":"No historical bid/ask, no true maker-limit fill, funding 13ms settled timestamp floored to an hour for Freqtrade 2026.4 legacy format; not actual exchange fills"}
    (d.parent/"native_source_manifest.json").write_text(json.dumps(summary,indent=2))
    print("NATIVE_SOURCE_CHECK_COMPLETE "+json.dumps(summary["series"],sort_keys=True))
if __name__=="__main__":
    main()
