"""A232: READ only existing A196+A197 original Freqtrade zipped trades. No trading.
Not a shared-account simulation, not a new entry algorithm, not forward OOS.
"""
import json
import re
import zipfile
from pathlib import Path

ROOT=Path("a232-archived")
OUT=Path("a232-diagnostic")
COINS=("BTC","ETH","SOL","LINK")
REQUIRED={(year,fee,coin) for year in ("2025","2026") for fee in ("base","stress") for coin in COINS}
AGG={}
ITEMS={}
for folder in ("2025","2026"):
    folder_path=ROOT/folder
    archives=sorted(folder_path.rglob("*.zip"))
    print("A232_NATIVE_ARCHIVED_ZIPS",folder,len(archives),flush=True)
    for archive in archives:
        name=archive.name
        p=re.search(r"(BTC|ETH|SOL|LINK)-fee(5|12p5)",name)
        if not p: continue
        sym,rate=p.group(1),p.group(2)
        scenario="base" if rate=="5" else "stress"
        key=(folder,scenario,sym)
        if key in ITEMS: raise RuntimeError("duplicate native ZIP for "+str(key))
        with zipfile.ZipFile(archive) as arc:
            found=[]
            for filename in arc.namelist():
                if not filename.endswith(".json") or "meta" in filename.lower():continue
                try: js=json.loads(arc.read(filename))
                except (ValueError,UnicodeDecodeError): continue
                if isinstance(js,dict) and "strategy" in js and "VideoDoubleMaFuturesStrategy" in js["strategy"]:
                    found.append((filename,js["strategy"]["VideoDoubleMaFuturesStrategy"]))
        if len(found)!=1:raise RuntimeError("Invalid original zipped native PnL "+str(archive)+" "+str([x[0] for x in found]))
        metrics=found[0][1]
        profit=metrics.get("profit_total_abs")
        count=metrics.get("total_trades")
        if profit is None or count is None:raise RuntimeError("No genuine PnL or trade count "+str(key))
        ITEMS[key]={"native_zip":str(archive),"profit_abs_usdt":round(float(profit),7),
           "native_return_pct":round(float(profit)/10000*100,6),"ntrades":int(count),
           "native_pf":metrics.get("profit_factor"),"native_dd_pct":None if metrics.get("max_drawdown_account") is None else round(100*float(metrics["max_drawdown_account"]),5)}
missing=REQUIRED-set(ITEMS)
if missing:raise RuntimeError("Missing 4-coin original trade receipts "+str(sorted(missing)))
if set(ITEMS)!=REQUIRED:raise RuntimeError("Unexpected extra original ZIP classifications "+str(set(ITEMS)-REQUIRED))
for year in ("2025","2026"):
    AGG[year]={}
    for cost in ("base","stress"):
        coins={coin:ITEMS[(year,cost,coin)] for coin in COINS}
        assert len(coins)==4
        total=sum(z["profit_abs_usdt"] for z in coins.values())
        AGG[year][cost]={
            "four_segregated_sleeve_aggregate_usdt":round(total,5),
            "four_segregated_sleeve_average_return_pct":round(total/40000*100,6),
            "separate_original_closed_trades":sum(z["ntrades"] for z in coins.values()),
            "all_BTC_ETH_SOL_LINK_included":True,
            "by_symbol":coins
        }
OUT.mkdir(exist_ok=True)
record={"scope":"source-native historical doubleMA original per-coin receipts, equal four segregated sleeves, not shared wallet",
 "original_source_sha":"22ca6588bbd056e671783f676f1a4010cbfc1bb6",
 "orig_2025_run":41149728068,"orig_2026_run":41148069316,
 "2025_period":"2025-04-01 through 2025-12-31 (in sample relative author source May2026)",
 "2026_period":"2026-05-13 through 2026-09-30 (post-source but historically observed)",
 "original_fee_base_per_side":0.0005,"original_fee_stress_per_side":0.00125,
 "native_pair_wallet_usdt":10000,"model_total_segregated_wallets_usdt":40000,
 "no_shared_account_drawdown_or_margin_validation":True,
 "no_new_strategy_parameters_or_orders":True,
 "results":AGG}
(OUT/"A232_FIXED_FOUR_SLEEVE_REAL_NATIVE_SOURCE_PNL.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
print("A232_FOUR_SLEEVE_SOURCE_NATIVE_RESULTS",json.dumps({year:{cost:[data["four_segregated_sleeve_average_return_pct"],data["separate_original_closed_trades"]] for cost,data in groups.items()} for year,groups in AGG.items()},ensure_ascii=False),flush=True)
