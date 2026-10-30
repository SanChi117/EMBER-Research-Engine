#!/usr/bin/env python3
"""Read-only 15 pinned GitHub JSON receipts, verify arithmetic, never execute external code."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import urllib.request
import sys

SOURCE_SHA = "3502b8ec96959ad47a9b63ae7474c17c7a2dbff7"
NAMES = ("MsSupportResistanceV1","MsFilterV6","MsFilterV6NoMs")
SYMBOLS = ("BTC","ETH","SOL","XRP","LTC")
EXPECTED = {
  "MsSupportResistanceV1": (404,703.15,1.376,35.3),
  "MsFilterV6": (164,398.52,1.504,96.2),
  "MsFilterV6NoMs": (208,225.94,1.214,169.7),
}
def download(path: str) -> bytes:
    url=f"https://raw.githubusercontent.com/fortunato/pymarket-structure/{SOURCE_SHA}/{path}"
    req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A189-public-receipts-auditor"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body=resp.read(2_000_000)
        assert resp.status==200 and len(body)<2_000_000 and body
        return body

def calculate():
    out={}
    for n in NAMES:
        transactions=[]
        per_pair=[]
        source_hashes={}
        for s in SYMBOLS:
            p=f"refs/freqtrade/backtest_results/{n}-{s}USDT-4h-trades.json"
            raw=download(p)
            source_hashes[p]=hashlib.sha256(raw).hexdigest()
            d=json.loads(raw)
            assert d["strategy"]==n and d["pair"]==f"{s}/USDT:USDT",d
            trades=d["trades"]
            assert all(isinstance(t["profit_abs"],(int,float)) for t in trades)
            transactions.extend(trades)
            per_pair.append({"pair":s,"n":len(trades),"pnl_usdt":round(sum(t["profit_abs"] for t in trades),2)})
        ntr=len(transactions)
        pnl=sum(t["profit_abs"] for t in transactions)
        gain=sum(t["profit_abs"] for t in transactions if t["profit_abs"]>0)
        loss=-sum(t["profit_abs"] for t in transactions if t["profit_abs"]<0)
        count_wins=sum(t["profit_abs"]>0 for t in transactions)
        top3=sum(sorted([t["profit_abs"] for t in transactions],reverse=True)[:3])
        assert len({(t["pair"],t["open_date"],t["is_short"]) for t in transactions})==ntr
        count_expected,pnl_expected,pf_expected,top3_expected=EXPECTED[n]
        assert ntr==count_expected, (n,ntr,count_expected)
        assert abs(round(pnl,2)-pnl_expected)<0.011,(n,pnl)
        pf=gain/loss
        assert abs(pf-pf_expected)<0.001,(n,pf)
        top3_share=top3/pnl*100
        assert abs(top3_share-top3_expected)<0.11,(n,top3_share)
        out[n]={"n":ntr,"pnl_usdt":round(pnl,2),"profit_factor":round(pf,6),
                "wins":count_wins,"win_rate_pct":round(100*count_wins/ntr,4),
                "top3_share_pct":round(top3_share,4),
                "profit_without_top3_usdt":round(pnl-top3,2),
                "per_pair":per_pair,"source_file_sha256":source_hashes}
    return {"schema":"EMBER_A189_MARKET_STRUCTURE_PUBLIC_RECEIPTS_CHECK_V1",
            "source_sha":SOURCE_SHA,"scope":"arithmetic of public 15 receipt files; not native strategy backtest",
            "strategies":out}
def main(path: Path):
    out=calculate()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("A189_PUBLIC_15_RECEIPT_SHA_PIN_ARITHMETIC_PASS")
    for k,v in out["strategies"].items():
        print(k,v["n"],v["pnl_usdt"],v["profit_factor"],v["top3_share_pct"])
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: script.py output.json")
    main(Path(sys.argv[1]))
