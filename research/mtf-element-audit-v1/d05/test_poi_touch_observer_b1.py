"""B1/C02 tests of read-only POI first-touch vs later-contact observer."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import POI, Bar
from poi_touch_observer_b1 import inspect_poi_touch_sequence, PoiObservationRejected

TF=900_000
def b(i,o=103,h=104,l=102,c=103,tf="15m"):
    return Bar(i*TF,(i+1)*TF,o,h,l,c,tf)
def zone(side="LONG",known=0):
    return POI("parent-poi","1h",side,98,100,known)

class TestPoiTouchObserver(unittest.TestCase):
    def test_initial_first_touch_not_ready(self):
        n=inspect_poi_touch_sequence(zone(),[b(0),b(1,o=102,h=103,l=99,c=102)],2*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE"])
        self.assertEqual(n.notes[0].known_at_ms,2*TF)
        self.assertEqual(n.readiness,"NOT_TRADE_READY")

    def test_continuous_contact_not_false_second_test(self):
        n=inspect_poi_touch_sequence(zone(),[b(0,o=102,h=103,l=99,c=102),b(1,o=102,h=103,l=99,c=102)],2*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE"])

    def test_exit_and_revisit_is_unclassified_not_automatic_entry(self):
        n=inspect_poi_touch_sequence(zone(),[
          b(0,o=102,h=103,l=99,c=102),b(1),b(2,o=102,h=103,l=99,c=102)
        ],3*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE","LATER_CONTACT_UNCLASSIFIED"])
        self.assertEqual(n.readiness,"NOT_TRADE_READY")

    def test_break_after_first_is_flagged_not_silently_ignored(self):
        n=inspect_poi_touch_sequence(zone(),[
          b(0,o=102,h=103,l=99,c=102),b(1,o=99,h=100,l=96,c=97)
        ],2*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE","POST_FIRST_CLOSE_BREACH_NEEDS_RULE"])

    def test_pre_first_breach_is_original_v05(self):
        n=inspect_poi_touch_sequence(zone(),[b(0,o=99,h=100,l=96,c=97)],TF)
        self.assertEqual([x.kind for x in n.notes],["PRE_FIRST_CLOSE_BREACH_V05"])

    def test_old_bars_prior_to_parent_known_are_ignored(self):
        n=inspect_poi_touch_sequence(zone(known=2*TF),[
          b(0,o=102,h=103,l=99,c=102),b(1,o=102,h=103,l=99,c=102),b(2,o=102,h=103,l=99,c=102)
        ],3*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE"])
        self.assertEqual(n.notes[0].bar_start_ms,2*TF)

    def test_futures_prefix_stability_future_modified_does_not_change(self):
        initial=[b(0,o=102,h=103,l=99,c=102)]
        n=inspect_poi_touch_sequence(zone(),initial,TF)
        a=inspect_poi_touch_sequence(zone(),initial+[b(1,o=99,h=100,l=96,c=97)],TF)
        self.assertEqual(n.notes,a.notes)

    def test_short_zone_breach_after_first_only_diagnostic(self):
        z=zone("SHORT")
        n=inspect_poi_touch_sequence(z,[
          b(0,o=97,h=99,l=96,c=97),
          b(1,o=100,h=105,l=99,c=104)
        ],2*TF)
        self.assertEqual([x.kind for x in n.notes],["FIRST_TEST_CANDIDATE","POST_FIRST_CLOSE_BREACH_NEEDS_RULE"])

    def test_empty_diagnostics_never_ready(self):
        n=inspect_poi_touch_sequence(zone(),[],TF)
        self.assertEqual(n.notes,())
        self.assertEqual(n.readiness,"NOT_TRADE_READY")

    def test_nan_poizone_rejected(self):
        z=POI("bad","1h","LONG",float("nan"),100,0)
        with self.assertRaisesRegex(PoiObservationRejected,"INVALID_POI_GEOMETRY"):
            inspect_poi_touch_sequence(z,[b(0)],TF)

    def test_as_of_type_must_be_integer(self):
        with self.assertRaisesRegex(PoiObservationRejected,"INVALID_AS_OF_TIME"):
            inspect_poi_touch_sequence(zone(),[b(0)],"tomorrow")

    def test_noncontiguous_closed_bars_not_allowed(self):
        with self.assertRaisesRegex(ValueError,"missing/overlapping bars"):
            inspect_poi_touch_sequence(zone(),[b(0),b(2)],3*TF)

    def test_no_source_confirmation_from_touch_alone(self):
        n=inspect_poi_touch_sequence(zone(),[b(0,o=102,h=103,l=99,c=102)],TF)
        self.assertEqual(n.source_status,"COURSE_REACTION_LIFECYCLE_PARTIAL")
        self.assertTrue(all(x.kind.endswith("CANDIDATE") or x.kind.endswith("RULE") for x in n.notes))

if __name__=="__main__":
    unittest.main(verbosity=2)
