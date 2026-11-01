"""Resolve 5m same-bar P07 SHORT TP1/BE order using frozen genuine USD-M 1m.

A level TOUCH is not proof of a queue fill or fee-adjusted break-even.
No PnL, live orders, target tuning, or money calculations.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ONE=HERE/"binance_usdtm_1m_p07_example_20261101.csv"
FIVE=HERE/"binance_usdtm_5m_three_examples_20261101.csv"
TP1=101.63
ENTRY=101.87
SOURCE_INITIAL_SL_PROXY=102.68


def run():
    with ONE.open(newline="") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==15
    assert all(x["symbol"]=="SOLUSDT" and x["interval"]=="1m"
               and x["event_id"]=="P07_SOL_20260901" for x in rows)
    t0=1788267600000
    for i,r in enumerate(rows):
        assert int(r["open_time"])==t0+i*60000
        assert int(r["close_time"])==t0+(i+1)*60000-1
        assert float(r["high"])>=max(float(r["open"]),float(r["close"]))
        assert float(r["low"])<=min(float(r["open"]),float(r["close"]))
    with FIVE.open(newline="") as f:
        fives=[x for x in csv.DictReader(f) if x["event_id"]=="P07_SOL_20260901"]
    assert len(fives)>=3
    for j in range(3):
        group=rows[j*5:j*5+5]
        same=fives[j]
        assert float(same["open"])==float(group[0]["open"])
        assert float(same["close"])==float(group[-1]["close"])
        assert float(same["high"])==max(float(x["high"]) for x in group)
        assert float(same["low"])==min(float(x["low"]) for x in group)

    stage=0;events=[]
    for r in rows:
        current_high=float(r["high"])
        current_low=float(r["low"])
        at=r["open_time"]
        if stage==0:
            if current_high>=SOURCE_INITIAL_SL_PROXY:
                raise AssertionError("Original source SL proxy touched before TP1")
            if current_low<=TP1:
                if current_high>=ENTRY:
                    return {"status":"STILL_AMBIGUOUS_1M", "minute_at":at}
                stage=1
                events.append({"event":"TP1_PRICE_TOUCHED","minute_open_ms":int(at)})
        elif current_high>=ENTRY:
            events.append({"event":"BE_PRICE_TOUCHED_AFTER_TP1","minute_open_ms":int(at)})
            stage=2
            break
    assert stage==2,events
    assert events[0]["minute_open_ms"]==1788267660000
    assert events[1]["minute_open_ms"]==1788268080000
    return {"status":"TP1_THEN_BE_PRICE_TOUCHED_UNAMBIGUOUS_ON_1M",
            "raw_data_blob_sha":"c5f869b593d3c32bf5597c1a4f0d0398bc6a9d24",
            "raw_data_sha256":hashlib.sha256(ONE.read_bytes()).hexdigest(),
            "bars":len(rows),"exact_1m_5m_alignment":True,"events":events,
            "orders_filled_not_asserted":True}


if __name__=="__main__":
    print("EMBER_P07_1M_RESOLUTION="+json.dumps(run(),ensure_ascii=False))
