import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replay_portfolio_scoped_v04 import scope_row

class PortfolioSymbolIdentityTests(unittest.TestCase):
    def test_same_raw_id_different_symbol_is_distinct(self):
        raw={'id':'15m:IDEA:1700000:B_IDM', 'route':'B_IDM'}
        a=scope_row('BTCUSDT',raw)
        b=scope_row('ETHUSDT',raw)
        self.assertNotEqual(a['id'],b['id'])
        self.assertEqual(a['source_id'],b['source_id'])
        self.assertEqual(a['route'],b['route'])
    def test_symbol_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            scope_row('BTCUSDT',{'id':'x','symbol':'ETHUSDT'})
    def test_empty_id_rejected(self):
        with self.assertRaises(ValueError):
            scope_row('BTCUSDT',{'id':''})

if __name__=='__main__':unittest.main()
