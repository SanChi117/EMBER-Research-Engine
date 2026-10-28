"""C92 extended ORIGINAL Binance USD-M native5m full-calendar research replay.

Add 2026-04..2026-08 monthly ZIP to exact pinned 2026-09 + Oct1/2
C73 15-archive source; provider SHA256 CHECKSUM + ZIP member name;
freeze download digest witness and require identical on independent CI rerun.
Never optimize parameters from evaluation periods or assert pristine OOS.
PAPER ONLY; no order API; no C73 preselected event filtering.
"""
from io import BytesIO
from zipfile import ZipFile,BadZipFile
from collections import Counter
from hashlib import sha256
from c89_original_native5m_adaptation_backtest import (
 Bar,STEP,SOURCES,BASE,C89Rejected,_safe_http,parse_original5m_csv,
 load_original_native5m)
from c91_continuous_causal_route_a_paper import analyze,dumps
MONTHS=("2026-04","2026-05","2026-06","2026-07","2026-08")
MARKETS=("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")
TOTAL_MONTHLY=25
MAX_ZIP_BYTES=20_000_000
class C92Rejected(ValueError):pass
def _monthly_archive(symbol,month,*,fetch=_safe_http):
    if symbol not in SOURCES or month not in MONTHS:
        raise C92Rejected("UNREGISTERED_SOURCE_PERIOD_SYMBOL")
    name=f"{symbol}-5m-{month}"
    url=f"{BASE}data/futures/um/monthly/klines/{symbol}/5m/{name}.zip"
    raw=fetch(url)
    if type(raw) is not bytes or not 0<len(raw)<MAX_ZIP_BYTES:
        raise C92Rejected("DOWNLOAD_SIZE_OR_TYPE")
    digest=sha256(raw).hexdigest()
    checksum=fetch(url+".CHECKSUM")
    if type(checksum) is not bytes:
        raise C92Rejected("CHECKSUM_NOT_BYTES")
    words=checksum.decode("ascii").strip().split()
    if len(words)!=2 or words[0].lower()!=digest or words[1].split("/")[-1]!=name+".zip":
        raise C92Rejected("BINANCE_PROVIDER_CHECKSUM_MISMATCH")
    try:
        with ZipFile(BytesIO(raw)) as z:
            if z.namelist()!=[name+".csv"]:
                raise C92Rejected("NOT_EXACT_ORIGINAL_ZIP_MEMBER")
            csvdata=z.read(name+".csv")
    except BadZipFile as e:
        raise C92Rejected("INVALID_ORIGINAL_BINANCE_ZIP") from e
    bars=parse_original5m_csv(csvdata,symbol)
    # Existing C89 original native type carries source price and time only.
    return bars,{"symbol":symbol,"period":month,"url":url,
        "zip_sha256":digest,"csv_sha256":sha256(csvdata).hexdigest(),
        "bars":len(bars),"source":"BINANCE_USDM_PROVIDER_CHECKSUM"}

def load_extended_original(c73,*,fetch=_safe_http):
    original,old_manifest=load_original_native5m(c73,fetch=fetch)
    markets={};manifest=[];expected=0
    for sym in MARKETS:
        bars=[]
        for m in MONTHS:
            part,meta=_monthly_archive(sym,m,fetch=fetch)
            if bars and part[0].open_ms!=bars[-1].close_ms:
                raise C92Rejected("GAP_OR_OVERLAP_IN_MONTHLY_ARCHIVES")
            bars.extend(part);manifest.append(meta)
        sep_oct=original[sym]
        if not bars or bars[-1].close_ms!=sep_oct[0].open_ms:
            raise C92Rejected("MONTH_TO_PINNED_SEPTEMBER_GAP")
        bars.extend(sep_oct)
        if any(a.close_ms!=b.open_ms for a,b in zip(bars,bars[1:])):
            raise C92Rejected("FULL_TIMELINE_DISCONTINUITY")
        markets[sym]=tuple(bars)
        expected+=len(bars)
    if len(manifest)!=TOTAL_MONTHLY or len(old_manifest)!=15 or len(markets)!=5:
        raise C92Rejected("CALENDAR_SOURCE_UNIVERSE_MISMATCH")
    return markets,{"new_monthly_25":manifest,"original_sep_oct_15":old_manifest,
        "total_bars":expected,"source_exhaustion":False,
        "provider_signature_limit":"BINANCE_CHECKSUM_SAME_HOST_NOT_INDEPENDENT_CRYPTO_SIGNATURE"}
def run(c73,*,fetch=_safe_http):
    markets,metadata=load_extended_original(c73,fetch=fetch)
    result=analyze(markets,metadata["new_monthly_25"]+metadata["original_sep_oct_15"])
    result["expanded_source"]={**metadata,"months":list(MONTHS)}
    result["source_period"]="2026-04-01--2026-10-02_UTC"
    result["no_trading_edge_claim"]=True
    result["research_only"]="PAPER_ONLY_ADAPTED_HYPOTHESIS"
    return result
