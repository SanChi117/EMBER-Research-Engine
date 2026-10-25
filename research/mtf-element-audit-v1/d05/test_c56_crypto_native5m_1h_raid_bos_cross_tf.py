"""C56 negative original CRYPTO native 5m and 3m same-raid comparisons."""
from dataclasses import replace
from decimal import Decimal as D
import unittest
from c20b_hourly_fractal_source_observer import HourFractal,FirstWickObservation
from c20b_five_minute_break_observer import FiveMinuteSwing,CloseBreakWitness
from c37_native_adapted_bos_event_scanner import AdaptedClosedBreak
from c56_crypto_native5m_1h_raid_bos_cross_tf import (
  validate_original_crypto_5m_break,compare_original_3m_5m_same_hourly_raid,
  c20_parent_key,c37_parent_key,HOUR,FIVE,TYPES,MISSING,BARRIERS)
O=1788220800000
B=O+5*HOUR
K=B+3*HOUR
THREE=180000
A="a"*64+":";F="b"*64+":"
def fiv():
    p=HourFractal("BSL",D("100"),O,O+2*HOUR,(F+str(O-HOUR),F+str(O),F+str(O+HOUR)))
    raid=FirstWickObservation(p,B,B+HOUR,B+2*HOUR,D("101"),"WICK_FRACTAL_GEOMETRY")
    swing=FiveMinuteSwing("LOW",D("99"),B+HOUR,B+HOUR+2*FIVE,
           (F+str(B+HOUR-FIVE),F+str(B+HOUR),F+str(B+HOUR+FIVE)))
    return CloseBreakWitness(p,raid,swing,"SHORT",K,K+FIVE,D("98"),F+str(K))
def thr(start=K):
    return AdaptedClosedBreak("LATEST_CONFIRMED_V1","BTCUSDT","BSL",
       O,B,B+2*HOUR,"100","101","SHORT",B+HOUR,B+HOUR+2*THREE,"99",
       A+str(B+HOUR),start,start+THREE,"98",A+str(start))
class C56IndependentSourceRaid5mVs3m(unittest.TestCase):
    def refuse(self,label,*,three=None,five=None,sym="BTCUSDT"):
        with self.assertRaisesRegex(ValueError,label):
            compare_original_3m_5m_same_hourly_raid(
                symbol=sym,e3=thr() if three is None else three,
                e5=fiv() if five is None else five)
    def test_valid_original_native5m_raid_source(self):
        self.assertTrue(validate_original_crypto_5m_break(fiv()))
    def test_original_native5m_and_native3m_different_raw_id_hashes(self):
        x=compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT",e3=thr(),e5=fiv())
        self.assertNotEqual(x.original_3m_bos_raw_id.split(":")[0],x.original_5m_bos_raw_id.split(":")[0])
    def test_3m_strictly_earlier_than_5m_closed(self):
        self.assertEqual(compare_original_3m_5m_same_hourly_raid(
            symbol="BTCUSDT",e3=thr(),e5=fiv()).source_status,TYPES[0])
    def test_5m_earlier_than_3m_closed(self):
        self.assertEqual(compare_original_3m_5m_same_hourly_raid(
            symbol="BTCUSDT",e3=thr(K+HOUR),e5=fiv()).source_status,TYPES[1])
    def test_original_3m_only_is_not_supposed_5m_trade(self):
        q=compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT",e3=thr())
        self.assertEqual(q.source_status,MISSING[0])
        self.assertIsNone(q.original_5m_bos_raw_id)
    def test_original_5m_only_is_not_supposed_3m_trade(self):
        q=compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT",e5=fiv())
        self.assertEqual(q.source_status,MISSING[1])
        self.assertIsNone(q.original_3m_bos_raw_id)
    def test_all_nontrade_research_blocks_present(self):
        q=compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT",e3=thr(),e5=fiv())
        self.assertEqual(q.blockers,BARRIERS)
        self.assertEqual((q.orders,q.trades,q.readiness),((),(),"NOT_TRADE_READY"))
    def test_no_author_approval(self):
        q=compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT",e3=thr(),e5=fiv())
        self.assertFalse(q.author_bos_approved or q.author_fill_approved)
    def test_same_exact_hourly_parent_keys(self):
        self.assertEqual(c20_parent_key(fiv()),c37_parent_key(thr()))
    def test_no_genuine_source_on_either_tf_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_BOTH"):
            compare_original_3m_5m_same_hourly_raid(symbol="BTCUSDT")
    def test_fx_or_unknown_crypto_market_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_CRYPTO"):
            compare_original_3m_5m_same_hourly_raid(symbol="EURUSD",e5=fiv())
    def test_duplicate_1h_parent_mismatch_rejected(self):
        bad=replace(thr(),raid_fractal_center_ms=O-HOUR)
        self.refuse("FALSE_PARENT_MATCH",three=bad)
    def test_wrong_3m_adapted_mode_rejected(self):
        bad=replace(thr(),hypothesis_id="EARLIEST_CONFIRMED_V1")
        self.refuse("NONBASELINE_OR_FOREIGN",three=bad)
    def test_wrong_symbol_from_source_3m_rejected(self):
        bad=replace(thr(),symbol="SOLUSDT")
        self.refuse("NONBASELINE_OR_FOREIGN",three=bad)
    def test_foreign_raw_5m_fake_type_rejected(self):
        self.refuse("UNTRUSTED_ORIGINAL5M",five={"start_ms":K})
    def test_wrong_original_5m_ID_rejected(self):
        self.refuse("BAD_ORIGINAL_NATIVE5M_SOURCE",five=replace(fiv(),source_row_id=F+str(K+FIVE)))
    def test_wrong_5m_bar_closed_known_ms_rejected(self):
        self.refuse("FUTURE_1H_RAID_5M",five=replace(fiv(),known_ms=K))
    def test_wrong_swings_sourced_after_break_start_rejected(self):
        f=fiv()
        self.refuse("FUTURE_1H_RAID_5M",five=replace(f,swing=replace(f.swing,known_ms=K+FIVE)))
    def test_5m_pivot_unknown_before_1h_wick_rejected(self):
        f=fiv()
        self.refuse("FUTURE_1H_RAID_5M",five=replace(f,raid_pivot=replace(f.raid_pivot,known_ms=B+HOUR),
            raid=replace(f.raid,fractal=replace(f.raid_pivot,known_ms=B+HOUR))))
    def test_1h_body_breach_cannot_be_wick_confirmed(self):
        f=fiv()
        self.refuse("FUTURE_1H_RAID_5M",five=replace(f,raid=replace(f.raid,verdict="FIRST_BREACH_BODY")))
    def test_1h_breach_without_right_closed_hour_rejected(self):
        f=fiv()
        self.refuse("FUTURE_1H_RAID_5M",five=replace(f,raid=replace(f.raid,confirmed_at_ms=B+HOUR)))
    def test_1h_breach_hour_known_ms_mismatch_rejected(self):
        f=fiv()
        self.refuse("FUTURE_1H_RAID_5M",five=replace(f,raid=replace(f.raid,first_breach_close_ms=B+FIVE)))
    def test_BSL_source_wick_is_strict_not_equal(self):
        f=fiv();self.refuse("RAID_SWING_BREAK_LEVELS",five=replace(f,raid=replace(f.raid,extreme=D("100"))))
    def test_5m_close_must_cross_strict_known_swing(self):
        f=fiv();self.refuse("RAID_SWING_BREAK_LEVELS",five=replace(f,close=D("99")))
    def test_original5m_ID_source_swing_center_must_be_exact(self):
        f=fiv();w=replace(f.swing,source_ids=(F+str(B+HOUR-FIVE),F+str(B+HOUR+FIVE),F+str(B+HOUR+2*FIVE)))
        self.refuse("BAD_ORIGINAL_NATIVE5M_SOURCE",five=replace(f,swing=w))
    def test_all_5_crypto_symbols_allowed_only_as_market_scope(self):
        for sym in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"):
            self.assertEqual(compare_original_3m_5m_same_hourly_raid(symbol=sym,e5=fiv()).symbol,sym)
if __name__=="__main__":unittest.main()
