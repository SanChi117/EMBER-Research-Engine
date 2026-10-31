"""A240: replay original Binance Futures source data providers for author BTC/ETH only.
This wrapper changes only downloader symbol sets, not source market values/strategies.
"""
from __future__ import annotations
import argparse
import importlib
import json
import sys
from pathlib import Path

BASE="research.doublema_native_oos_20261031"
COINS=("BTCUSDT","ETHUSDT")
PAIRS=("BTC_USDT_USDT","ETH_USDT_USDT")

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--period",required=True,choices=("2025","2026"))
    cli.add_argument("--datadir",required=True)
    args=cli.parse_args()
    root=Path(args.datadir).resolve()
    root.mkdir(parents=True,exist_ok=True)
    print("A240_PREPARING_AUTHENTIC_BINANCE_USDM",args.period,COINS,flush=True)
    if args.period=="2025":
        m=importlib.import_module(BASE+".a197_prepare_2025_alternate_regime")
        m.SYMS=COINS
        sys.argv=["a197_prepare_2025_alternate_regime.py","--datadir",str(root)]
        m.main()
        manifest_path=root/"A197_2025_AUTHENTIC_SOURCE_SHA_MANIFEST.json"
        manifest=json.loads(manifest_path.read_text("utf8"))
        assert tuple(manifest["counts"])==COINS
        assert all(manifest["counts"][sym]["funding_settlements"]>900 for sym in COINS)
    else:
        m=importlib.import_module(BASE+".a195_prepare_crosspair")
        m.SYMBOLS=COINS
        sys.argv=["a195_prepare_crosspair.py","--datadir",str(root)]
        m.main()
        d=importlib.import_module(BASE+".a196_prepare_real_5m_detail")
        d.SYMBOLS=COINS
        sys.argv=["a196_prepare_real_5m_detail.py","--datadir",str(root)]
        d.main()
        manifest_path=root/"A195_DATA_SHA_MANIFEST.json"
        manifest=json.loads(manifest_path.read_text("utf8"))
        assert tuple(manifest["data"])==COINS
        assert all(manifest["data"][sym]["funding_settlements"]>400 for sym in COINS)
        detail=json.loads((root/"A196_REAL_5M_SHA_MANIFEST.json").read_text("utf8"))
        assert tuple(detail["symbols"])==COINS
    for coin in PAIRS:
        for tf in ("1h","4h","1d","5m"):
            f=root/"futures"/f"{coin}-{tf}-futures.json"
            assert f.is_file() and f.stat().st_size>100,(str(f),"missing_untrusted_data")
        for kind in ("1h-mark.json","1h-funding_rate.json"):
            f=root/"futures"/f"{coin}-{kind}"
            assert f.is_file() and f.stat().st_size>100,(str(f),"missing_untrusted_funding_or_mark")
    print("A240_BTC_ETH_FUTURES_GENUINE_INPUTS_VALIDATED",args.period,str(manifest_path),flush=True)

if __name__=="__main__":
    main()
