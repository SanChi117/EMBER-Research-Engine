"""C53 source vendor bar receipt cannot certify an academic TradingView FX example."""
import unittest
from dataclasses import replace
from datetime import datetime,timezone
from c53_fx_provider_original_source_attestation_gate import (
  SourceBarReceipt,assess_course_figure_original_fx_source,
  review_all_eight_original_course_fx_sources,
  STATES,AUTHORS_GOLDENS_REQUIRED,OFFICIAL_DOCUMENTATION,HOUR)
from c52_full_course_visual_49_source_inspection import FULL_SOURCE_HEADERS

ID_OANDA_4H="153eXt9lGrrhRumOfFsLQryS-3FBBX8Vl"
ID_OANDA_1H="1HuwTCxVYvm_YSmaPpZ2RxD7PA9UuzwtC"
ID_OANDA_15M="1obj4bBVqplvrL2E_iNHXOHoOaDhj5gKx"
ID_SAXO_4H="1F0LLCklPaPNCBWHwVpsKUPqp1hdsh35p"

def stamp(day="2024-05-22T07:00:00+00:00"):
    return int(datetime.fromisoformat(day).timestamp()*1000)

def raw(provider="OANDA",timeframe="4H",instrument="EURUSD",side="MID",
        start=None):
    step={"4H":4*HOUR,"1H":HOUR,"15M":15*60*1000}[timeframe]
    k=stamp() if start is None else start
    return SourceBarReceipt(provider,instrument,timeframe,side,
        "https://api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles" if provider=="OANDA"
        else "https://gateway.saxobank.com/openapi/chart/v3/charts",
        "a"*64,k,k+step,"1.08200","1.08400","1.08100","1.08300",
        "source:fxbar-id:"+str(k),True)

class C53FxSourceNotAcademicGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=review_all_eight_original_course_fx_sources()
    def gate(self,id=ID_OANDA_4H,receipt=None):
        return assess_course_figure_original_fx_source(id,market_receipt=receipt)
    def rejected(self,pattern,receipt,id=ID_OANDA_4H):
        with self.assertRaisesRegex(ValueError,pattern):self.gate(id,receipt)
    def test_eight_source_fx_publisher_images_missing_raw(self):
        self.assertEqual(len(self.review),8)
        self.assertEqual(sum(x.raw_source_receipt_present for x in self.review),0)
    def test_original_source_provider_only_not_retrieved(self):
        self.assertTrue(all(x.source_attestation_state=="SOURCE_NOT_RETRIEVED" for x in self.review))
    def test_eurusd_OANDA_2024_source_4h_observed(self):
        x=self.gate()
        self.assertEqual((x.original_tradingview_provider,x.original_tradingview_instrument,x.original_tradingview_tf),
            ("OANDA","EURUSD","4H"))
    def test_original_publication_not_market_timestamp(self):
        self.assertTrue(all(x.chart_publication_time_NOT_market_bar_time for x in self.review))
    def test_eight_original_figures_still_not_trade_ready(self):
        self.assertTrue(all(x.orders==x.trades==() and x.readiness=="NOT_TRADE_READY" for x in self.review))
    def test_synthetic_OANDA_provider_receipt_only_source_not_author(self):
        x=self.gate(receipt=raw())
        self.assertTrue(x.raw_source_receipt_present)
        self.assertEqual(x.source_attestation_state,"PROVIDER_ONLY_SOURCE_RECEIVED_CHART_CANDLE_UNALIGNED")
        self.assertFalse(x.actual_original_author_POI_or_VC_golden or x.author_entry_trade_ready)
    def test_synthetic_OANDA_1h_receipt_separate_tf(self):
        x=self.gate(ID_OANDA_1H,raw(timeframe="1H"))
        self.assertEqual(x.original_tradingview_tf,"1H")
    def test_synthetic_OANDA_15m_receipt_separate_tf(self):
        x=self.gate(ID_OANDA_15M,raw(timeframe="15M"))
        self.assertEqual(x.original_tradingview_tf,"15M")
    def test_synthetic_SAXO_only_matching_saxo_provider(self):
        x=self.gate(ID_SAXO_4H,raw(provider="SAXO",side="BID",start=stamp("2025-01-06T08:00:00+00:00")))
        self.assertEqual(x.original_tradingview_provider,"SAXO")
        self.assertFalse(x.independently_matched_chart_bar_ohlc)
    def test_source_receipt_cannot_fill_orders(self):
        x=self.gate(receipt=raw())
        self.assertEqual((x.orders,x.trades,x.readiness),((),(),"NOT_TRADE_READY"))
    def test_source_receipt_cannot_turn_on_chart_price_basis(self):
        x=self.gate(receipt=raw())
        self.assertFalse(x.screenshot_quote_price_side_verified)
    def test_source_receipt_cannot_verify_actual_screen_candle_time(self):
        x=self.gate(receipt=raw())
        self.assertFalse(x.screenshot_bar_timestamp_verified)
    def test_synthetic_raw_source_provider_mismatch_blocked(self):
        self.rejected("PROVIDER_INSTRUMENT_TF_OR_PRICE_SIDE_MISMATCH",
            raw(provider="SAXO"))
    def test_synthetic_1h_in_4h_image_blocked(self):
        self.rejected("PROVIDER_INSTRUMENT_TF_OR_PRICE_SIDE_MISMATCH",raw(timeframe="1H"))
    def test_synthetic_wrong_fx_market_blocked(self):
        self.rejected("PROVIDER_INSTRUMENT_TF_OR_PRICE_SIDE_MISMATCH",replace(raw(),instrument="BTCUSDT"))
    def test_synthetic_unrecognized_price_side_blocked(self):
        self.rejected("PROVIDER_INSTRUMENT_TF_OR_PRICE_SIDE_MISMATCH",replace(raw(),pricing_component="LAST"))
    def test_synthetic_HTTP_endpoint_blocked(self):
        self.rejected("CANDLE_SOURCE_ENDPOINT_WRONG_PROVIDER",
            replace(raw(),original_provider_source_endpoint="http://api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles"))
    def test_synthetic_fake_remote_host_with_oanda_path_blocked(self):
        self.rejected("CANDLE_SOURCE_ENDPOINT_WRONG_PROVIDER",
            replace(raw(),original_provider_source_endpoint="https://attacker.example/oanda/replay"))
    def test_synthetic_wrong_vendor_hostname_blocked(self):
        self.rejected("CANDLE_SOURCE_ENDPOINT_WRONG_PROVIDER",
            replace(raw(),original_provider_source_endpoint="https://gateway.saxobank.com/openapi/chart/v3/charts"))
    def test_synthetic_missing_source_sha_blocked(self):
        self.rejected("NONCAUSAL_OR_UNTRACEABLE",replace(raw(),native_source_digest_sha256="bad"))
    def test_synthetic_missing_original_bar_id_blocked(self):
        self.rejected("NONCAUSAL_OR_UNTRACEABLE",replace(raw(),source_closed_bar_id=""))
    def test_synthetic_half_closed_bar_blocked(self):
        self.rejected("FORGED_AUTHOR_CHART_MATCH_OR_UNCLOSED_DATA",
            replace(raw(),fully_closed=False))
    def test_synthetic_author_golden_field_forged_blocked(self):
        self.rejected("FORGED_AUTHOR_CHART_MATCH_OR_UNCLOSED_DATA",
            replace(raw(),source_original_chart_match_author_verified=True))
    def test_synthetic_forged_real_order_blocked(self):
        self.rejected("FORGED_AUTHOR_CHART_MATCH_OR_UNCLOSED_DATA",
            replace(raw(),orders=("LIVE_BUY",)))
    def test_synthetic_noncontiguous_close_known_time_blocked(self):
        self.rejected("NONCAUSAL_OR_UNTRACEABLE",
            replace(raw(),closed_known_ms=raw().closed_known_ms-15*60*1000))
    def test_synthetic_nonquarterhour_bar_start_blocked(self):
        self.rejected("NONCAUSAL_OR_UNTRACEABLE",
            replace(raw(),start_ms=raw().start_ms+THREE_MINUTE()))
    def test_synthetic_bad_ohlc_order_blocked(self):
        self.rejected("MALFORMED_OR_FOREIGN_FX_OHLC",
            replace(raw(),low="1.09"))
    def test_synthetic_nondecimal_price_blocked(self):
        self.rejected("NONDECIMAL_FX_OHLC",replace(raw(),close="NaN"))
    def test_synthetic_negative_foreign_fx_price_blocked(self):
        self.rejected("MALFORMED_OR_FOREIGN_FX_OHLC",replace(raw(),open="-10"))
    def test_synthetic_no_future_image_bar_after_2024_publication(self):
        self.rejected("MARKET_BAR_KNOWN_AFTER_SCREENSHOT_PUBLICATION",
            raw(start=stamp("2026-10-24T09:00:00+00:00")))
    def test_synthetic_saxo_future_after_2025_published_blocked(self):
        self.rejected("MARKET_BAR_KNOWN_AFTER_SCREENSHOT_PUBLICATION",
            raw(provider="SAXO",start=stamp("2026-01-06T08:00:00+00:00")),
            ID_SAXO_4H)
    def test_true_fourhour_day_alignment_not_forced_utc_mod4h(self):
        x=self.gate(receipt=raw(start=stamp("2024-05-22T07:00:00+00:00")))
        self.assertEqual(x.source_attestation_state,STATES[1])
    def test_source_15m_nonhour_aligned_start_is_valid(self):
        x=self.gate(ID_OANDA_15M,raw(timeframe="15M",start=stamp("2024-05-22T12:15:00+00:00")))
        self.assertTrue(x.raw_source_receipt_present)
    def test_2024_OANDA_time_not_2023_certified_author(self):
        self.assertTrue(all(not x.actual_original_author_POI_or_VC_golden for x in self.review))
    def test_screenshot_ID_for_cropped_image_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_ONE_OF_EIGHT_ORIGINAL"):
            self.gate("1_f_EEaMnRuTmBCx7fcrryM0w2OSpvU7k")
    def test_fake_screenshot_candle_time_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_SOURCE_TIME"):
            assess_course_figure_original_fx_source(ID_OANDA_4H,
              proposed_screenshot_candle_time="2024-05-22T07:00:00Z")
    def test_fake_author_positive_claim_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_SOURCE_TIME"):
            assess_course_figure_original_fx_source(ID_OANDA_4H,
              proposed_raw_author_golden=True)
    def test_six_missing_goldens_documented(self):
        self.assertEqual(len(AUTHORS_GOLDENS_REQUIRED),6)
    def test_full_eight_source_gate_deterministic(self):
        self.assertEqual(review_all_eight_original_course_fx_sources(),self.review)
    def test_vendor_public_api_references_real_https(self):
        self.assertEqual(set(OFFICIAL_DOCUMENTATION),{"OANDA","SAXO"})
        self.assertTrue(all(x.startswith("https://") for x in OFFICIAL_DOCUMENTATION.values()))
    def test_synthetic_candle_receipt_cannot_be_dictionary(self):
        self.rejected("UNTRUSTED_RAW_FX_SOURCE_RECEIPT",{"provider":"OANDA"})
    def test_original_chart_date_is_still_unverified_even_with_receipt(self):
        x=self.gate(receipt=raw())
        self.assertFalse(x.screenshot_bar_timestamp_verified or x.independently_matched_chart_bar_ohlc)
    def test_zero_trade_goldens_at_all_eight_screenshot_source_gates(self):
        self.assertTrue(all(not x.author_entry_trade_ready for x in self.review))
def THREE_MINUTE():return 3*60*1000
if __name__=="__main__":unittest.main()
