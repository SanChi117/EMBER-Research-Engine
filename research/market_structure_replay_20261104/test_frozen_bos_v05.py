"""MSR-05 causal regression tests. No trading, no fitted parameters."""
import unittest
from replay import Bar,iso
from frozen_bos_counterfactual_v05 import compare_symbol,summarize

STEP=900000
def small(lock_pivot=101,sweep_pivot=104,bars_count=150):
    b=[]
    for i in range(bars_count):
        price=100 if i<70 else 103 if i<75 else 105
        b.append(Bar('SOLUSDT',i*STEP,price,price+1,price-1,price,100))
    ev=[
      {'symbol':'SOLUSDT','event':'PIVOT_HIGH_CONFIRMED','candidate_id':'-','known_at':iso(b[10].known_at),'pivot_price':lock_pivot},
      {'symbol':'SOLUSDT','event':'ACCUMULATION_LOCKED','candidate_id':'x','known_at':iso(b[50].known_at),'atr1h':2},
      {'symbol':'SOLUSDT','event':'PIVOT_HIGH_CONFIRMED','candidate_id':'-','known_at':iso(b[60].known_at),'pivot_price':sweep_pivot},
      {'symbol':'SOLUSDT','event':'SWEEP_RETURN','candidate_id':'x','known_at':iso(b[69].known_at),'side':1,'reference':sweep_pivot,'pivot_known_at':iso(b[60].known_at)},
      {'symbol':'SOLUSDT','event':'STRUCTURE_BREAK_CONFIRMED','candidate_id':'x','known_at':iso(b[75].known_at),'side':1,'reference':sweep_pivot,'pivot_known_at':iso(b[60].known_at)}]
    return b,ev

class FrozenBOSTests(unittest.TestCase):
    def test_old_and_frozen_anchors_are_distinct(self):
        b,e=small()
        r=compare_symbol(b,e)[0]
        self.assertEqual((r['box_anchor'],r['sweep_anchor']),(101,104))
        self.assertEqual(r['status'],'BOTH')
        self.assertEqual(r['frozen_bos_at'],iso(b[70].known_at))
        self.assertEqual(r['original_bos_at'],iso(b[75].known_at))
    def test_future_cannot_change_past(self):
        b,e=small()
        previous=compare_symbol(b,e)
        future=[Bar(x.symbol,x.t,x.o,x.h+200,x.l,x.c*2,x.v) if i>=110 else x for i,x in enumerate(b)]
        self.assertEqual(previous,compare_symbol(future,e))
    def test_missing_anchor_remains_unknown(self):
        b,e=small()
        row=compare_symbol(b,e[1:])[0]
        self.assertEqual(row['status'],'NO_ANCHOR_AT_LOCK')
        self.assertIsNone(row['frozen_signal'])
    def test_invalid_original_bos_raises(self):
        b,e=small()
        e[-1]['known_at']=iso(b[90].known_at)
        with self.assertRaisesRegex(ValueError,'parity mismatch'):
            compare_symbol(b,e)
    def test_same_price_different_timestamp_is_reselection(self):
        b,e=small(lock_pivot=104)
        r=compare_symbol(b,e)[0]
        self.assertTrue(r['anchor_reselected'])
        self.assertFalse(r['anchor_price_changed'])
    def test_bos_not_before_sweep(self):
        b,e=small()
        e[3]['known_at']=e[-1]['known_at']
        with self.assertRaisesRegex(ValueError,'sweep precedes'):
            compare_symbol(b,e)
    def test_truncated_observation_censored(self):
        b,e=small(bars_count=87)
        self.assertFalse(compare_symbol(b,e)[0]['window_complete'])
    def test_summary_counts(self):
        b,e=small()
        self.assertEqual(summarize(compare_symbol(b,e))['original_bos'],1)

if __name__=='__main__':
    unittest.main()
