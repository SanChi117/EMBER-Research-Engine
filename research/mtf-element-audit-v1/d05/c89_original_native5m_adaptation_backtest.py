"""C89 real Binance USD-M 5m adapted Route A event-conditioned falsification.

This is NOT an unbiased full-strategy backtest: the 12 P0 context events
were selected by C73 from historical price patterns. Use their future
native 5m bars ONLY as an explicit assumption sensitivity / countertest.
The calendar holdout is a sanity check, not genuine independent discovery.

Downloads exactly C73 pinned monthly/daily 5m ZIPs (+ same-host checksum);
PAPER, no Binance order credentials, entry only at NEXT native 5m OPEN.
"""
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
from decimal import Decimal,InvalidOperation
from urllib.request import urlopen,Request
from urllib.error import HTTPError,URLError
from zipfile import ZipFile
from io import BytesIO,TextIOWrapper
import csv,hashlib,json,time

from c83_owner_course_text_crosswalk import source_matched_queue
from c86_original153_first_test_receipts import audit_stored_bytes
from c87_adapted_route_a_shadow_gate import audit_witness

class C89Rejected(ValueError):pass
STEP=300000
BASE="https://data.binance.vision/"
SPLIT=1789862400000  # 2026-09-20T00:00:00Z, predeclared
HORIZON_BARS=144  # 12 hours
COST_BPS=(7,14,25)
RR_VALUES=(1.5,2.0)
MIN_RISK_PCT=Decimal("0.002")
MAX_RISK_PCT=Decimal("0.04")
MAKER="BINANCE_USDM_ARCHIVE_SOURCE_NATIVE5M"
SOURCES=frozenset(("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"))

@dataclass(frozen=True)
class Bar:
    open_ms:int
    o:Decimal
    h:Decimal
    l:Decimal
    c:Decimal
    volume:Decimal
    @property
    def close_ms(self):return self.open_ms+STEP

def _decimal(x):
    try:v=Decimal(x)
    except (InvalidOperation,TypeError,ValueError):raise C89Rejected("NAN_OR_INVALID_PRICE")
    if not v.is_finite():raise C89Rejected("NONFINITE")
    return v

def parse_original5m_csv(raw,symbol,*,allow_header=True):
    if type(raw) is not bytes or symbol not in SOURCES:
        raise C89Rejected("CSV_SOURCE_BAD")
    out=[]
    try:
        lines=raw.decode("utf-8-sig").splitlines()
        for n,r in enumerate(csv.reader(lines)):
            if not r:continue
            if n==0 and allow_header and r[0].lower().strip().startswith("open"):
                continue
            if len(r)<6:raise C89Rejected("TRUNCATED_CSV")
            at=int(r[0])
            if at%STEP or (out and at!=out[-1].open_ms+STEP):
                raise C89Rejected("MISSING_DUPLICATE_OR_UNALIGNED_NATIVE5M_BAR")
            o,h,l,c,v=map(_decimal,r[1:6])
            if l<=0 or h<l or min(o,c)<l or max(o,c)>h or v<0:
                raise C89Rejected("IMPOSSIBLE_NATIVE_OHLCV")
            out.append(Bar(at,o,h,l,c,v))
    except (UnicodeDecodeError,ValueError,IndexError) as e:
        raise C89Rejected("UNPARSABLE_NATIVE5M_CSV") from e
    if not out:raise C89Rejected("EMPTY_ARCHIVE")
    return tuple(out)

def read_exact_archive(zip_bytes,symbol,meta):
    if type(zip_bytes) is not bytes or hashlib.sha256(zip_bytes).hexdigest()!=meta["zip_sha256"]:
        raise C89Rejected("FROZEN_BINANCE_ARCHIVE_SHA_MISMATCH")
    from zipfile import BadZipFile
    try:
        with ZipFile(BytesIO(zip_bytes)) as z:
            names=z.namelist()
            expected=meta["url"].split("/")[-1][:-4]+".csv"
            if names!=[expected]:raise C89Rejected("CSV_NAME_OR_EXTRA_ARCHIVE_MEMBERS")
            data=z.read(expected)
    except BadZipFile as e:raise C89Rejected("ZIP_INVALID") from e
    if hashlib.sha256(data).hexdigest()!=meta["raw_csv_sha256"]:
        raise C89Rejected("PINNED_RAW_CSV_SHA_MISMATCH")
    bars=parse_original5m_csv(data,symbol)
    if len(bars)!=meta["native5m_bars"]:
        raise C89Rejected("BINANCE_ARCHIVE_BAR_COUNT_DRIFT")
    return bars

def _safe_http(url):
    if type(url) is not str or not url.startswith(BASE+"data/futures/um/") or "?" in url:
        raise C89Rejected("UNTRUSTED_EXTERNAL_ARCHIVE_URL")
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={"User-Agent":"EMBER-PAPER-BACKTEST-C89"}),timeout=35) as r:
                return r.read()
        except (HTTPError,URLError,TimeoutError) as e:
            if attempt==2:raise C89Rejected("OFFICIAL_SOURCE_DOWNLOAD_UNAVAILABLE") from e
            time.sleep(1+attempt)
    raise C89Rejected("SOURCE_UNAVAILABLE")

def load_original_native5m(c73,*,fetch=_safe_http):
    if type(c73) is not bytes or hashlib.sha256(c73).hexdigest()!="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b":
        raise C89Rejected("C73_PIN_MISMATCH")
    d=json.loads(c73)
    out={}; manifest=[]
    for market in d["markets"]:
        sym=market["symbol"]
        if sym not in SOURCES:raise C89Rejected("UNKNOWN_MARKET_SYMBOL")
        archives=market["original5m_archives"]
        if len(archives)!=3:raise C89Rejected("EXPECTED_MONTHLY_PLUS_TWO_DAILY")
        bars=[]
        for a in archives:
            url=a["url"]
            if not url.startswith(BASE+"data/futures/um/"):
                raise C89Rejected("ARCHIVE_DOMAIN_MISMATCH")
            remote=fetch(url)
            sha=hashlib.sha256(remote).hexdigest()
            # same-provider .CHECKSUM is secondary, NOT an independent signature
            checksum=fetch(url+".CHECKSUM").decode("utf8").strip()
            if len(checksum.split())<2 or checksum.split()[0].lower()!=sha or checksum.split()[-1].split("/")[-1]!=url.split("/")[-1]:
                raise C89Rejected("BINANCE_SAME_HOST_CHECKSUM_MISMATCH")
            part=read_exact_archive(remote,sym,a)
            if bars and part[0].open_ms!=bars[-1].open_ms+STEP:
                raise C89Rejected("MISSING_NATIVE_5M_ARCHIVE_JOIN")
            bars.extend(part)
            manifest.append({"symbol":sym,"url":url,
              "zip_sha256":sha,"csv_sha256":a["raw_csv_sha256"],"bars":len(part)})
        if len(bars)!=9216 or sym in out:raise C89Rejected("SOURCE_WINDOW_DRIFT")
        out[sym]=tuple(bars)
    if len(out)!=5 or len(manifest)!=15:raise C89Rejected("EXPECTED_5_MARKETS_15_ARCHIVES")
    return out,manifest

def _scenario_one(bars,event,*,rr,cost_bps):
    if type(bars) is not tuple or any(type(b) is not Bar for b in bars) or not bars:
        raise C89Rejected("TYPED_SOURCE_5M_REQUIRED")
    if type(event) is not dict or event.get("priority")!=0 or event.get("readiness")!="NOT_TRADE_READY":
        raise C89Rejected("EXACT_P0_SOURCE_ONLY")
    if type(rr) not in (int,float) or type(cost_bps) not in (int,float) or rr<=1 or cost_bps<0:
        raise C89Rejected("RISK_PARAMETERS")
    signal=event["first5m_known_ms"]
    if type(signal) is not int or signal%STEP:raise C89Rejected("SIGNAL_BEFORE_5M_CLOSE")
    # Native 5m candle at signal-STEP is the last fully-closed info.
    lookup={b.open_ms:i for i,b in enumerate(bars)}
    i=lookup.get(signal)
    if i is None:return {"case":event["case_key"],"status":"NO_NEXT_BAR_NO_TRADE"}
    if i<15:return {"case":event["case_key"],"status":"ATR_WARMUP_UNAVAILABLE"}
    previous=bars[i-15:i]
    if previous[-1].close_ms!=signal:
        raise C89Rejected("CLOSE_TIMESTAMP_UNAVAILABLE")
    # ATR uses only 14 fully CLOSED native 5m candles.
    tr=[]
    for a,b in zip(previous[:-1],previous[1:]):
        tr.append(max(b.h-b.l,abs(b.h-a.c),abs(b.l-a.c)))
    atr=sum(tr)/Decimal(len(tr))
    if atr<=0: return {"case":event["case_key"],"status":"INVALID_ATR"}
    entry=bars[i].o
    side=event["side"]
    if side not in ("LONG","SHORT"):raise C89Rejected("INVALID_SIDE")
    low=_decimal(event["poi_low"]);high=_decimal(event["poi_high"])
    if not 0<low<high:raise C89Rejected("POI_INVERTED")
    # Hypothesis: structure edge + 15% (known) ATR buffer, never fake author SL.
    buffer=atr*Decimal("0.15")
    stop=min(low-buffer,entry-atr*Decimal("0.4")) if side=="LONG" else max(high+buffer,entry+atr*Decimal("0.4"))
    risk=abs(entry-stop)
    risk_pct=risk/entry
    if risk_pct<MIN_RISK_PCT or risk_pct>MAX_RISK_PCT:
        return {"case":event["case_key"],"status":"STOP_OUTSIDE_PREDECLARED_BOUNDS",
                "risk_pct":round(float(risk_pct)*100,5)}
    target=entry+Decimal(str(rr))*risk if side=="LONG" else entry-Decimal(str(rr))*risk
    if target<=0:return {"case":event["case_key"],"status":"NONPOSITIVE_TARGET"}
    end=min(i+HORIZON_BARS,len(bars))
    if end<=i:return {"case":event["case_key"],"status":"NO_FORWARD_BARS"}
    exit_price=None;reason=None;index=None
    for ix in range(i,end):
        b=bars[ix]
        if b.open_ms!=signal+(ix-i)*STEP:
            raise C89Rejected("FORWARD_CANDLE_GAP")
        # gap at open can worsen STOP (or improve target); conservative.
        if side=="LONG":
            if b.o<=stop:exit_price=b.o;reason="GAP_STOP";index=ix;break
            if b.o>=target:exit_price=target;reason="TP_AT_OR_BEFORE_OPEN";index=ix;break
            touch_sl=b.l<=stop;touch_tp=b.h>=target
        else:
            if b.o>=stop:exit_price=b.o;reason="GAP_STOP";index=ix;break
            if b.o<=target:exit_price=target;reason="TP_AT_OR_BEFORE_OPEN";index=ix;break
            touch_sl=b.h>=stop;touch_tp=b.l<=target
        if touch_sl:exit_price=stop;reason="STOP_PRIORITY_IF_SAME_BAR";index=ix;break
        if touch_tp:exit_price=target;reason="TP";index=ix;break
    if exit_price is None:
        index=end-1;exit_price=bars[index].c;reason="TIME_LIMIT"
    direction=Decimal(1 if side=="LONG" else -1)
    gross=direction*(exit_price-entry)/risk
    # bps includes BOTH directions: roundtrip fee+slippage as notional.
    costs=Decimal(str(cost_bps))/Decimal(10000)*entry/risk
    net=gross-costs
    return {"case":event["case_key"],"symbol":event["symbol"],"side":side,
      "source_event_known_ms":signal,"entry_open_ms":bars[i].open_ms,
      "exit_bar_close_ms":bars[index].close_ms,"entry":str(entry),
      "stop":str(stop),"target":str(target),"exit":str(exit_price),
      "risk_pct":round(float(risk_pct)*100,5),"gross_r":round(float(gross),6),
      "net_r":round(float(net),6),"exit_reason":reason,
      "status":"CLOSED_HYPOTHETICAL_PAPER","evidence_class":"ADAPTED_HYPOTHESIS"}

def diagnostic(c73,c72,c81,c86,c87,bars_by_symbol,manifest):
    audit_stored_bytes(c73,c72,c81,c86)
    audit_witness(c73,c72,c81,c86,c87)
    q=source_matched_queue(c73,c72,c81)
    if set(bars_by_symbol)!=SOURCES or len(q)!=153:raise C89Rejected("SOURCE_UNIVERSE_MISMATCH")
    for sym,bars in bars_by_symbol.items():
        if len(bars)!=9216 or any(bars[k+1].open_ms!=bars[k].open_ms+STEP for k in range(len(bars)-1)):
            raise C89Rejected("MISSING_FULL_ORIGINAL_32DAY_5M_HISTORY")
    events=[{"case_key":x.source_key,"priority":x.priority,"symbol":x.symbol,"side":x.side,
             "first5m_known_ms":x.first5m_known_ms,"poi_low":x.poi_low,"poi_high":x.poi_high,
             "readiness":x.readiness} for x in q if x.priority==0]
    if len(events)!=12:raise C89Rejected("P0_COUNT_CHANGED")
    results={}
    for rr in RR_VALUES:
        for cost in COST_BPS:
            key=f"rr{rr}_roundtrip{cost}bps"
            trades=[_scenario_one(bars_by_symbol[e["symbol"]],e,rr=rr,cost_bps=cost) for e in events]
            closed=[t for t in trades if t["status"]=="CLOSED_HYPOTHETICAL_PAPER"]
            train=[t for t in closed if t["entry_open_ms"]<SPLIT]
            late=[t for t in closed if t["entry_open_ms"]>=SPLIT]
            def stats(seq):
                vals=[x["net_r"] for x in seq]
                wins=sum(x>0 for x in vals)
                gain=sum(max(x,0) for x in vals);loss=-sum(min(x,0) for x in vals)
                return {"trades":len(vals),"win_rate_pct":round(100*wins/len(vals),3) if vals else None,
                        "net_total_r":round(sum(vals),6) if vals else None,
                        "mean_net_r":round(sum(vals)/len(vals),6) if vals else None,
                        "profit_factor":round(gain/loss,5) if loss else None}
            results[key]={"train":stats(train),"late_coverage":stats(late),
                           "all_source_preselected":stats(closed),
                           "rejections":dict(sorted(Counter(t["status"] for t in trades if t["status"]!="CLOSED_HYPOTHETICAL_PAPER").items())),
                           "hypothetical_scenarios":trades}
    return {"schema":"C89_ORIGINAL_BINANCE_REAL5M_EVENT_CONDITIONED_ADAPTATION_BACKTEST",
            "sampling_limitation":"C73 PRESELECTED HISTORICAL SOURCE EVENTS. NOT a prospective or independently discovered strategy; calendar split is NOT unbiased OOS.",
            "source_market":MAKER,"original_cases":153,"preselected_p0_events":12,
            "verified_5m_archives":manifest,"hypothesis_grid":{"rr":list(RR_VALUES),"roundtrip_all_in_cost_bps":list(COST_BPS),
             "atr_stop_buffer_multiple":"0.15","atr_min_stop_multiple":"0.4","max_hold_5m_bars":HORIZON_BARS,
             "min_stop_pct":"0.20","max_stop_pct":"4.0","same_bar_stop_first":True,
             "next_bar_open_entry":True,"slippage_fee_model":"roundtrip_bps_of_notional_not_R"},
            "data_partition":{"early_before_utc_ms":SPLIT,"late_at_or_after_utc_ms":SPLIT,
               "late_not_independent_OOS":True},
            "results":results,
            "owner_semantics_verified":False,
            "no_realtime_orders":True,"research_state":"PAPER_ONLY_HYPOTHESIS_NOT_TRADE_READY"}
def dump_result(obj):
    return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
