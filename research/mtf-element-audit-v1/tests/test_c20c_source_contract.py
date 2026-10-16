"""Research-only C20C author-source contract: no inferred trade approval."""
import unittest

class TestSourceContract(unittest.TestCase):
    def test_no_trade_ready(self):
        self.assertNotEqual("NOT_TRADE_READY", "READY")
