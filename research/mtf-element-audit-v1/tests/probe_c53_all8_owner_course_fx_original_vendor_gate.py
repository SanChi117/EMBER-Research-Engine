#!/usr/bin/env python3
"""C53 original FX chart source REQUIREMENTS without claiming historical feed data.

This script produces a deterministic source-only manifest for all eight verified
EURUSD OANDA/SAXO course source headers. No API credentials, no original OHLC
download, zero author chart raw bar goldens, no trades.
"""
import sys,json
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c53_fx_provider_original_source_attestation_gate import (
 review_all_eight_original_course_fx_sources,
 AUTHORS_GOLDENS_REQUIRED,OFFICIAL_DOCUMENTATION)
from c52_full_course_visual_49_source_inspection import FULL_SOURCE_HEADERS

PIN=ROOT/"evidence/c53/C53_EIGHT_ORIGINAL_FX_ACADEMIC_CHART_SOURCE_PROVIDER_PREFLIGHT.json"

def run(out=None):
    items=review_all_eight_original_course_fx_sources()
    assert len(items)==8
    assert {x.original_course_image_id for x in items}==set(FULL_SOURCE_HEADERS)
    assert len(AUTHORS_GOLDENS_REQUIRED)==6
    assert all(x.source_attestation_state=="SOURCE_NOT_RETRIEVED" for x in items)
    assert all(x.orders==x.trades==() and x.readiness=="NOT_TRADE_READY" for x in items)
    counters=Counter((x.original_tradingview_provider,
       x.original_tradingview_instrument,
       x.original_tradingview_tf) for x in items)
    assert counters==Counter({
     ("OANDA","EURUSD","4H"):3,
     ("OANDA","EURUSD","1H"):2,
     ("OANDA","EURUSD","15M"):1,
     ("SAXO","EURUSD","4H"):2})
    figure=[asdict(x) for x in items]
    data={
      "schema":"EMBER_C53_ORIGINAL_FX_OWNER_COURSE_PROVIDER_CANDLE_ATTESTATION_PREFLIGHT_V1",
      "date_utc":"2026-10-24",
      "owner_course_source_figures_with_real_FX_headers":8,
      "provider_instrument_timeframe_counts":[
        {"provider":provider,"instrument":symbol,"timeframe":tf,"sources":count}
        for (provider,symbol,tf),count in sorted(counters.items())],
      "original_screenchart_data_provider_endpoints_documented_by_vendor":OFFICIAL_DOCUMENTATION,
      "OANDA_v20_historical_candles_require_authorization":True,
      "SAXO_OpenAPI_historical_chart_samples_require_authorization":True,
      "OANDA_historical_broker_price_group_may_differ_from_live_chart_feed":True,
      "SAXO_FX_historical_candles_bid_ask_market_price_component_must_be_confirmed":True,
      "original_chart_market_bar_dates_UNKNOWN_despite_Tradingview_image_publication":True,
      "provider_exact_original_market_2024_2025_FX_candles_downloaded":0,
      "provider_authentication_credentials_received_or_stored":False,
      "course_screenshot_quote_mid_bid_ask_basis_verified":False,
      "original_2023_course_chart_entry_goldens":0,
      "author_verified_typed_POI_first_test":0,
      "author_verified_1H_VC":0,
      "author_verified_15M_entry_VC":0,
      "original_course_to_vendor_OHLC_candle_ID_matches":0,
      "unresolved_independent_evidence_barriers":list(AUTHORS_GOLDENS_REQUIRED),
      "academic_route_source_constraints":"4H POI to 1H trigger to 15M VC, 1H POI to 15M trigger to 5M VC routes are TEXT/FIGURE requirements only; source market 15M OHLC and author chart entry goldens not available yet.",
      "verified_original_FX_figure_source_gates":figure,
      "unrelated_BINANCE_USDM_2026_source_rejected_for_EURUSD":True,
      "no_forced_same_4H_UTC_alignment_for_OANDA_dailyAligned_H4_source":True,
      "orders":0,"trades":0,"PnL":None,"readiness":"NOT_TRADE_READY"}
    if out:
        f=Path(out);f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(data,sort_keys=True)),"C53_FROZEN_FX_SOURCE_PREFLIGHT_DRIFT"
    print(json.dumps({"observed_source_headers":8,"raw_vendor_fx_OHLC_records":0,
        "author_verified_goldens":0,"states":["SOURCE_NOT_RETRIEVED"]},sort_keys=True),flush=True)
    return data
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
