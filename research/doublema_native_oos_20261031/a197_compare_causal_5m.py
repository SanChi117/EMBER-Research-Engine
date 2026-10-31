#!/usr/bin/env python3
"""A197 causal-fix ONLY direct Freqtrade 5m comparison to ORIGINAL A196 native ZIP.
Author original source immutable; test copy changes one candle-boundary inequality.
Not a live execution certification. Fail closed on archive/data inconsistencies.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
SYMS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")

def open_native(p):
    assert p.is_file() and zipfile.is_zipfile(p),p
    with zipfile.ZipFile(p) as z:
        names=[t for t in z.namelist() if t.endswith('.json') and '_config' not in t]
        assert len(names)==1,names
        d=json.loads(z.read(names[0]))['strategy']['VideoDoubleMaFuturesStrategy']
    assert d['total_trades']==len(d['trades'])
    assert abs(sum(x['profit_abs'] for x in d['trades'])-d['profit_total_abs'])<.001
    assert all("2026-05-13"<=x["open_date"][:10]<"2026-10-01" for x in d["trades"])
    return d,hashlib.sha256(p.read_bytes()).hexdigest()

def stats(d):
    t=d['trades']
    wins=sorted((x['profit_abs'] for x in t if x['profit_abs']>0),reverse=True)
    return {"n":len(t),"return_pct":round(d['profit_total']*100,6),
       "pf":round(d['profit_factor'],6),
       "maxdd_pct":round(d['max_drawdown_account']*100,6),
       "net_USDT":round(d['profit_total_abs'],6),
       "long_USDT":round(sum(x['profit_abs'] for x in t if not x['is_short']),4),
       "short_USDT":round(sum(x['profit_abs'] for x in t if x['is_short']),4),
       "top3_net_fraction":round(sum(wins[:3])/d['profit_total_abs'],6) if d['profit_total_abs']>0 else None,
       "top3_gross_fraction":round(sum(wins[:3])/sum(wins),6) if wins else None,
       "stops":sum(x['exit_reason'] in ('stop_loss','trailing_stop_loss') for x in t)}
def compare(old,causal):
    a={(x['open_timestamp'],x['is_short']):x for x in old}
    b={(x['open_timestamp'],x['is_short']):x for x in causal}
    assert len(a)==len(old) and len(b)==len(causal)
    common=set(a)&set(b)
    changed=[{"entry":k[0],"side":"SHORT" if k[1] else "LONG",
        "original_exit":a[k]['close_date'],"causal_exit":b[k]['close_date'],
        "original_reason":a[k]['exit_reason'],"causal_reason":b[k]['exit_reason'],
        "original_USDT":round(a[k]['profit_abs'],5),"causal_USDT":round(b[k]['profit_abs'],5)}
        for k in sorted(common) if a[k]['close_timestamp']!=b[k]['close_timestamp']
            or abs(a[k]['profit_abs']-b[k]['profit_abs'])>0.001
            or a[k]['exit_reason']!=b[k]['exit_reason']]
    return {"shared_entries":len(common),
        "removed_original_entries":len(set(a)-set(b)),
        "new_causal_entries":len(set(b)-set(a)),
        "changed_common_trades":len(changed),
        "changed_trade_receipts":changed}
def main():
    p=argparse.ArgumentParser();p.add_argument("--results",required=True)
    p.add_argument("--original-artifact",required=True)
    args=p.parse_args();out=Path(args.results);archive=Path(args.original_artifact)
    report={"schema":"EMBER_A197_CALLBACK_CAUSAL_BOUNDARY_8_NATIVE_5M_COMPARISON",
      "original_source_commit":"40af5c7c1c44253766428cfb06babf22f9817aa4",
      "original_source_blob":"22ca6588bbd056e671783f676f1a4010cbfc1bb6",
      "engine":"freqtrade==2026.4",
      "only_test_copy_patch":"return dataframe.loc[dates <= candle_time] -> return dataframe.loc[dates < candle_time.floor('h')]",
      "window":"[2026-05-13,2026-10-01)",
      "source_original_5m_run":41148069316,
      "genuine_both_venues":"Binance USD-M historical source only, static Binance metadata",
      "outcomes":{}}
    for sym in SYMS:
        report['outcomes'][sym]={}
        for fee in FEES:
            before,sha_a=open_native(archive/f"5m-detail-{sym}-fee{fee}.zip")
            after,sha_b=open_native(out/f"causal-{sym}-fee{fee}.zip")
            original_stats=stats(before);causal_stats=stats(after)
            delta=compare(before['trades'],after['trades'])
            result={"original":original_stats,"causal_only_boundary_fix":causal_stats,
               "delta_net_pct":round(causal_stats['return_pct']-original_stats['return_pct'],6),
               "delta_pf":round(causal_stats['pf']-original_stats['pf'],6),
               "changed_trade_receipts":delta,
               "sha256_original_native_zip":sha_a,"sha256_causal_native_zip":sha_b}
            report['outcomes'][sym][fee]=result
            print("A197_CAUSAL_5M_ORIGINAL_VS_FIXED",sym,fee,
                 "N",original_stats["n"],causal_stats["n"],
                 "PCT",original_stats["return_pct"],causal_stats["return_pct"],
                 "PF",original_stats["pf"],causal_stats["pf"],
                 "CHANGED",delta["changed_common_trades"],flush=True)
    report["any_economic_differences"]=any(
        (abs(z['delta_net_pct'])>0.0001 or z['changed_trade_receipts']['removed_original_entries']>0
           or z['changed_trade_receipts']['new_causal_entries']>0)
        for v in report['outcomes'].values() for z in v.values())
    report["limitations"]=["Only one original callback boundary fixed in test copy, not a certified adapted strategy",
       "Without true order book, limit queue, 1m path or slippage 5m execution may be optimistic",
       "One previously investigated historical period; never treat causal corrected result as unseen OOS",
       "No small 1% account risk validated, no live or PAPER orders, no 15m modification"]
    (out/"A197_CAUSAL_FIXED_VS_ORIGINAL_5M_MACHINE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("A197_EIGHT_GENUINE_FREQTRADE_NATIVE_CAUSAL_VS_ORIGINAL_RECEIPTS_COMPLETE",report['any_economic_differences'],flush=True)
if __name__=="__main__":main()
