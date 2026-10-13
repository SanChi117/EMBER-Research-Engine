"""Specific archive conflict correction must fail closed, cannot change prices."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from repair_vision_jan29_2025 import conflicting_dates,validate_override,DAY,STEP
class TestVisionRepair(unittest.TestCase):
    def test_reject_incomplete_archive(self):
        with self.assertRaisesRegex(ValueError,'96 quarters'):validate_override([],{'volume':1})
    def test_reject_wrong_interval_and_timestamp(self):
        rows=[[DAY+i*STEP]+['1']*10 for i in range(96)]
        rows[0][0]=DAY-STEP
        with self.assertRaisesRegex(ValueError,'contiguous'):validate_override(rows,{'volume':96})
    def test_reject_price_conflict(self):
        rows=[[DAY+i*STEP]+['100','105','95','100','1']+['0']*5 for i in range(96)]
        with self.assertRaisesRegex(ValueError,'prices'):validate_override(rows,{'open':100,'high':111,'low':95,'close':100,'volume':96})
    def test_reject_volume_conflict(self):
        rows=[[DAY+i*STEP]+['100','105','95','100','1']+['0']*5 for i in range(96)]
        with self.assertRaisesRegex(ValueError,'volume'):validate_override(rows,{'open':100,'high':105,'low':95,'close':100,'volume':99})
if __name__=='__main__':unittest.main()