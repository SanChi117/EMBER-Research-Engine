"""C115 frozen price-source negative controls. NO derived backtest successes."""
import unittest
from unittest.mock import patch
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace as NS
import c115_4h_poi_native5m_price_only_blind_replay as c115
from c89_original_native5m_adaptation_backtest import Bar

def synthetic():
    a=tuple(NS(start_ms=i*180000,known_ms=(i+1)*180000,open=D(100),
               high=D(101),low=D(99),close=D(100),volume=D(3)) for i in range(5))
    b=tuple(Bar(j*300000,D(100),D(101),D(99),D(100),D(5)) for j in range(3))
    return a,b

class C115PriceOnlyContracts(unittest.TestCase):
    def test_original_c114_hypothesis_sha_frozen(self):
        self.assertTrue(c115.frozen())
    def test_windows_are_two_new_2023_56day_periods(self):
        self.assertEqual(len(c115.WINDOWS),2)
        self.assertEqual(c115.WINDOWS[0][1].strftime("%Y-%m-%d"),"2023-09-01")
        self.assertEqual(c115.WINDOWS[1][1].strftime("%Y-%m-%d"),"2023-11-01")
        self.assertTrue(all((end-begin).days==56 for _,begin,end in c115.WINDOWS))
    def test_exact_3m5m_15m_ohlc_required(self):
        a,b=synthetic()
        p=c115.price_only_causal_15m_parity(a,b)
        self.assertEqual(p["aligned15m"],1)
        self.assertTrue(p["strict_ohlc_price_clock_parity"])
        self.assertEqual(p["volume_mismatch_15m_bucket_count"],0)
    def test_volume_mismatch_reported_not_a_signal_or_gate(self):
        a,b=synthetic()
        b=list(b);b[1]=replace(b[1],volume=D(500))
        p=c115.price_only_causal_15m_parity(a,tuple(b))
        self.assertEqual(p["volume_mismatch_15m_bucket_count"],1)
        self.assertFalse(p["volume_is_signal"])
        self.assertFalse(p["volume_is_source_gate"])
        self.assertEqual(len(p["volume_discrepancy_samples"]),1)
    def test_true_ohlc_disagreement_always_blocks(self):
        a,b=synthetic();b=list(b);b[1]=replace(b[1],h=D(102))
        with self.assertRaisesRegex(c115.C115Rejected,"STRICT_15M_OHLC"):
            c115.price_only_causal_15m_parity(a,tuple(b))
    def test_clock_gaps_cannot_be_hidden_with_same_ohlc(self):
        a,b=synthetic();a=list(a)
        a[2].start_ms+=60000
        with self.assertRaisesRegex(c115.C115Rejected,"NATIVE_3M_INTRA_BUCKET_GAP"):
            c115.price_only_causal_15m_parity(tuple(a),b)
    def test_missing_native_5m_rejected(self):
        a,b=synthetic()
        with self.assertRaises(c115.C115Rejected):
            c115.price_only_causal_15m_parity(a,b[:2])
    def test_scoped_source_only_replacement_restores_original_engine(self):
        original=c115.original
        prev_windows,prev_parity,prev_precommit=original.WINDOWS,original.independent_15m_parity,original.PRECOMMIT
        with c115.frozen_source_scope():
            self.assertEqual(original.WINDOWS,c115.WINDOWS)
            self.assertIs(original.independent_15m_parity,c115.price_only_causal_15m_parity)
        self.assertEqual(original.WINDOWS,prev_windows)
        self.assertIs(original.independent_15m_parity,prev_parity)
        self.assertEqual(original.PRECOMMIT,prev_precommit)
    def test_event_trade_attribution_bridge_only_adds_metadata(self):
        original_trade={"entry":"100","stop":"90","target":"120","net_r":1.4,
                        "entry_ms":10,"exit_ms":30}
        event={"symbol":"BNBUSDT","parent_id":"4H-CLOSED","trade":original_trade}
        with patch.object(c115,"_ORIGINAL_PER_SYMBOL",return_value={"events":[event]}) as mock:
            z=c115.pure_trade_provenance_bridge((),(),"BNBUSDT",c115.WINDOWS[0])
        self.assertEqual(z["events"][0]["trade"]["symbol"],"BNBUSDT")
        self.assertEqual(z["events"][0]["trade"]["parent_id"],"4H-CLOSED")
        self.assertEqual({k:z["events"][0]["trade"][k] for k in
                          ("entry","stop","target","net_r","entry_ms","exit_ms")},
                         {"entry":"100","stop":"90","target":"120",
                          "net_r":1.4,"entry_ms":10,"exit_ms":30})
    def test_event_trade_attribution_bridge_rejects_symbol_conflict(self):
        z={"events":[{"symbol":"BNBUSDT","parent_id":"4H","trade":
                      {"symbol":"BTCUSDT","entry":"100","net_r":0}}]}
        with patch.object(c115,"_ORIGINAL_PER_SYMBOL",return_value=z):
            with self.assertRaises(c115.C115Rejected):
                c115.pure_trade_provenance_bridge((),(),"BNBUSDT",c115.WINDOWS[0])
    def test_all_original_economic_parameters_untouched(self):
        x=c115.original
        self.assertEqual(x.BPS,(14,25,40))
        self.assertEqual(x.REPS,2000)
        self.assertEqual(x.BOOT_SEED,11420261030)
        self.assertEqual(x.LANDMARK,6*x.H)
        self.assertEqual(c115.EXPECTED_ZIPS,2688)
if __name__=="__main__":unittest.main()
