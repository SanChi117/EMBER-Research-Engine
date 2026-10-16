"""B1/C09: independent price geometry witnesses, not author trade certification."""
from dataclasses import FrozenInstanceError,replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from course_primitives_v05 import Bar
from f03_5m_original_source import verify_original_5m
from c09_source_5m_raid_bos_geometry import inspect_source_raid_bos_5m,PriceRouteRejected

T=1790899200000
M=300000
URL="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2026-10-02.zip"
NAME="BTCUSDT-5m-2026-10-02.csv"
def bars(scenario=False,mod=None):
    rows=[]
    for i in range(288):
        o,h,l,c=100,101,99,100
        if scenario:
            if i==2*12+6:h=107
            if i==7*12+2:h=109
            if i==8*12+1:l=98
            if i==8*12+5:o,h,l,c=100,101,96,97
        if mod is not None and i in mod:
            o,h,l,c=mod[i]
        rows.append([str(T+i*M),str(o),str(h),str(l),str(c),"1",
                     str(T+(i+1)*M-1),"101","10","0.5","50","0"])
    fh=BytesIO()
    with zipfile.ZipFile(fh,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(NAME,"\n".join(",".join(row) for row in rows)+"\n")
    b=fh.getvalue()
    checksum=(sha256(b).hexdigest()+"  BTCUSDT-5m-2026-10-02.zip").encode()
    return verify_original_5m(URL,b,checksum)
def observe(p=None,at=T+24*3600000):
    return inspect_source_raid_bos_5m(bars(True) if p is None else p,at)
class Source5mRaidToBosGeometry(unittest.TestCase):
    def test_realistic_synthetic_1h_wick_raid_then_later_closed_5m_bos(self):
        q=observe()
        self.assertGreaterEqual(q.hourly_raid_candidates,1)
        self.assertGreaterEqual(q.five_minute_bos_candidates,1)
        self.assertGreater(q.bos_witnesses[0].bos_5m_known_at_ms,q.bos_witnesses[0].raid_1h_known_at_ms)
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
    def test_witness_has_source_row_pointer(self):
        q=observe()
        self.assertIn(str(8*12+5),str((q.bos_witnesses[0].breached_5m_close_bar_start-T)//M))
        self.assertTrue(q.bos_witnesses[0].original_5m_member_id.endswith(str(T+(8*12+5)*M)))
    def test_no_raid_in_featureless_contiguous_history(self):
        q=observe(bars())
        self.assertEqual(q.hourly_raid_candidates,0)
        self.assertEqual(q.five_minute_bos_candidates,0)
    def test_after_seven_hours_no_raid_source_exists_yet(self):
        q=observe(at=T+7*3600000)
        self.assertEqual(q.hourly_raid_candidates,0)
    def test_raid_only_known_when_one_hour_candle_closes(self):
        q=observe(at=T+8*3600000-300000)
        self.assertEqual(q.hourly_raid_candidates,0)
        q=observe(at=T+8*3600000)
        self.assertGreaterEqual(q.hourly_raid_candidates,1)
    def test_5m_bos_cannot_be_known_before_breach_candle_close(self):
        q=observe(at=T+8*3600000+5*300000)
        self.assertEqual(q.five_minute_bos_candidates,0)
        q=observe(at=T+8*3600000+6*300000)
        self.assertGreaterEqual(q.five_minute_bos_candidates,1)
    def test_false_hourly_raid_with_wick_but_close_above_pool(self):
        proof=bars(True,{7*12+11:(100,109,99,108)})
        q=observe(proof)
        self.assertEqual(q.hourly_raid_candidates,0)
        self.assertEqual(q.five_minute_bos_candidates,0)
    def test_wick_only_ltf_bos_not_accepted(self):
        p=bars(True,{8*12+5:(100,101,96,100)})
        self.assertEqual(observe(p).five_minute_bos_candidates,0)
    def test_breaking_raid_extreme_after_raid_invalidates_ltf_setup(self):
        p=bars(True,{8*12+3:(100,110,99,100)})
        self.assertEqual(observe(p).five_minute_bos_candidates,0)
    def test_no_hourly_bar_from_11_five_minute_candles(self):
        q=observe(at=T+11*M)
        self.assertEqual(q.hourly_closed_count,0)
    def test_hourly_bar_only_after_12_five_minute_candles(self):
        q=observe(at=T+12*M)
        self.assertEqual(q.hourly_closed_count,1)
    def test_past_prefix_immune_to_different_future_suffix(self):
        p=bars(True)
        changed=bars(True,{230:(100,150,99,100)})
        a=observe(p,at=T+9*3600000)
        b=observe(changed,at=T+9*3600000)
        self.assertEqual(a.hourly_raid_candidates,b.hourly_raid_candidates)
        # Source archive IDs differ when future suffix is mutated; that is\n        # correct provenance, not leaked future price logic. Compare the\n        # semantic event fields rather than distinct archive-root SHA pointers.\n        self.assertEqual(\n            [(v.raid_id,v.raid_1h_known_at_ms,v.bos_id,v.bos_5m_known_at_ms,v.breached_5m_close_bar_start) for v in a.bos_witnesses],\n            [(v.raid_id,v.raid_1h_known_at_ms,v.bos_id,v.bos_5m_known_at_ms,v.breached_5m_close_bar_start) for v in b.bos_witnesses])
    def test_asof_after_archive_cannot_claim_future_event(self):
        with self.assertRaisesRegex(PriceRouteRejected,"AS_OF_NOT_CLOSED_WITHIN_5M_ARCHIVE"):
            observe(at=T+24*3600000+M)
    def test_asof_unclosed_five_minute_rejected(self):
        with self.assertRaisesRegex(PriceRouteRejected,"AS_OF_NOT_CLOSED_WITHIN_5M_ARCHIVE"):
            observe(at=T+8*3600000+1)
    def test_missing_one_5m_bar_rejected(self):
        p=bars(True)
        broken=list(p.rows)
        broken[3]=replace(broken[3],bar=Bar(T+4*M,T+5*M,100,101,99,100,"5m"))
        q=replace(p,rows=tuple(broken))
        with self.assertRaisesRegex(PriceRouteRejected,"NONCONTIGUOUS_OR_UNIDENTIFIED_5M_PROVENANCE"):
            observe(q)
    def test_unverified_not_complete_original_5m_proof_rejected(self):
        p=bars(True)
        with self.assertRaisesRegex(PriceRouteRejected,"NOT_A_FULL_ORIGINAL_5M_SOURCE_PROOF"):
            observe(replace(p,rows=p.rows[:100]))
    def test_no_stronghl_without_authored_vc_evidence(self):
        q=observe()
        self.assertEqual(q.stronghl_status,"NO_INDEPENDENT_STRONG_HL_VC_CERTIFICATE")
        self.assertIn("UNAPPROVED",q.academic_semantics)
    def test_frozen_result_not_mutable_into_academic_trade(self):
        q=observe()
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
if __name__=="__main__":
    unittest.main(verbosity=2)
