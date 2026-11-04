"""Import research-only replay tests into EMBER's normal pytest suite."""
import io
import unittest
from pathlib import Path


def test_market_structure_replay_unittest_suite():
    root = Path(__file__).resolve().parents[1] / 'research' / 'market_structure_replay_20261104'
    suite = unittest.TestLoader().discover(str(root), pattern='test_replay.py')
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    assert result.testsRun >= 11
    assert result.wasSuccessful(), 'offline replay causal/zip tests failed'