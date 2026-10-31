"""A235: isolate forced-1h harness defect. Same 3-pair research portfolio, NOT full author parity."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"research/a228_five_original"))
import a228_run_original_freqtrade_five as old
EXPECTED={"TrendFollowing":"4h","Risk_Stair_S5":"15m","NASOSv7LongShort":"5m"}
def main():
    old.REPLAY=old.GEN/"a235_backtests"
    old.REPLAY.mkdir(parents=True,exist_ok=True)
    config=old.config_for_run()
    assert config.pop("timeframe")=="1h"
    cfg=old.GEN/"a235_config.json"
    cfg.write_text(json.dumps(config,indent=2))
    receipts=json.loads(old.SOURCE_RECEIPT.read_text())
    rows=[]
    for year,timerange in old.YEARS.items():
      for cost,fee in old.COSTS.items():
       for name,tf in EXPECTED.items():
        row=old.run_one(year,timerange,cost,fee,name,cfg)
        if row["state"]=="NATIVE_FREQTRADE_BACKTEST_COMPLETE":
          dest=old.REPLAY/year/cost/name
          data,_=old.recent_result(dest)
          m=data["strategy"][name]
          assert m["timeframe"]==tf,(name,m["timeframe"],tf)
          assert m["timeframe_detail"]==("" if tf=="5m" else "5m")
          assert m["starting_balance"]==1000
          assert abs(sum(t["profit_abs"] for t in m["trades"])-m["profit_total_abs"])<1e-5
          row["actual_timeframe"]=m["timeframe"]
          row["actual_detail"]=m["timeframe_detail"]
          row["source_receipt"]=receipts["original_pins"][name]
          zips=list(dest.glob("*.zip"))
          assert len(zips)==1
          row["native_zip_sha256"]=hashlib.sha256(zips[0].read_bytes()).hexdigest()
          with zipfile.ZipFile(zips[0]) as z:
            s=[n for n in z.namelist() if n.endswith("_"+name+".py")]
            assert len(s)==1,s
            raw=z.read(s[0])
            sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            assert sha==receipts["original_pins"][name]["git_blob"]
            row["archived_source_blob"]=sha
        row["full_author_config_parity"]=False
        row["scope"]="Only forced-1h removed; old 3-pair portfolio and execution overrides retained to isolate one defect"
        rows.append(row)
        (old.REPLAY/"A235_RESULTS.json").write_text(json.dumps(rows,indent=2))
    assert len(rows)==18
    failed=[r for r in rows if r["state"]!="NATIVE_FREQTRADE_BACKTEST_COMPLETE"]
    print("A235_SUMMARY",json.dumps([{k:r.get(k) for k in ("strategy","year","cost_model","state","actual_timeframe","native_profit_total_pct","native_trade_count")} for r in rows]),flush=True)
    if failed:raise RuntimeError(str(len(failed))+" native runs blocked; see recorded logs")
if __name__=="__main__":main()
