"""Synthetic-only negative closed-candle tests for C20B research geometry."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c20_original_32day_native5m_lineage import C20NativeSourceLineage,NativeFiveMinute,FIVE,SEPT_START
from c20b_hourly_fractal_source_observer import closed_hourly,observe_fractals_and_first_breach
from c20b_five_minute_break_observer import cross_timeframe_raid_break
ONE=3600000
SHA="a"*64
def synthetic(size=120,body=False,invalid=False):
    source=[]
    for i in range(size):
        o,h,l,c=D(100),D(102),D(98),D(100)
        if i==18:h=D(110)
        if i==66:h=D(111)
        if i==71 and body:o,h,l,c=D(100),D(112),D(99),D(112)
        if i==81:l=D(96)
        if i==84:o,h,l,c=D(100),D(101),D(94),D(95)
        if i==84 and invalid:h=D(113)
        at=SEPT_START+i*FIVE
        source.append(NativeFiveMinute("BTCUSDT",at,at+FIVE,o,h,l,c,D(1),SHA+":"+str(at),SHA))
    return C20NativeSourceLineage("BTCUSDT",SEPT_START+size*FIVE,
        tuple(source),(SHA,"b"*64,"c"*64),3072,32)

class C20BGeometry(unittest.TestCase):
    def test_1h_source_buckets_and_pivot_confirmation(self):
        line=synthetic()
        hour=closed_hourly(line,line.as_of_ms)
        self.assertEqual(len(hour),10)
        self.assertEqual(len(hour[0].native_rows),12)
        p,r=observe_fractals_and_first_breach(hour)
        target=[x for x in r if x.fractal.center_ms==SEPT_START+ONE and x.fractal.kind=="BSL"]
        self.assertEqual(len(target),1)
        self.assertEqual(target[0].fractal.known_ms,SEPT_START+3*ONE)
        self.assertEqual(target[0].confirmed_at_ms,SEPT_START+7*ONE)
        self.assertEqual(target[0].verdict,"WICK_FRACTAL_GEOMETRY")
    def test_closure_only_5m_candidate_and_spatial_direction(self):
        line=synthetic()
        g=cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
        candidates=[x for x in g.potential_bos_witnesses
                    if x.raid.fractal.center_ms==SEPT_START+ONE]
        self.assertTrue(candidates)
        w=candidates[0]
        self.assertEqual(w.side,"SHORT")
        self.assertEqual(w.start_ms,SEPT_START+7*ONE)
        self.assertEqual(w.known_ms,SEPT_START+7*ONE+FIVE)
        self.assertLess(w.swing.level,w.raid.fractal.level)
        self.assertLess(w.close,w.swing.level)
        self.assertEqual(g.author_approved_bos,0)
        self.assertEqual(g.author_approved_trades,0)
    def test_pre_close_does_not_see_future_5m_bos(self):
        line=synthetic()
        earlier=cross_timeframe_raid_break(line,as_of_ms=SEPT_START+7*ONE)
        after=cross_timeframe_raid_break(line,as_of_ms=SEPT_START+7*ONE+FIVE)
        self.assertEqual(earlier.potential_bos_witnesses,())
        self.assertTrue(after.potential_bos_witnesses)
    def test_body_sweep_not_clean_wick_raid(self):
        line=synthetic(body=True)
        g=cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
        self.assertFalse(any(x.raid.fractal.center_ms==SEPT_START+ONE for x in g.potential_bos_witnesses))
    def test_break_candle_above_wick_extreme_invalidates(self):
        line=synthetic(invalid=True)
        g=cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
        self.assertFalse(any(x.raid.fractal.center_ms==SEPT_START+ONE for x in g.potential_bos_witnesses))
    def test_hourly_right_confirmation_needed(self):
        line=synthetic()
        early=closed_hourly(line,SEPT_START+6*ONE)
        _,obs=observe_fractals_and_first_breach(early)
        r=next(x for x in obs if x.fractal.center_ms==SEPT_START+ONE and x.fractal.kind=="BSL")
        self.assertEqual(r.verdict,"WICK_NEEDS_FOLLOWING_CLOSED_HOUR")
    def test_5m_unclosed_asof_not_accepted(self):
        line=synthetic()
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_UNCLOSED"):
            cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms-1)
    def test_false_source_ready_not_accepted(self):
        line=replace(synthetic(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_C20A_SOURCE"):
            cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
    def test_corrupt_origin_row_id_rejected(self):
        line=synthetic()
        a=line.original_5m_closed
        bad=replace(a[7],origin_raw_row_id="tampered")
        line=replace(line,original_5m_closed=a[:7]+(bad,)+a[8:])
        with self.assertRaisesRegex(ValueError,"CORRUPTED_FIVE_MINUTE_SOURCE_ROW"):
            cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
    def test_future_suffix_invariance(self):
        line=synthetic()
        cut=SEPT_START+85*FIVE
        short=replace(line,as_of_ms=cut,original_5m_closed=line.original_5m_closed[:85])
        a=cross_timeframe_raid_break(short,as_of_ms=cut)
        b=cross_timeframe_raid_break(line,as_of_ms=cut)
        self.assertEqual(a,b)
    def test_unapproved_academic_bos_even_if_geometry_matches(self):
        line=synthetic()
        obs=cross_timeframe_raid_break(line,as_of_ms=line.as_of_ms)
        self.assertTrue(obs.potential_bos_witnesses)
        self.assertEqual(obs.author_status,"AUTHOR_GOLDEN_SOURCE_UNAVAILABLE")
        self.assertEqual(obs.readiness,"NOT_TRADE_READY")
        self.assertIn("NO_AUTHOR_FUTURES_GOLDEN",obs.missing_context)
if __name__=="__main__":unittest.main()
