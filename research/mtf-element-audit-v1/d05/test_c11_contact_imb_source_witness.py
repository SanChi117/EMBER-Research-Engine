"""B1/C11 falsification: price-confirmed wick contact + later 5m IMB != academic VC."""
from __future__ import annotations
from dataclasses import FrozenInstanceError,replace
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"mtf-course-v05"/"src"))
from test_c10_two_day_original_5m_context import make,T,DAY,PERIOD
from c11_contact_imb_source_witness import inspect_contact_then_5m_imb,StrongCandidateRejected

def proof(*, gap=True,raid=True,test=True,future=None):
    d0=make(0,pattern=raid)
    overrides={}
    if gap:
        overrides[26]=(96,97,95,96)  # after confirmed 1h short raid at 02:00 UTC
    if not test:
        overrides[27]=(95,96,94,95) # no contact with bearish 97..99 gap
    if future is not None:overrides[future]=(100,150,99,100)
    d1=make(1,pattern=raid,override=overrides)
    return d0,d1

def scan(first=None,second=None,at=T+DAY+28*PERIOD):
    a,b=proof()
    return inspect_contact_then_5m_imb(a if first is None else first,
                                       b if second is None else second,at)

class PriceContactImbC11Tests(unittest.TestCase):
    def test_valid_source_1h_raid_then_5m_imb_geometric_candidate(self):
        a=scan()
        self.assertGreaterEqual(a.raid_contact_candidates,1)
        self.assertGreaterEqual(a.post_raid_5m_imb_candidates,1)
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_witness_uses_original_zip_hash_and_exact_contact_row(self):
        a,b=proof()
        v=scan(a,b).paired_source_price_witnesses[0]
        self.assertEqual(v.source_symbol,"BTCUSDT")
        self.assertTrue(v.contact_source_5m_id.startswith(b.zip_sha256+":"))
        self.assertTrue(v.confirmation_source_5m_id.startswith(b.zip_sha256+":"))
        self.assertLess(v.contact_known_ms,v.confirmation_known_ms)
    def test_imbs_are_real_wick_gaps_not_volume_threshold(self):
        v=scan().paired_source_price_witnesses[0]
        self.assertEqual((v.poi_low,v.poi_high),(97,99))
        self.assertEqual(v.side,"SHORT")
    def test_later_zone_retest_is_after_third_5m_close(self):
        v=scan().paired_source_price_witnesses[0]
        self.assertIsNotNone(v.first_later_poi_test_known_ms)
        self.assertGreater(v.first_later_poi_test_known_ms,v.confirmation_known_ms)
    def test_immediately_after_imb_close_no_retrospective_touch(self):
        a,b=proof()
        result=inspect_contact_then_5m_imb(a,b,T+DAY+27*PERIOD)
        witness=result.paired_source_price_witnesses[0]
        self.assertIsNone(witness.first_later_poi_test_known_ms)
    def test_unvisited_poi_not_declared_tested(self):
        a,b=proof(test=False)
        res=inspect_contact_then_5m_imb(a,b,T+DAY+28*PERIOD)
        self.assertTrue(res.paired_source_price_witnesses)
        self.assertIsNone(res.paired_source_price_witnesses[0].first_later_poi_test_source_id)
    def test_wick_extreme_rebreach_before_imb_rejects_geometric_pair(self):
        a,b=proof()
        # Break the 1H raid wick extreme (112) in a closed 5m bar before
        # the 5m bearish gap is formed; no causal StrongHL candidate.
        from test_c10_two_day_original_5m_context import make
        broken=make(1,pattern=True,override={
            25:(100,115,99,100),
            26:(96,97,95,96),
        })
        result=inspect_contact_then_5m_imb(a,broken,T+DAY+28*PERIOD)
        self.assertEqual(result.post_raid_5m_imb_candidates,0)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")
    def test_imb_gap_missing_means_no_confirmation(self):
        a,b=proof(gap=False)
        q=inspect_contact_then_5m_imb(a,b,T+DAY+28*PERIOD)
        self.assertEqual(q.post_raid_5m_imb_candidates,0)
    def test_no_liquidity_contact_no_strong_candidate(self):
        a,b=proof(raid=False)
        q=inspect_contact_then_5m_imb(a,b,T+DAY+28*PERIOD)
        self.assertEqual(q.raid_contact_candidates,0)
        self.assertEqual(q.post_raid_5m_imb_candidates,0)
    def test_no_imb_confirmation_before_third_close(self):
        a,b=proof()
        q=inspect_contact_then_5m_imb(a,b,T+DAY+26*PERIOD)
        self.assertEqual(q.post_raid_5m_imb_candidates,0)
    def test_5m_imb_paired_only_at_its_close(self):
        a,b=proof()
        q=inspect_contact_then_5m_imb(a,b,T+DAY+27*PERIOD)
        self.assertGreaterEqual(q.post_raid_5m_imb_candidates,1)
        self.assertTrue(all(p.confirmation_known_ms<=q.as_of_ms for p in q.paired_source_price_witnesses))
    def test_future_suffix_cannot_change_historical_price_events(self):
        a,b=proof()
        _,other=proof(future=200)
        x=inspect_contact_then_5m_imb(a,b,T+DAY+28*PERIOD)
        y=inspect_contact_then_5m_imb(a,other,T+DAY+28*PERIOD)
        clean=lambda z:[(w.contact_1h_raid_uid,w.contact_known_ms,w.confirmation_5m_imb_uid,
                         w.confirmation_known_ms,w.poi_low,w.poi_high,w.first_later_poi_test_known_ms)
                        for w in z.paired_source_price_witnesses]
        self.assertEqual(clean(x),clean(y))
    def test_different_future_archive_sha_is_expected(self):
        a,b=proof()
        _,other=proof(future=200)
        self.assertNotEqual(b.zip_sha256,other.zip_sha256)
    def test_repeated_day_not_allowed(self):
        a,b=proof()
        with self.assertRaisesRegex(StrongCandidateRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_contact_then_5m_imb(b,b,T+DAY+28*PERIOD)
    def test_other_symbol_not_allowed(self):
        a,b=proof()
        with self.assertRaisesRegex(StrongCandidateRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_contact_then_5m_imb(make(0,symbol="ETHUSDT"),b,T+DAY+28*PERIOD)
    def test_missing_raw_member_rejected(self):
        a,b=proof()
        rows=list(b.rows)
        rows[3]=replace(rows[3],raw_id="fake")
        with self.assertRaisesRegex(StrongCandidateRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_contact_then_5m_imb(a,replace(b,rows=tuple(rows)),T+DAY+28*PERIOD)
    def test_incomplete_original_day_rejected(self):
        a,b=proof()
        with self.assertRaisesRegex(StrongCandidateRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_contact_then_5m_imb(a,replace(b,rows=b.rows[:287]),T+DAY+28*PERIOD)
    def test_bad_asof_future_cannot_claim_confirmation(self):
        a,b=proof()
        with self.assertRaisesRegex(StrongCandidateRejected,"INVALID_TWO_DAY_SOURCE_PREFIX"):
            inspect_contact_then_5m_imb(a,b,T+2*DAY+PERIOD)
    def test_candidate_cannot_be_mutated_into_author_certification(self):
        q=scan()
        v=q.paired_source_price_witnesses[0]
        with self.assertRaises(FrozenInstanceError):
            v.academic_status="APPROVED"
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
    def test_no_author_entry_or_trade_approval_is_returned(self):
        q=scan()
        self.assertEqual(q.academic_status,"NO_AUTHOR_GOLDEN_STRONGHL_OR_VC_APPROVAL")
        self.assertEqual(q.confirmation_definition,"3_CANDLE_WICK_GAP_NOT_EXCHANGE_VOLUME_SPIKE")
        self.assertEqual(q.readiness,"NOT_TRADE_READY")

if __name__=="__main__":
    unittest.main(verbosity=2)
