"""C24: a technical first intact price level NEVER approves a trade."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c21b_native_3m_vs_5m import make3
from c21_native3m_source_bridge import SEPT_START,THREE
from c24_bos_research_admission_gate import audit_route_admission

class C24FailClosedSourceTests(unittest.TestCase):
    def test_single_pivot_is_research_only(self):
        x=make3()
        r=audit_route_admission(x,as_of_ms=x.as_of_ms)
        self.assertGreater(r.total_original_research_edges,0)
        self.assertEqual(r.approved_trades,r.author_approved_bos)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        self.assertTrue(all(not c.author_approved for c in r.cases))
        self.assertTrue(all(c.reason.startswith(("REJECT_","RESEARCH_")) for c in r.cases))
    def test_multiple_parent_witness_is_preserved(self):
        x=make3()
        result=audit_route_admission(x,as_of_ms=x.as_of_ms)
        self.assertEqual(sum(c.reason=="REJECT_MULTIPLE_1H_RAID_PARENTS" for c in result.cases),
                         result.multiple_parent_refused)
    def test_early_before_raid_confirmation_is_empty(self):
        x=make3()
        self.assertEqual(audit_route_admission(x,as_of_ms=SEPT_START+7*3600000).total_original_research_edges,0)
    def test_asof_prefix_invariant(self):
        x=make3()
        cut=SEPT_START+141*THREE
        truncated=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        self.assertEqual(audit_route_admission(x,as_of_ms=cut),audit_route_admission(truncated,as_of_ms=cut))
    def test_fake_ready_rejected(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            audit_route_admission(x,as_of_ms=x.as_of_ms)
    def test_original_source_row_tamper_rejected(self):
        x=make3()
        bars=x.original_3m_closed
        x=replace(x,original_3m_closed=bars[:99]+(replace(bars[99],raw_id="bad"),)+bars[100:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            audit_route_admission(x,as_of_ms=x.as_of_ms)
