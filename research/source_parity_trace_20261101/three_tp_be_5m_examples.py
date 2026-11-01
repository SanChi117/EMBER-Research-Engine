"""Resolve P07/P10/P06 sample TP1→BE OHLC ambiguity using frozen USD-M 5m bars.

Only confirmed pre-existing TP1 levels and hypothetical initial stops are used.
No money math, no position sizing, no backtest returns, no claimed order fills.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIVE=ROOT/"binance_usdtm_5m_three_examples_20261101.csv"
HOUR=ROOT/"binance_usdtm_closed_20261101.csv"
DATA={
    "P07_SOL_20260901":{"symbol":"SOLUSDT","start":"2026-09-01T13:00:00Z",
                         "entry":101.87,"stop":102.68,"tp1":101.63,"side":-1},
    "P10_BTC_20260903":{"symbol":"BTCUSDT","start":"2026-09-03T14:00:00Z",
                         "entry":78802.2,"stop":77053.8,"tp1":79196.0,"side":1},
    "P06_BTC_20261002":{"symbol":"BTCUSDT","start":"2026-10-02T09:00:00Z",
                         "entry":86205.2,"stop":84820.7,"tp1":86365.5,"side":1},
}


def ms(text):
    return int(datetime.fromisoformat(text.replace("Z","+00:00")).timestamp()*1000)


def iso(t):
    return datetime.fromtimestamp(t/1000,timezone.utc).isoformat(timespec="minutes").replace("+00:00","Z")


def load():
    with FIVE.open(newline="") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==2592
    a={}
    for tag,defn in DATA.items():
        frame=[r for r in rows if r["event_id"]==tag]
        assert len(frame)==864
        assert all(r["symbol"]==defn["symbol"] and r["interval"]=="5m" for r in frame)
        base=ms(defn["start"])
        for i,r in enumerate(frame):
            assert int(r["open_time"])==base+i*300000
            assert int(r["close_time"])==base+(i+1)*300000-1
            assert float(r["high"])>=max(float(r["open"]),float(r["close"]))
            assert float(r["low"])<=min(float(r["open"]),float(r["close"]))
        assert float(frame[0]["open"])==defn["entry"]
        a[tag]=frame
    return a


def validate_h1_parity(a):
    with HOUR.open(newline="") as f:
        hourly={(r["symbol"],int(r["open_time"])):r
                for r in csv.DictReader(f) if r["interval"]=="1h"}
    for tag,rows in a.items():
        for i in range(0,len(rows),12):
            group=rows[i:i+12]
            assert len(group)==12
            orig=hourly[(DATA[tag]["symbol"],int(group[0]["open_time"]))]
            expected={"open":float(group[0]["open"]),
                      "high":max(float(x["high"]) for x in group),
                      "low":min(float(x["low"]) for x in group),
                      "close":float(group[-1]["close"])}
            for field,value in expected.items():
                assert abs(value-float(orig[field]))<1e-7,(
                    tag,orig["open_time"],field,value,orig[field]
                )


def hit(bar,price,side,target=False):
    if target:
        return float(bar["high"])>=price if side>0 else float(bar["low"])<=price
    return float(bar["low"])<=price if side>0 else float(bar["high"])>=price


def trace_tp1_be(tag,rows):
    d=DATA[tag]
    reached=None
    for bar in rows:
        if reached is None:
            stop=hit(bar,d["stop"],d["side"])
            tp=hit(bar,d["tp1"],d["side"],target=True)
            if stop and tp:
                return {"status":"AMBIGUOUS_INITIAL_SL_AND_TP1_SAME_5M",
                        "bar_open_utc":iso(int(bar["open_time"]))}
            if stop:
                return {"status":"INITIAL_SL_TOUCH_BEFORE_TP1",
                        "bar_open_utc":iso(int(bar["open_time"]))}
            if tp:
                reached=iso(int(bar["open_time"]))
                if hit(bar,d["entry"],d["side"]):
                    return {"status":"AMBIGUOUS_NEW_BE_AND_TP1_SAME_5M",
                            "tp1_bar_open_utc":reached}
        elif hit(bar,d["entry"],d["side"]):
            return {"status":"TP1_THEN_PRICE_LEVEL_BE_TOUCH_ON_LATER_5M",
                    "tp1_bar_open_utc":reached,
                    "be_bar_open_utc":iso(int(bar["open_time"]))}
    return {"status":"TP1_TOUCHED_NO_BE_IN_72H" if reached else "NO_TP1_IN_72H",
            "tp1_bar_open_utc":reached}


def run():
    assert hashlib.sha256(HOUR.read_bytes()).hexdigest()==(
        "b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
    )
    frames=load()
    validate_h1_parity(frames)
    return {"receipt_sha256":hashlib.sha256(FIVE.read_bytes()).hexdigest(),
            "raw_source":"Binance USD-M /fapi/v1/klines 5m 2026-11-01 fetch",
            "source_data_Git_blob_sha":"e574a70d0ab2842bf9e22dd56d84ae952ab9bd27",
            "total_bars":2592,
            "72h_5m_bar_to_1h_alignment":"EXACT_216_HOURLY_AGGREGATE_BARS",
            "scenario_only_no_fill_confirmation":True,
            "examples":{tag:trace_tp1_be(tag,x) for tag,x in frames.items()}}


if __name__=="__main__":
    print("EMBER_5M_TP1_BE="+json.dumps(run(),ensure_ascii=False))
