"""C54 crypto-only target with original 4H Binance raw3m lineage, 8 C45 academic routes."""
import unittest
from dataclasses import replace
from c54_crypto_only_course_logic_source_bridge import (
 CryptoTechnicalParent,ROUTE_MAP,TARGET,ILLUSTRATION_ROLE,
 overlay_crypto_course_routes,validate_original_crypto_parent,
 original_c45_route_semantic_probe,SOURCE_MISSING,THREE,HOUR)
from c45_recovered_course_text_contract import TEXT_ROUTE_MODES
BASE=1788321600000
PREFIX="a"*64+":"
def parent(*,touch=True,later=True,symbol="BTCUSDT"):
    return CryptoTechnicalParent(symbol,BASE+200*HOUR,"LONG",
        tuple(PREFIX+str(BASE+i*4*HOUR) for i in range(3)),
        BASE+12*HOUR,PREFIX+str(BASE+13*HOUR) if touch else None,
        BASE+13*HOUR+THREE if touch else None,
        PREFIX+str(BASE+14*HOUR) if later else None,
        BASE+17*HOUR if later else None)
class CryptoOnlyLogicalCourseSource(unittest.TestCase):
    def fail(self,part,source=None,**args):
        with self.assertRaisesRegex(ValueError,part):
            overlay_crypto_course_routes(source if source is not None else parent(),**args)
    def test_course_target_crypto_binance_original_source_only(self):
        self.assertEqual(TARGET,"CRYPTO_BINANCE_USDM_ORIGINAL_CLOSED_OHLC_ONLY")
    def test_explicit_fx_images_are_not_source(self):
        self.fail("COURSE_IMAGES_ARE_LOGIC_NOT_SOURCE_CANDLES",illustration="EURUSD_OANDA")
    def test_original_all_eight_c45_routes_retained(self):
        self.assertEqual(len(original_c45_route_semantic_probe()),8)
    def test_all_academic_modes_equal_C45_contract(self):
        self.assertEqual(set(ROUTE_MAP),set(TEXT_ROUTE_MODES))
    def test_A_four_route_variants_separate(self):
        self.assertEqual(sum(k.startswith("A_") for k in ROUTE_MAP),4)
    def test_B_two_route_variants_separate(self):
        self.assertEqual(sum(k.startswith("B_") for k in ROUTE_MAP),2)
    def test_C_two_route_variants_separate(self):
        self.assertEqual(sum(k.startswith("C_") for k in ROUTE_MAP),2)
    def test_all_eight_paper_route_overlays(self):
        self.assertEqual(len(overlay_crypto_course_routes(parent())),8)
    def test_all_eight_show_academic_semantics_missing(self):
        x=overlay_crypto_course_routes(parent())
        self.assertTrue(all(z.academic_semantic_requirements_missing==SOURCE_MISSING for z in x))
    def test_historical_crypto_data_not_author_PoI_by_default(self):
        self.assertTrue(all(not z.academic_PoI_VC_entry_confirmed for z in overlay_crypto_course_routes(parent())))
    def test_all_order_trade_outputs_zero(self):
        self.assertTrue(all(z.orders==z.trades==() for z in overlay_crypto_course_routes(parent())))
    def test_never_go_live_or_be_trade_ready(self):
        self.assertTrue(all(z.readiness=="NOT_TRADE_READY" for z in overlay_crypto_course_routes(parent())))
    def test_course_4H_1H_15M_route_shape_exact(self):
        x=overlay_crypto_course_routes(parent(),mode="A_4H_TRIGGER_15M_VC")[0]
        self.assertEqual(x.academic_timeframe_sequence,("4H","1H","15M","15M","4H"))
    def test_no_1H_trigger_context_route_independent(self):
        x=overlay_crypto_course_routes(parent(),mode="A_4H_NO_TRIGGER_1H_VC")[0]
        self.assertIsNone(x.academic_timeframe_sequence[1])
    def test_onehour_parent_15m_to5m_figure_is_logic(self):
        x=overlay_crypto_course_routes(parent(),mode="A_1H_TRIGGER_5M_VC")[0]
        self.assertEqual(x.academic_timeframe_sequence,("1H","15M","5M","5M","1H"))
        self.assertEqual(x.course_illustration_role,ILLUSTRATION_ROLE)
    def test_separate_idm_route_not_inferred_from_imb(self):
        x=overlay_crypto_course_routes(parent(),mode="B_4H_VC_1H_IDM")[0]
        self.assertEqual(x.route_family,"B_IDM")
        self.assertFalse(x.academic_PoI_VC_entry_confirmed)
    def test_separate_raid_route_not_inferred_from_imb(self):
        x=overlay_crypto_course_routes(parent(),mode="C_1H_RAID_3M_BOS")[0]
        self.assertEqual(x.route_family,"C_RAID_TO_BOS")
        self.assertFalse(x.academic_PoI_VC_entry_confirmed)
    def test_all_route_variants_have_paper_state(self):
        self.assertTrue(all(x.final_state=="TECHNICAL_1H_IMB_AFTER_TOUCH_ONLY"
                    for x in overlay_crypto_course_routes(parent())))
    def test_no_original_3m_touch_does_not_make_trade(self):
        a=overlay_crypto_course_routes(parent(touch=False,later=False))[0]
        self.assertEqual(a.final_state,"TECHNICAL_FIRST_TOUCH_UNKNOWN")
        self.assertFalse(a.observed_first_native3m_touch)
    def test_touch_without_later_1h_is_not_vc(self):
        a=overlay_crypto_course_routes(parent(later=False))[0]
        self.assertEqual(a.final_state,"TECHNICAL_FIRST_TOUCH_WITHOUT_1H_SOURCE")
        self.assertFalse(a.observed_later_fully_closed_1h_technical_imb)
    def test_original_parent_known_before_first_touch(self):
        self.assertTrue(overlay_crypto_course_routes(parent())[0].known_parent_before_first_touch)
    def test_original_1h_technical_not_promoted_as_vc(self):
        self.assertTrue(all(x.later_1h_source_is_not_automatic_vc for x in overlay_crypto_course_routes(parent())))
    def test_source_5_markets_are_only_actual_binance_fixture_universe(self):
        for name in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"):
            validate_original_crypto_parent(replace(parent(),symbol=name))
    def test_forex_symbol_cannot_be_target_market(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),symbol="EURUSD"))
    def test_synthetic_usdt_not_in_frozen_45zip_universe_rejected(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),symbol="INJUSDT"))
    def test_forged_real_academic_typed_POI_refused(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),author_poi_verified=True))
    def test_forged_first_valid_academic_test_refused(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),academic_first_test_verified=True))
    def test_forged_1h_academic_vc_refused(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),academic_volume_confirmation_verified=True))
    def test_forged_order_refused(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),orders=("BUY",)))
    def test_fake_trade_ready_refused(self):
        self.fail("FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC",replace(parent(),readiness="TRADE_READY"))
    def test_unknown_academic_route_refused(self):
        self.fail("UNKNOWN_ROUTE_NOT_IN_ACADEMY",mode="D_FX_OANDA_PRICE_COPY")
    def test_plain_dict_without_evidence_type_refused(self):
        self.fail("UNTRUSTED_CRYPTO_TECHNICAL_SOURCE",{"symbol":"BTCUSDT"})
    def test_three_4h_candles_required(self):
        self.fail("THREE_ORIGINAL_4H_CANDLES_REQUIRED",
            replace(parent(),original_4h_source3m_ids=(PREFIX+str(BASE),)))
    def test_4h_complete_knowledge_from_three_candles(self):
        self.fail("NONCAUSAL_OR_MIXED_4H_CRYPTO_SOURCE",
            replace(parent(),original_4h_known_ms=BASE+8*HOUR))
    def test_nonconsecutive_original4h_rejected(self):
        q=parent();self.fail("NONCAUSAL_OR_MIXED_4H_CRYPTO_SOURCE",
            replace(q,original_4h_source3m_ids=(q.original_4h_source3m_ids[0],
              q.original_4h_source3m_ids[1],PREFIX+str(BASE+9*HOUR))))
    def test_mixed_original_native_zip_id_rejected(self):
        q=parent();self.fail("NONCAUSAL_OR_MIXED_4H_CRYPTO_SOURCE",
            replace(q,original_4h_source3m_ids=(
              q.original_4h_source3m_ids[0],q.original_4h_source3m_ids[1],
              "b"*64+":"+str(BASE+8*HOUR))))
    def test_future_original4h_parent_unavailable_rejected(self):
        self.fail("NONCAUSAL_OR_MIXED_4H_CRYPTO_SOURCE",
            replace(parent(),source_as_of_ms=BASE+11*HOUR))
    def test_bad_original3m_raw_source_id_rejected(self):
        q=parent();self.fail("FORGED_NONCRYPTO_NATIVE_SOURCE_ID",
            replace(q,first_original3m_touch_id="EUR_USD_OANDA_1h"))
    def test_touch_bar_closed_ms_exact(self):
        q=parent();self.fail("CRYPTO_FIRST_TOUCH_PRE_PARENT_OR_FUTURE",
            replace(q,first_original3m_touch_known_ms=q.first_original3m_touch_known_ms+THREE))
    def test_first_touch_cannot_predate_parent_known(self):
        q=parent();self.fail("CRYPTO_FIRST_TOUCH_PRE_PARENT_OR_FUTURE",
            replace(q,first_original3m_touch_id=PREFIX+str(BASE+11*HOUR),
                first_original3m_touch_known_ms=BASE+11*HOUR+THREE))
    def test_touch_missing_id_but_has_close_time_rejected(self):
        q=parent();self.fail("TOUCH_BAR_ID_KNOWN_AT_MISMATCH",
            replace(q,first_original3m_touch_id=None))
    def test_later1h_cannot_exist_with_no_touch(self):
        q=parent(touch=False,later=False);self.fail("TECHNICAL_1H_VC_FUTURE_OR_ORPHAN",
            replace(q,first_later_1h_technical_imb_source3m_id=PREFIX+str(BASE+14*HOUR),
                first_later_1h_technical_imb_known_ms=BASE+17*HOUR))
    def test_later1h_must_be_closed_after_1h_3_candles(self):
        q=parent();self.fail("TECHNICAL_1H_VC_FUTURE_OR_ORPHAN",
            replace(q,first_later_1h_technical_imb_known_ms=BASE+15*HOUR))
    def test_later1h_future_after_asof_rejected(self):
        q=parent();self.fail("TECHNICAL_1H_VC_FUTURE_OR_ORPHAN",
            replace(q,source_as_of_ms=BASE+16*HOUR))
    def test_later1h_must_have_exact_native_source_ID(self):
        q=parent();self.fail("FORGED_NONCRYPTO_NATIVE_SOURCE_ID",
            replace(q,first_later_1h_technical_imb_source3m_id="fake-id"))
    def test_later1h_missing_timestamp_rejected(self):
        q=parent();self.fail("LATER_1H_CANDLE_ID_KNOWN_AT_MISMATCH",
            replace(q,first_later_1h_technical_imb_known_ms=None))
    def test_later1h_source_row_start_after_first_touch_end(self):
        q=parent();self.fail("TECHNICAL_1H_VC_FUTURE_OR_ORPHAN",
            replace(q,first_later_1h_technical_imb_source3m_id=PREFIX+str(BASE+12*HOUR),
                first_later_1h_technical_imb_known_ms=BASE+15*HOUR))
    def test_all_overlays_keep_frozen_original_source_candle_IDS(self):
        q=parent();self.assertTrue(all(x.original_4h_raw3m_ids==q.original_4h_source3m_ids
                               for x in overlay_crypto_course_routes(q)))
    def test_no_original_academic_card_can_overwrite_crypto_market(self):
        q=parent();self.fail("COURSE_IMAGES_ARE_LOGIC_NOT_SOURCE_CANDLES",q,
            illustration={"image_id":"1obj4bBVqplvrL2E_iNHXOHoOaDhj5gKx","source_symbol":"EURUSD"})
if __name__=="__main__":unittest.main()
