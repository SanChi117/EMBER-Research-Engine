"""C106B: pre-price negative proofs for already-existing C105 4H parent event chain.
NO new SMC detectors; no imported third-party Pine algorithm, no strategy tuning.
"""
import hashlib,json,sys,unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c106_parent4h_semantic_transfer as r
import c105_parent4h_structural_geometry as geo
import c105_parent4h_native3m_source as src
import c104_native3m_source as strict
from c93_native3m_raid_bos_route_c_research import _confirmed
from c91_continuous_causal_route_a_paper import OHLC
from c90_structural_fta_backtest import Swing
from test_c105_parent4h_only_geometry import fixtures,parent,bar

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent/"evidence"/"c105"/r.SOURCE_BASELINE
def frozen_trades():
    return json.loads(EVIDENCE.read_text())["trades"]
class ExistingOnly(unittest.TestCase):
    def bad(self,fn,part):
        with self.assertRaisesRegex(r.C106Rejected,part):
            fn()
    def test_01_only_frozen_ten_new_tickers(self):
        self.assertEqual(len(set(r.SYMBOLS)),10)
    def test_02_unseen_symbols_not_old_three_groups(self):
        self.assertFalse(any(set(r.SYMBOLS)&x for x in r.PREVIOUS_GROUPS))
    def test_03_no_luxalgo_trade_detectors_added(self):
        txt=(HERE/"c106_parent4h_semantic_transfer.py").read_text()
        self.assertNotIn("request.security(",txt)
        self.assertNotIn("barmerge.lookahead_on",txt)
        self.assertNotIn("storeOrdeBlock(",txt)
    def test_04_C105_three_sources_byte_frozen(self):
        r.check_frozen()
    def test_05_old_25_source_provenance_sha_frozen(self):
        self.assertEqual(hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),r.A168_WITNESS_SHA)
        self.assertEqual(len(frozen_trades()),25)
    def test_06_original_trades_all_4h_parent(self):
        self.assertTrue(all(t["parent_tf"]==t["stop_source_tf"]==t["target_source_tf"]=="4H" for t in frozen_trades()))
    def test_07_original_trades_temporal_order(self):
        self.assertTrue(all(t["zone_created_ms"]<t["first_4h_poi_touch_ms"]<
            t["one_hour_rejection_close_ms"]<t["fifteen_minute_vc_close_ms"]==t["entry_ms"] for t in frozen_trades()))
    def test_08_no_4h_pivot_before_right2_confirm(self):
        # Same pre-existing _confirmed swing, no new detector.
        tf=geo.H4
        x=(bar(0,tf,h="101",l="95"),bar(tf,tf,h="105",l="96"),
           bar(2*tf,tf,h="100",l="97"),bar(3*tf,tf,h="99",l="98"),
           bar(4*tf,tf,h="101",l="95"))
        self.assertEqual(_confirmed(x,tf,3*tf),())
        self.assertEqual(_confirmed(x,tf,5*tf),())
    def test_09_4h_future_swing_hidden_in_parent_target(self):
        now,f,sw,rows,starts=fixtures()
        future=Swing(geo.H4,"HIGH",D("110"),now-geo.H4,now+geo.H4,2)
        plan,why=geo.parent_plan(parent(),now,D("100"),f,sw+(future,),rows,starts)
        self.assertEqual(why,"OK")
        self.assertEqual(plan["fta"],"120")
    def test_10_4h_fvg_known_on_closed_third(self):
        a,b,c=bar(0,geo.H4,h="100",l="95"),bar(geo.H4,geo.H4),bar(2*geo.H4,geo.H4,h="106",l="101",c="103")
        day=(bar(-2*geo.D1,geo.D1,c="99"),bar(-geo.D1,geo.D1,c="100"))
        week=(bar(-geo.W1,geo.W1,o="99",c="100"),)
        z,why=geo.zone_from_three((a,b,c),day,week)
        self.assertEqual((why,z.created_ms,z.lower,z.upper),("OK",3*geo.H4,D("100"),D("101")))
    def test_11_no_FVG_without_three_complete(self):
        self.assertRaises(geo.C105Rejected,geo.zone_from_three,(),(),())
    def test_12_1h_rejection_cannot_be_same_first_touch_bar(self):
        z=parent();z.state="WAIT_1H_REJECTION";z.first_touch_ms=8*geo.H
        h=bar(7*geo.H,geo.H,o="98",h="100",l="97",c="100")
        self.assertFalse(geo.rejection(z,h))
    def test_13_15m_confirmation_must_follow_one_hour_reaction(self):
        z=parent();z.state="WAIT_15M_VC";z.rejection_ms=4*geo.H
        series=tuple(bar(4*geo.H+(i-3)*geo.M15,geo.M15) for i in range(4))
        self.assertFalse(geo.vc(z,series))
    def test_14_structural_stop_cannot_be_3m_atr(self):
        now,f,sw,rows,starts=fixtures()
        plan,why=geo.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        self.assertEqual(plan["pad_source"],"ATR_FULLY_CLOSED_4H")
        self.assertEqual(plan["stop_source_tf"],"4H")
    def test_15_4h_tp_nonfixed_RR(self):
        now,f,sw,rows,starts=fixtures()
        plan,why=geo.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        self.assertEqual((plan["target"],plan["target_source_tf"]),("119.40","4H"))
    def test_16_source_loader_restores_old_tickers_after_error(self):
        old=src.SYMBOLS
        try:
            with self.assertRaises(RuntimeError):
                r.load_new_sources(fetch=lambda url:(_ for _ in ()).throw(RuntimeError("offline")))
        finally:
            self.assertEqual(src.SYMBOLS,old)
            self.assertEqual(strict.SYMBOLS,strict.SYMBOLS)
    def test_17_frozen_roundtrip_fees_all_three(self):
        self.assertEqual(geo.BPS,(14,25,40))
    def test_18_same_original_48h_timeout(self):
        self.assertEqual(geo.MAX_HOLD,960)
    def test_19_reject_foreign_1h_stop(self):
        t=dict(frozen_trades()[0]);t["stop_source_tf"]="1H"
        self.bad(lambda:r.audit_existing_trade(t,tuple()),"NOT_4H_PARENT")
    def test_20_reject_lower_15m_pad(self):
        t=dict(frozen_trades()[0]);t["pad_source"]="ATR_15M"
        self.bad(lambda:r.audit_existing_trade(t,tuple()),"LOWER_TF_EXIT_LEAK")
    def test_21_reject_event_backdating(self):
        t=dict(frozen_trades()[0]);t["one_hour_rejection_close_ms"]=t["first_4h_poi_touch_ms"]
        self.bad(lambda:r.audit_existing_trade(t,tuple()),"ASOF_EVENT_ORDER")
    def test_22_reject_unconfirmed_future_FTA(self):
        t=dict(frozen_trades()[0]);t["fta_confirmed_ms"]=t["entry_ms"]+geo.H4
        self.bad(lambda:r.audit_existing_trade(t,tuple()),"FUTURE_4H_FTA")
    def test_23_reject_3m_misaligned_time(self):
        t=dict(frozen_trades()[0]);t["fifteen_minute_vc_close_ms"]+=geo.THREE
        t["entry_ms"]+=geo.THREE
        self.bad(lambda:r.audit_existing_trade(t,tuple()),"WRONG_CLOSED_TIMEFRAME_ALIGNMENT")
    def test_24_reject_mixed_symbol_source(self):
        t=dict(frozen_trades()[0]);t["symbol"]="ALGOUSDT"
        self.bad(lambda:r.audit_existing_trade(t,(type("Fake",(),{"symbol":"CRVUSDT","start_ms":0})(),)),"UNRELATED_ORIGINAL_MARKET_SOURCE")
    def test_25_independent_source_replay_requires_all_320(self):
        self.bad(lambda:r.replay_unchanged({},[]),"NEW_10_ORIGINAL_320_ZIP_REQUIRED")
    def test_26_historic_screen_is_not_live_approval(self):
        z=json.loads(EVIDENCE.read_text())
        self.assertFalse(z["admission"]["live_approved"])
        self.assertFalse(z["admission"]["passes_historical_screen"])
if __name__=="__main__":unittest.main()
