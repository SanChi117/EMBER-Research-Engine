"""C72 native5m independently source 3:1 as-of and no fake VC."""
import io,zipfile,hashlib,unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import SEPT_START,END,DAY,NativeKline
from c21_native3m_source_bridge import PERIODS,STARTS
from c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import PostContactSourceGate
from c72_original_native5m_source_vc_after15m_gate import (
    FIVE,Q,Original5m,Original5mArchive,Original5mReview,Source5mEvent,
    original5m_url,parse_original5m_zip,reconcile_original5m_to_native15m,
    scan_original5m_source_events,first_any_5m_after_provisional15m,
    C72Rejected,STATES,K_IMB,K_SNR_LIQ,K_SNR_IMB)
SHA="a"*64
def row(i,op="100",hi="101",lo="99",cl="100",v="1",sha=SHA):
    t=SEPT_START+i*FIVE
    return Original5m("BTCUSDT",t,t+FIVE,D(op),D(hi),D(lo),D(cl),
                       D(v),sha,sha+":"+str(t))
def source(cut=SEPT_START+18*FIVE):
    bars=[row(i) for i in range((cut-SEPT_START)//FIVE)]
    return Original5mReview("BTCUSDT",cut,tuple(bars),(SHA,),0)
def gate(known=SEPT_START+Q,state="FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED",
         branch="NEW_1H_VC_POI",side="LONG"):
    return PostContactSourceGate("BTCUSDT",side,branch,None,None,None,
        SEPT_START,known,("15M_CLASSIC_IMB_SOURCE_ONLY",),("LONG",),
        state,END,True,True)
def fake5(kind=K_IMB,side="LONG",start=SEPT_START+Q,sha=SHA):
    known=start+3*FIVE
    return Source5mEvent(kind,side,start,known,sha+":"+str(start),
                         sha+":"+str(start+2*FIVE),"SOURCE_ONLY")
class C72Source5m(unittest.TestCase):
    def test_01_native5m_url_exact_locked_readonly(self):
        self.assertEqual(original5m_url("BTCUSDT","2026-09"),
          "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-2026-09.zip")
    def test_02_unknown_market_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"MARKET"):original5m_url("FAKE","2026-09")
    def test_03_future_period_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"PERIOD"):original5m_url("BTCUSDT","2026-11")
    def test_04_no_owner_vc_automatically_from_immediate_5m_gap(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
                                              (fake5(),))
        self.assertEqual(x.state,"FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC")
        self.assertFalse(x.author_5m_vc or x.author_structural_sl)
        self.assertFalse(x.author_valid_first_1h_poi_test or x.author_15m_trigger)
    def test_05_snr_after15m_source_only_not_author(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
                                             (fake5(K_SNR_LIQ),))
        self.assertEqual(x.state,"FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC")
    def test_06_late_favorable_cannot_override_first_opposite(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
          (fake5(side="SHORT"),fake5(start=SEPT_START+2*Q)))
        self.assertEqual(x.state,"FIRST_5M_SOURCE_OPPOSITE_SIDE")
    def test_07_two_sides_first_same_close_ambiguous(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
          (fake5(),fake5(side="SHORT")))
        self.assertEqual(x.state,"FIRST_5M_SOURCE_TWO_SIDES_AMBIGUOUS")
    def test_08_two_kinds_first_same_close_ambiguous(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
          (fake5(),fake5(K_SNR_IMB)))
        self.assertEqual(x.state,"FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS")
    def test_09_5m_pattern_begun_before_closed15m_cannot_be_vc(self):
        x=first_any_5m_after_provisional15m(gate(),source(),
          (fake5(start=SEPT_START),))
        self.assertEqual(x.state,"NO_5M_VC_SOURCE_RIGHT_CENSORED")
    def test_10_missing_5m_after_candidate_source_right_censored(self):
        self.assertEqual(first_any_5m_after_provisional15m(
          gate(),source(),()).state,"NO_5M_VC_SOURCE_RIGHT_CENSORED")
    def test_11_full_24h_no_candidates_not_hallucinated(self):
        c=source(cut=SEPT_START+25*3600000)
        self.assertEqual(first_any_5m_after_provisional15m(
          gate(),c,()).state,"NO_5M_VC_SOURCE_FULL_24H_WINDOW")
    def test_12_no_c71_provisional_new_poi_branch_cannot_go_5m(self):
        x=first_any_5m_after_provisional15m(
          gate(branch="TRIGGER"),source(),(fake5(),))
        self.assertEqual(x.state,"NO_C71_SINGLE_NEW_1H_POI_15M_SOURCE")
    def test_13_ambiguous_previous15m_source_refuses_5m_promotion(self):
        x=first_any_5m_after_provisional15m(
          gate(state="FIRST_ANY_SOURCE_OPPOSITE_DIRECTION"),source(),(fake5(),))
        self.assertEqual(x.state,"NO_C71_SINGLE_NEW_1H_POI_15M_SOURCE")
    def test_14_forged_owner_1h_first_valid_poi_test_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                replace(gate(),author_1h_poi_valid_test=True),source(),(fake5(),))
    def test_15_forged_owner15m_trigger_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                replace(gate(),author_15m_trigger=True),source(),(fake5(),))
    def test_16_fake_orders_prior_C71_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                replace(gate(),orders=("BUY",)),source(),(fake5(),))
    def test_17_routeB_IDM_injection_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                replace(gate(),route_b_idm_approved=True),source(),(fake5(),))
    def test_18_routeC_raid_bos_injection_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                replace(gate(),route_c_raid_bos_approved=True),source(),(fake5(),))
    def test_19_fake_source5m_SHA_ID_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FORGED"):
            first_any_5m_after_provisional15m(
                gate(),source(),(replace(fake5(),first_bar_id="WRONG"),))
    def test_20_fake_source5m_author_vc_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FORGED"):
            first_any_5m_after_provisional15m(
                gate(),source(),(replace(fake5(),author_volume_confirmation=True),))
    def test_21_future_source_event_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FORGED"):
            first_any_5m_after_provisional15m(
                gate(),source(),(fake5(start=SEPT_START+25*3600000),))
    def test_22_source_5m_gap_requires_3_wicks_not_2_bodies(self):
        c=source()
        self.assertEqual(scan_original5m_source_events(c),())
    def test_23_source_5m_classic_three_wick_gap_requires_full_third_close(self):
        c=source()
        bars=list(c.rows)
        bars[3]=row(3,hi="101",lo="99")
        bars[4]=row(4,hi="107",lo="100",cl="106")
        bars[5]=row(5,op="108",hi="110",lo="107",cl="109")
        c=replace(c,rows=tuple(bars))
        e=scan_original5m_source_events(c)
        self.assertTrue(any(x.kind==K_IMB and x.pattern_start_ms==SEPT_START+3*FIVE
                            and x.known_ms==SEPT_START+6*FIVE for x in e))
    def test_24_bad_provenance_original5m_raw_source_rejected(self):
        c=source()
        rows=list(c.rows);rows[0]=replace(rows[0],raw_id="FAKE")
        with self.assertRaisesRegex(C72Rejected,"UNTRUSTED"):
            scan_original5m_source_events(replace(c,rows=tuple(rows)))
    def test_25_wrong_source_symbol_rejected(self):
        with self.assertRaisesRegex(C72Rejected,"FAKE_OWNER"):
            first_any_5m_after_provisional15m(
                gate(),replace(source(),symbol="ETHUSDT"),(fake5(),))
    def test_26_no_default_trades_or_5m_vc(self):
        x=first_any_5m_after_provisional15m(gate(),source(),(fake5(),))
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_27_source_replay_cut_only_closed5m_events(self):
        c=source()
        z=fake5(start=SEPT_START+16*FIVE)
        self.assertGreater(z.known_ms,c.as_of_ms)
        with self.assertRaisesRegex(C72Rejected,"FORGED"):
            first_any_5m_after_provisional15m(gate(),c,(z,))
    def test_28_15m_candidate_close_must_be_aligned_and_past(self):
        with self.assertRaisesRegex(C72Rejected,"BAD_15M"):
            first_any_5m_after_provisional15m(
                gate(known=SEPT_START+Q+FIVE),source(),(fake5(),))
    def test_29_orig_archive_missing_full_month_rejected(self):
        a=Original5mArchive("BTCUSDT","2026-09",SHA,SHA,
                            original5m_url("BTCUSDT","2026-09"),(row(0),))
        with self.assertRaisesRegex(C72Rejected,"WRONG_5M"):
            reconcile_original5m_to_native15m((a,a,a),(),as_of_ms=END)
    def test_30_parse_bad_checksum_reject(self):
        with self.assertRaisesRegex(C72Rejected,"INVALID_CHECKSUM"):
            parse_original5m_zip("BTCUSDT","2026-09",b"BAD",b"not_checksum")
if __name__=="__main__":unittest.main()
