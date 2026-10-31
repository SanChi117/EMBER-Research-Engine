import unittest
from a233_audit import closed_balance_dd, overlaps

def trade(start, end, pnl=0, stake=100):
    return dict(open_timestamp=start, close_timestamp=end, profit_abs=pnl, stake_amount=stake)

class AuditTests(unittest.TestCase):
    def test_initial_capital_is_peak(self):
        self.assertAlmostEqual(closed_balance_dd([trade(0, 1, -20)], 100), 20)

    def test_same_time_closes_are_one_event(self):
        self.assertEqual(closed_balance_dd([trade(0, 1, -20), trade(0, 1, 20)], 100), 0)

    def test_peak_to_trough(self):
        self.assertAlmostEqual(closed_balance_dd([trade(0, 1, 25), trade(1, 2, -25)], 100), 20)

    def test_adjacent_trades_do_not_overlap(self):
        self.assertEqual(overlaps([trade(0, 10), trade(10, 20)])['max_simultaneous_positions'], 1)

    def test_simultaneous_overlap_and_stakes(self):
        r = overlaps([trade(0, 7200000, stake=100), trade(3600000, 10800000, stake=200)])
        self.assertEqual(r['hours_with_multiple_positions'], 1)
        self.assertEqual(r['max_sum_original_stakes_usdt'], 300)
        self.assertEqual(r['max_simultaneous_positions'], 2)

    def test_zero_duration_excluded_explicitly(self):
        r = overlaps([trade(0, 0)])
        self.assertEqual(r['zero_duration_trades_excluded_from_overlap'], 1)
        self.assertEqual(r['max_simultaneous_positions'], 0)

    def test_reversed_dates_fail(self):
        with self.assertRaises(ValueError):
            overlaps([trade(10, 0)])

if __name__ == '__main__':
    unittest.main()
