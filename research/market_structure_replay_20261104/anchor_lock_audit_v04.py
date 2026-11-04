"""MSR-04: compare 15m BOS pivot frozen at ACCUMULATION vs sweep-time pivot.
Research-only and read-only; old events and order systems are untouched.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from replay import read_csv, replay

def ms(ts):
    d=datetime.fromisoformat(ts.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset().total_seconds()!=0:
        raise ValueError("UTC timestamps required")
    return int(d.timestamp()*1000)

def compare(events):
    by_symbol=defaultdict(list)
    for e in events: by_symbol[e["symbol"]].append(e)
    output=[]
    for symbol in sorted(by_symbol):
        pivots={1:None,-1:None}
        boxes={}
        sweeps={}
        last=-1
        for e in by_symbol[symbol]:
            t=ms(e["known_at"])
            if t<last: raise ValueError("source timestamps unsorted")
            last=t
            typ=e["event"]
            cid=e.get("candidate_id","-")
            if typ=="PIVOT_HIGH_CONFIRMED":
                pivots[1]=(float(e["pivot_price"]),e["known_at"])
            elif typ=="PIVOT_LOW_CONFIRMED":
                pivots[-1]=(float(e["pivot_price"]),e["known_at"])
            elif typ=="ACCUMULATION_LOCKED":
                if cid in boxes: raise ValueError("duplicate accumulation lock")
                boxes[cid]={"at":e["known_at"],"anchors":pivots.copy(),
                            "lo":float(e["level_low"]),"hi":float(e["level_high"]),
                            "atr":float(e["atr1h"])}
            elif typ=="SWEEP_RETURN":
                d=int(e["side"])
                if d not in (-1,1) or cid not in boxes or cid in sweeps:
                    raise ValueError("orphan or duplicate sweep")
                p=pivots[d]
                if p is None or p[0]!=float(e["reference"]) or p[1]!=e["pivot_known_at"]:
                    raise ValueError("sweep pivot does not match causal snapshot")
                if ms(p[1])>t: raise ValueError("future sweep pivot")
                sweeps[cid]={"at":e["known_at"],"side":d,"pivot":p}
            elif typ=="STRUCTURE_BREAK_CONFIRMED":
                if cid not in boxes or cid not in sweeps:
                    raise ValueError("orphan BOS")
                box,sweep=boxes[cid],sweeps[cid]
                d=int(e["side"])
                if d!=sweep["side"]:raise ValueError("direction changed")
                if not(ms(box["at"])<ms(sweep["at"])<t):
                    raise ValueError("invalid A-M-BOS chronology")
                old=box["anchors"][d]
                new=sweep["pivot"]
                if new!=(float(e["reference"]),e["pivot_known_at"]):
                    raise ValueError("BOS reference changed after sweep")
                changed=old!=new
                change_price=bool(old and old[0]!=new[0])
                row={
                    "symbol":symbol,"candidate_id":cid,"side":d,
                    "box_at":box["at"],"sweep_at":sweep["at"],"bos_at":e["known_at"],
                    "box_low":box["lo"],"box_high":box["hi"],"atr1h_box":box["atr"],
                    "anchor_at_box":old[0] if old else None,
                    "anchor_known_at_box":old[1] if old else None,
                    "anchor_at_sweep":new[0],"anchor_known_at_sweep":new[1],
                    "anchor_reselected":changed,"anchor_price_changed":change_price,
                    "anchor_shift_atr1h":(new[0]-old[0])/box["atr"] if old and box["atr"]>0 else None,
                    "pivot_known_after_box":ms(new[1])>ms(box["at"]),
                    "pivot_known_on_sweep":new[1]==sweep["at"],
                    "pivot_inside_box":box["lo"]<=new[0]<=box["hi"],
                    "anchor_status":"MISSING_AT_BOX" if old is None else
                        "RESELECTED" if changed else "UNCHANGED",
                    "note":"Source event log lacks BOS candle close; this is NOT a valid frozen-anchor breakout test."
                }
                output.append(row)
    return output

def summarize(rows):
    return {
        "bos":len(rows),
        "unique_symbol_time_direction":len({(r["symbol"],r["bos_at"],r["side"]) for r in rows}),
        "reselected":sum(r["anchor_reselected"] for r in rows),
        "price_changed":sum(r["anchor_price_changed"] for r in rows),
        "pivot_known_after_box":sum(r["pivot_known_after_box"] for r in rows),
        "on_sweep":sum(r["pivot_known_on_sweep"] for r in rows),
        "inside_box":sum(r["pivot_inside_box"] for r in rows),
        "missing_box_anchor":sum(r["anchor_at_box"] is None for r in rows),
        "status":"CAUSAL_DIAGNOSTIC_NOT_EXPERT_TRUTH_NO_TRADES"
    }

def run(paths,out):
    receipts=[]; rows=[]; total=Counter()
    for path in sorted(paths):
        data,sha=read_csv(path)
        events=replay(data).events
        rows.extend(compare(events))
        total.update(e["event"] for e in events)
        receipts.append({"symbol":data[0].symbol,"bars":len(data),"sha256":sha})
    summary=summarize(rows)
    summary["source_receipts"]=receipts
    summary["source_event_counts"]=dict(total)
    out.mkdir(parents=True,exist_ok=True)
    if rows:
        with (out/"anchor_ledger.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--csv",nargs="+",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(run(a.csv,a.out),ensure_ascii=False,indent=2))
