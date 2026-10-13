"""No data window search/tuning and no modification of the original algorithm."""
from __future__ import annotations
import sys,unittest,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from run_frozen_oos_2025 import verify_period,scope_row,finite_model,END
class TestFrozenOOS(unittest.TestCase):
    def test_different_end_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Frozen OOS end'):
            verify_period('/nonexistent','2026-10-13T00:00:00Z')
    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'VISION manifest'):
                verify_period(tmp)
    def test_malformed_universe_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'manifest_vision.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'ten Futures'):
                verify_period(tmp)
    def test_scope_preserves_original_identity(self):
        row=scope_row('ETHUSDT',{'id':'SAME','route':'B_IDM'})
        self.assertEqual(row['id'],'ETHUSDT|SAME')
        self.assertEqual(row['source_id'],'SAME')
        with self.assertRaises(ValueError):scope_row('BTCUSDT',{'id':'x','symbol':'ETHUSDT'})
    def test_no_trade_no_invented_pf(self):
        z=finite_model([])
        self.assertEqual(z['closed_model_trades'],0)
        self.assertIsNone(z['profit_factor'])
if __name__=='__main__': unittest.main()