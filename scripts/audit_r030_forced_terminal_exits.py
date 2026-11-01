"""R030 audit ORIGINAL Freqtrade source-native PnL attribution to force_exit.

Reads only existing immutable GitHub Actions archived R030 artifact ZIP files
from A245 2024/25/2026 and the separately frozen 2023 holdout. No backtest
is re-run and no strategy parameter can be changed. Does not assume
a "force_exit" can be excluded from a realistic continuing account; its
contribution is reported to expose finite-window censoring.
"""
from __future__ import annotations

import argparse
import json
import math
import zipfile
from pathlib import Path

SOURCE = "VolatilitySystem"
HISTORY = ("2024", "2025", "2026_JAN_MAY")
EXPECT = {("2024","stress"):(88,15.62758473),
          ("2025","stress"):(80,16.166268094),
          ("2026_JAN_MAY","stress"):(37,2.238313457),
          ("2023_JUN_OCT","stress"):(38,12.744903134)}


def source_result(zippath: Path):
    with zipfile.ZipFile(zippath) as outer:
        for name in outer.namelist():
            if name.endswith(".json") and ".meta." not in name:
                try:
                    data=json.loads(outer.read(name))
                except (ValueError,UnicodeError):
                    continue
                if isinstance(data,dict) and SOURCE in data.get("strategy",{}):
                    return data["strategy"][SOURCE]
    return None


def inspect(native: dict, *, label: str, cost: str) -> dict:
    n=int(native["total_trades"])
    trade_rows=native.get("trades")
    if not isinstance(trade_rows,list) or len(trade_rows)!=n:
        raise ValueError(f"missing original unmodified trade records {label} {cost}")
    recorded=float(native["profit_total_abs"])
    exit_summary=native.get("exit_reason_summary",[])
    if not isinstance(exit_summary,list):
        raise ValueError("missing original exit_reason_summary")
    exits={}
    for row in exit_summary:
        key=row.get("key")
        if key and key!="TOTAL":
            exits[key]={
                "trades":int(row["trades"]),
                "profit_total_abs":float(row["profit_total_abs"]),
            }
    if sum(x["trades"] for x in exits.values())!=n:
        raise ValueError(f"exit summary missing trades {label} {cost}")
    if not math.isclose(
        sum(x["profit_total_abs"] for x in exits.values()),recorded,
        rel_tol=0,abs_tol=.06,
    ):
        raise ValueError(f"exit PnL not equal original wallet PnL {label} {cost}")
    end=exits.get("force_exit",{"trades":0,"profit_total_abs":0.})
    rest=recorded-end["profit_total_abs"]
    return {
        "original_label":label,"fee":cost,
        "native_trade_count":n,
        "original_wallet_net_pct":round(recorded/10,8),
        "end_of_test_force_exit_count":end["trades"],
        "end_of_test_force_exit_pnl_pct_wallet":round(end["profit_total_abs"]/10,8),
        "all_other_exit_pnl_pct_wallet":round(rest/10,8),
        "share_of_net_profit_due_to_forced_terminal_exit":(
            round(end["profit_total_abs"]/recorded,6) if recorded else None
        ),
        "end_exits_by_reason":exits,
        "source_strategy_stoploss":"-1",
        "source_futures_leverage":2.,
        "warning":"Terminal forced closing can create unbanked end-of-window gains. "
                  "Excluding them is attribution only, NOT a valid rebacktest. "
                  "No mark/liquidation/price-path MMR parity or future account proof.",
    }


def find_paths(root: Path):
    candidates=[]
    for path in root.rglob("*.zip"):
        try:
            result=source_result(path)
        except zipfile.BadZipFile:
            continue
        if result is None:
            continue
        parts=path.parts
        cost=next((c.lower() for c in parts if c.lower() in ("base","stress")),None)
        year=next((p for p in parts if p in HISTORY),None)
        if year is None:
            year="2023_JUN_OCT"
        if cost is None:
            raise ValueError(f"cannot establish fee for {path}")
        candidates.append((year,cost,path,result))
    return candidates


def run(root:Path,outfile:Path):
    rows=[]
    for year,cost,path,result in find_paths(root):
        audit=inspect(result,label=year,cost=cost)
        audit["native_archived_file"]=str(path)
        rows.append(audit)
    if not rows:
        raise ValueError("no native source-backed R030 result archives")
    discovered={(r["original_label"],r["fee"]) for r in rows}
    for key,(n,expected) in EXPECT.items():
        if key not in discovered:
            raise ValueError(f"missing previously independently attested result {key}")
        row=next(x for x in rows if (x["original_label"],x["fee"])==key)
        if row["native_trade_count"]!=n or not math.isclose(
            row["original_wallet_net_pct"],expected,abs_tol=.0001
        ):
            raise ValueError(f"archived result mismatch vs pre-existing evidence {key}")
    report={
        "status":"R030_NATIVE_FINITE_WINDOW_FORCED_EXIT_ATTRIBUTION",
        "rows":sorted(rows,key=lambda x:(x["original_label"],x["fee"])),
        "frozen_source":"freqtrade/freqtrade-strategies Git blob "
                        "15ce2473f3f60bd33c4a67b0b8b228e379850f19",
        "warnings":[
            "Never claim 'organic-only' contribution is a real strategy account backtest.",
            "Original 2023 holdout has no complete historical mark/MMR liquidation proof.",
            "The 2024/25/2026 controlled wallet may differ from original author wallet.",
            "End-of-period forced exits change realized account PnL and may dominate "
            "short finite-window statistical screens; this is NOT robust positive edge.",
        ],
    }
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("R030_PNL_ATTRIBUTION",json.dumps(report["rows"],sort_keys=True))
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    run(args.root,args.output)


if __name__=="__main__":
    main()
