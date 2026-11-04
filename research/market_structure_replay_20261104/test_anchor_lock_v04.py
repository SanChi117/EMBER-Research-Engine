"""MSR-04 deterministic tests for frozen anchor vs sweep anchor. NO trading."""
import unittest
from replay import Bar, iso, replay
from anchor_lock_audit_v04 import compare, summarize

def fixture():
    t="2026-08-01T"
    return [
        {"symbol":"BTCUSDT","event":"PIVOT_HIGH_CONFIRMED","known_at":t+"01:00:00Z","pivot_price":110},
        {"symbol":"BTCUSDT","event":"PIVOT_LOW_CONFIRMED","known_at":t+"01:30:00Z","pivot_price":95},
        {"symbol":"BTCUSDT","event":"ACCUMULATION_LOCKED","known_at":t+"02:00:00Z","candidate_id":"A",
         "level_low":94,"level_high":112,"atr1h":2},
        {"symbol":"BTCUSDT","event":"PIVOT_HIGH_CONFIRMED","known_at":t+"02:45:00Z","pivot_price":108},
        {"symbol":"BTCUSDT","event":"SWEEP_RETURN","known_at":t+"03:00:00Z","candidate_id":"A",
         "side":1,"reference":108,"pivot_known_at":t+"02:45:00Z","extreme":93},
        {"symbol":"BTCUSDT","event":"STRUCTURE_BREAK_CONFIRMED","known_at":t+"03:45:00Z",
         "candidate_id":"A","side":1,"reference":108,"pivot_known_at":t+"02:45:00Z"},
    ]

class FrozenAnchorAudit(unittest.TestCase):
    def test_frozen_price_is_not_new_pivot(self):
        r=compare(fixture())
        self.assertEqual((r[0]["anchor_at_box"],r[0]["anchor_at_sweep"]),(110,108))
        self.assertEqual(r[0]["anchor_shift_atr1h"],-1.0)
        self.assertEqual(r[0]["anchor_status"],"RESELECTED")
    def test_absent_anchor_does_not_mean_failed_break(self):
        r=compare(fixture()[1:])
        self.assertIsNone(r[0]["anchor_at_box"])
        self.assertEqual(r[0]["anchor_status"],"MISSING_AT_BOX")
    def test_future_append_cannot_change_history(self):
        e=fixture()
        r=compare(e)
        future={"symbol":"BTCUSDT","event":"PIVOT_HIGH_CONFIRMED",
                "known_at":"2026-08-02T00:00:00Z","pivot_price":200}
        self.assertEqual(r,compare(e+[future]))
    def test_invalid_event_order_fails(self):
        e=fixture();e[3]["known_at"]="2026-08-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"unsorted"):compare(e)
    def test_orphan_bos_fails(self):
        e=fixture();e[-1]["candidate_id"]="missing"
        with self.assertRaisesRegex(ValueError,"orphan"):compare(e)
    def test_changed_bos_reference_fails(self):
        e=fixture();e[-1]["reference"]=109
        with self.assertRaisesRegex(ValueError,"BOS reference changed"):compare(e)
    def test_same_price_different_pivot_is_reselection(self):
        e=fixture();e[3]["pivot_price"]=110;e[4]["reference"]=110;e[5]["reference"]=110
        r=compare(e)
        self.assertTrue(r[0]["anchor_reselected"])
        self.assertFalse(r[0]["anchor_price_changed"])
    def test_bos_close_not_invented(self):
        r=compare(fixture())[0]
        self.assertNotIn("passed_frozen_anchor",r)
        self.assertIn("NOT a valid",r["note"])
    def test_synthetic_replay_is_not_modified(self):
        b=[Bar("BTCUSDT",i*900000,100,101,99,100,1000) for i in range(600)]
        original=replay(b).events
        _=compare(original)
        self.assertEqual(original,replay(b).events)

if __name__=="__main__":unittest.main()
