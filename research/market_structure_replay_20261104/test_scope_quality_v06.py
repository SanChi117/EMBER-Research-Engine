"""MSR06: strictly causal geometry tests, with no future market data in signals."""
import unittest
from replay import Bar, STEP_MS
from scope_quality_v06 import qualifies,strict_crossing,episodes

class ScopeQualityTests(unittest.TestCase):
    def setUp(self):
        self.data={}
        for i,v in enumerate((100,102,103,99,101)):
            self.data[(i+1)*STEP_MS]=Bar('BTCUSDT',i*STEP_MS,v,v+.1,v-.1,v,1)
    def test_qualified(self):
        self.assertTrue(qualifies(101,1,100,2))
        self.assertFalse(qualifies(100,1,100,2))
    def test_bear_qualified(self):
        self.assertTrue(qualifies(99,-1,100,2))
        self.assertFalse(qualifies(101,-1,100,2))
    def test_continuation_not_crossing(self):
        self.assertIsNone(strict_crossing(self.data,2*STEP_MS,3*STEP_MS,1,100,2))
    def test_reentry_is_new_crossing(self):
        self.assertEqual(strict_crossing(self.data,2*STEP_MS,5*STEP_MS,1,100,2),5*STEP_MS)
    def test_lookahead_does_not_modify_previous_result(self):
        a=strict_crossing(self.data,STEP_MS,3*STEP_MS,1,100,2)
        self.data[5*STEP_MS]=Bar('BTCUSDT',4*STEP_MS,50,51,49,50,1)
        self.assertEqual(a,strict_crossing(self.data,STEP_MS,3*STEP_MS,1,100,2))
    def test_episodes_adjacent_and_separated(self):
        x=[{'symbol':'BTCUSDT','side':1,'sweep_at':'2026-08-01T00:00:00Z'},
           {'symbol':'BTCUSDT','side':1,'sweep_at':'2026-08-01T04:00:00Z'},
           {'symbol':'BTCUSDT','side':1,'sweep_at':'2026-08-01T12:00:00Z'}]
        self.assertEqual(episodes(x,4),2)
    def test_distinct_symbol_does_not_merge(self):
        x=[{'symbol':'BTCUSDT','side':1,'sweep_at':'2026-08-01T00:00:00Z'},
           {'symbol':'ETHUSDT','side':1,'sweep_at':'2026-08-01T00:00:00Z'}]
        self.assertEqual(episodes(x,4),2)
    def test_distinct_direction_does_not_merge(self):
        x=[{'symbol':'BTCUSDT','side':1,'sweep_at':'2026-08-01T00:00:00Z'},
           {'symbol':'BTCUSDT','side':-1,'sweep_at':'2026-08-01T00:00:00Z'}]
        self.assertEqual(episodes(x,4),2)

if __name__=='__main__':unittest.main()
