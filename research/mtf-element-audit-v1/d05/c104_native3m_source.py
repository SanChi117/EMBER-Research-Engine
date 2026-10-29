"""C104 SOURCE: own strict Binance Vision USD-M 3m ZIP parser for ten preregistered coins. PAPER only."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D
from datetime import datetime,timezone
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile,BadZipFile
import csv
from c21_native3m_source_bridge import Original3mRow,THREE
from c89_original_native5m_adaptation_backtest import BASE,_safe_http
import c102_c103_native3m_new_symbol_transfer as c102

class C104SourceError(ValueError): pass
SYMBOLS=("AAVEUSDT","APTUSDT","ARBUSDT","ATOMUSDT","ETCUSDT",
         "FILUSDT","LTCUSDT","NEARUSDT","TRXUSDT","UNIUSDT")
DAYS=c102.DAYS
EXPECTED=320

def daily(sym,date,*,fetch=_safe_http):
    if sym not in SYMBOLS or date not in DAYS:
        raise C104SourceError("UNREGISTERED_10_SYMBOLS_32_DAYS")
    stem=f"{sym}-3m-{date}"
    url=f"{BASE}data/futures/um/daily/klines/{sym}/3m/{stem}.zip"
    data=fetch(url);check=fetch(url+".CHECKSUM")
    if type(data) is not bytes or type(check) is not bytes or not 0<len(data)<=30000000:
        raise C104SourceError("MISSING_OFFICIAL_NATIVE3M")
    digest=sha256(data).hexdigest();fields=check.decode("ascii").strip().split()
    if len(fields)!=2 or fields[0].lower()!=digest or fields[1].split("/")[-1]!=stem+".zip":
        raise C104SourceError("PROVIDER_CHECKSUM_MISMATCH")
    try:
        with ZipFile(BytesIO(data)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=stem+".csv" or
                members[0].is_dir() or members[0].flag_bits&1 or
                members[0].file_size>30000000):
                raise C104SourceError("ZIP_MEMBER_INVALID")
            raw=z.read(members[0])
    except (BadZipFile,EOFError) as ex:
        raise C104SourceError("BINANCE_ZIP_CORRUPT") from ex
    lines=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if lines and lines[0][0].lower().strip() in ("open_time","open time"):
        lines=lines[1:]
    if len(lines)!=480:raise C104SourceError("PARTIAL_ORIGINAL_3M_DAY")
    start=c102.timestamp(date);out=[]
    for i,row in enumerate(lines):
        if len(row)!=12:raise C104SourceError("WRONG_NATIVE_CSV_COLUMNS")
        at=start+i*THREE
        try:
            stamp,closed,count=int(row[0]),int(row[6]),int(row[8])
            o,h,l,c,v=[c102.dec(row[j]) for j in (1,2,3,4,5)]
            quote,taker,takerq=[c102.dec(row[j]) for j in (7,9,10)]
        except c102.C102Rejected as ex:
            raise C104SourceError("BAD_FINITE_NATIVE_PRICE") from ex
        except (ValueError,IndexError) as ex:
            raise C104SourceError("BAD_NATIVE_CSV_CLOCK") from ex
        if stamp!=at or closed!=at+THREE-1 or count<0:
            raise C104SourceError("NATIVE3M_GAP_UNCLOSED_DUPLICATE")
        if not (0<l<=min(o,c)<=max(o,c)<=h and min(v,quote,taker,takerq)>=0):
            raise C104SourceError("IMPOSSIBLE_SOURCE_OHLCV")
        out.append(Original3mRow(sym,at,at+THREE,o,h,l,c,v,
                   digest+":"+str(at),digest))
    return tuple(out),{"symbol":sym,"date":date,"timeframe":"NATIVE_3M",
       "zip_sha256":digest,"csv_sha256":sha256(raw).hexdigest(),
       "bars":len(out),"source":url}

def load(*,fetch=_safe_http):
    todo=[(sym,date) for sym in SYMBOLS for date in DAYS]
    def get(pair):
        sym,date=pair;return pair,*daily(sym,date,fetch=fetch)
    with ThreadPoolExecutor(max_workers=10) as pool:
        fetched=list(pool.map(get,todo))
    if len(fetched)!=EXPECTED:raise C104SourceError("320_BINANCE_ZIPS_REQUIRED")
    market={s:[] for s in SYMBOLS};receipts=[]
    for (sym,date),bars,meta in fetched:
        xs=market[sym]
        if xs and xs[-1].known_ms!=bars[0].start_ms:
            raise C104SourceError("DAILY_3M_CLOCK_BREAK")
        xs.extend(bars);receipts.append(meta)
    if len({(r["symbol"],r["date"]) for r in receipts})!=EXPECTED:
        raise C104SourceError("DUPLICATED_DAILY_ZIP")
    for sym,xs in market.items():
        if len(xs)!=15360 or xs[0].start_ms!=c102.BEGIN_MS or xs[-1].known_ms!=c102.END_MS:
            raise C104SourceError("FULL_32DAY_SHA_SOURCE_REQUIRED")
    return {s:tuple(xs) for s,xs in market.items()},receipts
