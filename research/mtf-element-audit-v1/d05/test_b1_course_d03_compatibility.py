"""B1 experimental seam tests for unchanged course-v05 primitives and C07 D03 ledger.

These characterize compatibility and **expose** gaps. They do NOT harmonize
the sources or declare any academic trade trigger valid.
"""
from __future__ import annotations
import pathlib, sys, unittest

RESEARCH=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(RESEARCH/"mtf-course-v05"/"src"))
sys.path.insert(0,str(RESEARCH/"mtf-element-audit-v1"/"tools"))
from course_primitives_v05 import Bar, POI, PoiLifecycle
from strict_event_lineage_d03 import CausalEvent, EventLedger, D03Rejected

TF=900_000
def bar(i,o=101,h=102,l=99,c=101):
    return Bar(i*TF,(i+1)*TF,o,h,l,c,"15m")

def ev(uid,kind,start,end,known,parent=(),evidence=("root",),decision=None):
    return CausalEvent(uid,kind,"BTCUSDT","BINANCE","USDM_FUTURES","15m",
        start,end,known,tuple(parent),tuple(evidence),decision_at_ms=decision)

class CourseVsD03Seams(unittest.TestCase):
    def test_v05_existing_poi_lifecycle_first_touch_only(self):
        zone=POI("z","1h","LONG",98,100,0)
        lifecycle=PoiLifecycle(zone)
        self.assertEqual(lifecycle.advance(bar(0,o=103,h=104,l=102,c=103)),"FRESH")
        self.assertEqual(lifecycle.advance(bar(1,o=102,h=103,l=99,c=102)),"TESTED")
        self.assertEqual(lifecycle.tested_at,2*TF)

    def test_v05_second_touch_not_differentiated_yet(self):
        zone=POI("z","1h","LONG",98,100,0)
        lifecycle=PoiLifecycle(zone)
        lifecycle.advance(bar(0,o=102,h=103,l=99,c=102))
        old=lifecycle.tested_at
        lifecycle.advance(bar(1,o=103,h=104,l=102,c=103))
        self.assertEqual(lifecycle.advance(bar(2,o=102,h=103,l=99,c=102)),"TESTED")
        self.assertEqual(lifecycle.tested_at,old)  # DOCUMENTED GAP, not a pass on repeat logic

    def test_v05_does_not_update_invalidated_after_test(self):
        zone=POI("z","1h","LONG",98,100,0)
        lifecycle=PoiLifecycle(zone)
        self.assertEqual(lifecycle.advance(bar(0,o=102,h=103,l=99,c=101)),"TESTED")
        self.assertEqual(lifecycle.advance(bar(1,o=99,h=100,l=95,c=97)),"TESTED")
        # Needs a separate as-of invalidation ledger; original cannot be treated as complete.

    def test_v05_first_touch_not_backdated_before_known(self):
        zone=POI("z","1h","LONG",98,100,2*TF)
        lifecycle=PoiLifecycle(zone)
        self.assertEqual(lifecycle.advance(bar(0,o=100,h=101,l=99,c=100)),"FRESH")
        self.assertEqual(lifecycle.advance(bar(1,o=102,h=103,l=99,c=102)),"FRESH")
        self.assertEqual(lifecycle.advance(bar(2,o=102,h=103,l=99,c=102)),"TESTED")
        self.assertEqual(lifecycle.tested_at,3*TF)

    def test_d03_source_poi_test_causal_chain(self):
        g=EventLedger()
        g.add(ev("source","SOURCE",0,TF,TF))
        g.add(ev("poi","POI",TF,2*TF,2*TF,("source",)))
        g.add(ev("first","TEST",2*TF,3*TF,3*TF,("poi",)))
        self.assertEqual([x.uid for x in g.snapshot(3*TF)],["source","poi","first"])
        self.assertEqual(g.digest(),EventLedger.replay(g.export()).digest())

    def test_d03_reject_future_decision_confirmation(self):
        with self.assertRaisesRegex(D03Rejected,"DECISION_BEFORE_KNOWN"):
            ev("first","TEST",2*TF,3*TF,3*TF,("poi",),decision=2*TF)

    def test_d03_reject_parent_invalidated_before_test(self):
        g=EventLedger()
        g.add(ev("source","SOURCE",0,TF,TF))
        g.add(ev("poi","POI",TF,2*TF,2*TF,("source",)))
        g.add(ev("inv","INVALIDATION",2*TF,3*TF,3*TF,("poi",)))
        with self.assertRaisesRegex(D03Rejected,"PARENT_ANCESTRY_INVALIDATED"):
            g.add(ev("test","TEST",3*TF,4*TF,4*TF,("poi",)))

    def test_d03_temporal_only_link_can_omit_price_geometry(self):
        g=EventLedger()
        g.add(ev("source","SOURCE",0,TF,TF))
        g.add(ev("poi","POI",TF,2*TF,2*TF,("source",)))
        # There is no price field or zone intersection in CausalEvent. Even
        # geometrically unrelated test labels would be formally accepted.
        g.add(ev("unknown_price_contact","TEST",2*TF,3*TF,3*TF,("poi",)))
        self.assertEqual(len(g.snapshot(3*TF)),3)
        self.assertFalse("price" in CausalEvent.__dataclass_fields__)

if __name__=="__main__":
    unittest.main(verbosity=2)
