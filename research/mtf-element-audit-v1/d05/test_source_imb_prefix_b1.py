"""B1/C06 synthetic source-aligned IMB observation contract; no trading."""
from pathlib import Path
import sys,unittest
from dataclasses import FrozenInstanceError
H=Path(__file__).resolve().parent
sys.path[:0]=[str(H),str(H.parents[1]/"mtf-course-v05"/"src")]
from course_primitives_v05 import Bar,confirmed_imb
from source_imb_prefix_b1 import observe_source_defined_imbs,CourseImbRejected
T=3_600_000
M=900_000
def b(i,o,h,l,c):
    return Bar(T+i*M,T+(i+1)*M,o,h,l,c,"15m")
def scenario():
    return [b(0,102,105,100,103),b(1,104,109,103,108),
            b(2,107,111,106,110),b(3,109,112,106.5,110),
            b(4,108,110,105.5,108),b(5,110,113,107,112)]
def inspect(xs,at=None):
    return observe_source_defined_imbs(xs,xs[-1].end if at is None else at)
class ImbSource(unittest.TestCase):
    def test_not_known_until_third_close(self):
        xs=scenario()
        self.assertEqual(inspect(xs,xs[1].end),())
        self.assertEqual(inspect(xs,xs[2].end)[0].known_at_ms,xs[2].end)
    def test_zone_from_closed_wick_gap(self):
        x=inspect(scenario())[0]
        self.assertEqual((x.side,x.zone_lo,x.zone_hi),("LONG",105,106))
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_reaction_contact_after_formation(self):
        xs=scenario()
        x=inspect(xs)[0]
        self.assertEqual(x.contact.first_contact_at_ms,xs[4].end)
        self.assertTrue(any(v.type=="LATER_FAVORABLE_CLOSE_OBSERVED_NOT_VC" for v in x.contact.event_log))
    def test_no_contact_before_later_candle(self):
        xs=scenario()
        self.assertIsNone(inspect(xs,xs[3].end)[0].contact.first_contact_at_ms)
    def test_gapless_data_no_candidate(self):
        self.assertEqual(inspect([b(i,102,105,100,103) for i in range(5)]),())
    def test_source_primitives_unchanged(self):
        xs=scenario()
        expected=confirmed_imb(xs)
        actual=inspect(xs)
        self.assertEqual([(v.id,v.known,v.lo,v.hi) for v in expected],
                         [(v.imbalance_id,v.known_at_ms,v.zone_lo,v.zone_hi) for v in actual])
    def test_missing_bar_never_approves_first(self):
        xs=scenario()
        with self.assertRaisesRegex(CourseImbRejected,"MIXED_OR_GAPPED_HISTORY"):
            inspect([xs[0],xs[2],xs[3]])
    def test_mixed_tf_rejected(self):
        xs=scenario()
        xs[3]=Bar(T+M,T+M+300_000,109,112,106.5,110,"5m")
        with self.assertRaisesRegex(CourseImbRejected,"MIXED_OR_GAPPED_HISTORY"):
            inspect(xs)
    def test_asof_must_match_final_closed_bar(self):
        xs=scenario()
        with self.assertRaisesRegex(CourseImbRejected,"PREFIX_NOT_COMPLETE_TO_AS_OF"):
            inspect(xs[:4],xs[4].end)
    def test_later_history_never_moves_source_time(self):
        xs=scenario()
        self.assertEqual(inspect(xs,xs[2].end)[0].known_at_ms,inspect(xs)[0].known_at_ms)
    def test_no_same_formation_bar_entry(self):
        xs=scenario()
        self.assertIsNone(inspect(xs,xs[2].end)[0].contact)
    def test_immutable_and_unapproved(self):
        x=inspect(scenario())[0]
        self.assertIn("NOT_ACADEMIC_POI_SIGNOFF",x.status)
        with self.assertRaises(FrozenInstanceError):
            x.readiness="READY"
if __name__=="__main__":
    unittest.main(verbosity=2)
