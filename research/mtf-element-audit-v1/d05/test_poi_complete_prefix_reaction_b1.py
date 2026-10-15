"""B1/C05: source-boundary + adversarial causality checks for POI reaction diagrams.

These are deliberately synthetic *price paths* to falsify a mechanism.
They are not author-chart labels and do not create trade setups.
"""
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

D05=Path(__file__).resolve().parent
sys.path.insert(0,str(D05))
sys.path.insert(0,str(D05.parents[1]/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,POI
from poi_complete_prefix_reaction_b1 import PrefixRejected,inspect_complete_poi_prefix

STEP=900_000
T0=3_600_000

def candle(i,low=101,high=103,op=102,cl=102,step=STEP,base=T0,tf="15m"):
    return Bar(base+i*step,base+(i+1)*step,op,high,low,cl,tf)
def zone(side="LONG",known=T0):
    return POI("course-parent-candidate","1h",side,99,100,known)
def path():
    return [
        candle(0),
        candle(1,low=99.5,high=103),
        candle(2,low=101,high=104,cl=103),
        candle(3),
        candle(4,low=99.5,high=103),
    ]
def inspect(bars=None,asof=None,poi=None):
    xs=path() if bars is None else bars
    t=(xs[-1].end if xs else T0+STEP) if asof is None else asof
    return inspect_complete_poi_prefix(zone() if poi is None else poi,xs,t)

class AcademicLevelReactionPrefixContract(unittest.TestCase):
    def test_complete_history_first_contact_is_from_second_bar(self):
        x=inspect()
        self.assertEqual(x.first_contact_at_ms,T0+2*STEP)
        self.assertEqual(x.contact_count,2)
        self.assertEqual(x.event_log[0].type,"FIRST_CONTACT_OBSERVED_COMPLETE_PREFIX")
        self.assertEqual(x.order_readiness,"NOT_TRADE_READY")

    def test_subsequent_directional_move_is_only_observation(self):
        x=inspect()
        later=[t for t in x.event_log if t.type=="LATER_FAVORABLE_CLOSE_OBSERVED_NOT_VC"]
        self.assertEqual(len(later),1)
        self.assertEqual(later[0].bar_start_ms,T0+2*STEP)
        self.assertIn("UNKNOWN",x.academy_level_status)
        self.assertIn("NOT_ACADEMIC_VC",x.response_status)

    def test_repeated_zone_touch_after_exit_not_first_again(self):
        x=inspect()
        self.assertEqual([v.type for v in x.event_log].count("FIRST_CONTACT_OBSERVED_COMPLETE_PREFIX"),1)
        self.assertEqual([v.type for v in x.event_log].count("LATER_CONTACT_UNCLASSIFIED"),1)

    def test_continuous_contact_is_single_contact_group(self):
        xs=[candle(0,low=99.5),candle(1,low=99.6),candle(2,low=99.8)]
        x=inspect(xs)
        self.assertEqual(x.contact_count,1)
        self.assertEqual([v.type for v in x.event_log].count("LATER_CONTACT_UNCLASSIFIED"),0)

    def test_same_candle_wick_and_high_close_not_sequential_response(self):
        xs=[candle(0,low=99.5,high=110,cl=109)]
        x=inspect(xs)
        self.assertEqual([v.type for v in x.event_log],["FIRST_CONTACT_OBSERVED_COMPLETE_PREFIX"])

    def test_bearish_short_move_after_test_is_observation(self):
        xs=[candle(0,low=97,high=99.7,op=98.5,cl=98),
            candle(1,low=95,high=98,op=97,cl=96)]
        x=inspect(xs,poi=zone("SHORT"))
        self.assertEqual([v.type for v in x.event_log],
            ["FIRST_CONTACT_OBSERVED_COMPLETE_PREFIX","LATER_FAVORABLE_CLOSE_OBSERVED_NOT_VC"])

    def test_opposite_boundary_breach_is_warning_not_source_invalidation(self):
        xs=[candle(0,low=99.5),candle(1,low=97,high=102,cl=98)]
        x=inspect(xs)
        self.assertIn("CLOSE_BEYOND_OPPOSITE_BOUND_NEEDS_INVALIDATION_RULE",[v.type for v in x.event_log])
        self.assertEqual(x.order_readiness,"NOT_TRADE_READY")

    def test_untouched_prefix_has_no_first_contact(self):
        xs=[candle(0),candle(1),candle(2)]
        x=inspect(xs)
        self.assertIsNone(x.first_contact_at_ms)
        self.assertEqual(x.event_log,())
        self.assertEqual(x.contact_count,0)

    def test_missing_first_bar_must_not_label_later_touch_as_first(self):
        xs=path()[1:]
        with self.assertRaisesRegex(PrefixRejected,"NOT_ALL_POST_KNOWN_CANDLES_PRESENT"):
            inspect(xs)

    def test_internal_gap_must_not_forge_first_test(self):
        xs=[path()[0],path()[2],path()[3]]
        with self.assertRaisesRegex(PrefixRejected,"INCOMPLETE_OR_MIXED_TIMEFRAME_PREFIX"):
            inspect(xs)

    def test_tf_mixing_rejected(self):
        xs=[candle(0),candle(1,tf="5m",step=300_000,base=T0+STEP)]
        with self.assertRaisesRegex(PrefixRejected,"INCOMPLETE_OR_MIXED_TIMEFRAME_PREFIX"):
            inspect(xs,asof=T0+2*STEP)

    def test_late_asof_with_missing_final_bar_rejected(self):
        with self.assertRaisesRegex(PrefixRejected,"NOT_ALL_POST_KNOWN_CANDLES_PRESENT"):
            inspect(path()[:3],asof=T0+4*STEP)

    def test_known_at_inside_candle_is_unknown_not_confident_first(self):
        with self.assertRaisesRegex(PrefixRejected,"UNKNOWN_CONTACT_IN_PARTIAL_KNOWN_CANDLE"):
            inspect(poi=zone(known=T0+1))

    def test_as_of_not_closed_bar_boundary_rejected(self):
        with self.assertRaisesRegex(PrefixRejected,"AS_OF_NOT_CLOSED_BAR_BOUNDARY"):
            inspect(asof=T0+3*STEP+1)

    def test_future_suffix_cannot_change_past(self):
        xs=path()
        prev=inspect(xs,asof=T0+3*STEP)
        altered=xs[:3]+[candle(3,low=97,high=120,cl=110),candle(4,low=99.5)]
        a=inspect(altered,asof=T0+3*STEP)
        self.assertEqual(a,prev)

    def test_future_first_contact_is_not_revealed_early(self):
        xs=[candle(0),candle(1),candle(2,low=99.5)]
        x=inspect(xs,asof=T0+2*STEP)
        self.assertIsNone(x.first_contact_at_ms)

    def test_future_hindsight_must_not_change_first_timestamp(self):
        old=inspect(path()[:3],asof=T0+3*STEP)
        later=inspect(path(),asof=T0+5*STEP)
        self.assertEqual(old.first_contact_at_ms,later.first_contact_at_ms)

    def test_no_bars_and_wrong_input_fail_closed(self):
        with self.assertRaisesRegex(PrefixRejected,"NO_VALID_CANDLES"):
            inspect([])
        with self.assertRaisesRegex(PrefixRejected,"INVALID_POI_OR_BARS"):
            inspect_complete_poi_prefix("fake",path(),T0+5*STEP)

    def test_before_poi_known_cannot_label_touch(self):
        with self.assertRaisesRegex(PrefixRejected,"INVALID_AS_OF_OR_POI_KNOWN"):
            inspect(asof=T0)

    def test_wrong_asof_type_rejected(self):
        with self.assertRaisesRegex(PrefixRejected,"INVALID_AS_OF_OR_POI_KNOWN"):
            inspect(asof="future")

    def test_future_partial_bar_ignored_at_prefix_time(self):
        xs=path()
        x=inspect(xs,asof=T0+2*STEP)
        y=inspect(xs[:2],asof=T0+2*STEP)
        self.assertEqual(x,y)

    def test_immutable_source_record_cannot_be_promoted_to_ready(self):
        x=inspect()
        with self.assertRaises(FrozenInstanceError):
            x.order_readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            x.event_log[0].type="CONFIRMED_ACADEMIC_VC"

    def test_underlying_v05_poi_remains_unchanged(self):
        poi=zone()
        before=(poi.id,poi.tf,poi.side,poi.lo,poi.hi,poi.known)
        inspect(path(),poi=poi)
        self.assertEqual(before,(poi.id,poi.tf,poi.side,poi.lo,poi.hi,poi.known))

if __name__=="__main__":
    unittest.main(verbosity=2)
