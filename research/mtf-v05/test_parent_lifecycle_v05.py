"""Verified time-causal bug regression; not a teacher-chart precision test."""
import hashlib
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import mtf_engine
from mtf_engine_v05 import Feature,parent_issue_guard,ALGO

class ParentPOIAsOfGate(unittest.TestCase):
    def setUp(self):
        self.p=Feature('4h:fixture','4h','RB','LONG',97.,103.,1000,2000,'TEST_ONLY')
        self.states={self.p.id:{'poi':self.p,'tested':3000,'invalid':None,'issued_count':0}}
    def test_correct_time_order_allows(self):
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(True,'OK'))
    def test_rejects_invalid_at_exact_signal_boundary(self):
        self.states[self.p.id]['invalid']=5000
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(False,'PARENT_INVALIDATED'))
    def test_rejects_invalid_before_signal(self):
        self.states[self.p.id]['invalid']=4000
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(False,'PARENT_INVALIDATED'))
    def test_not_use_future_invalid_at_past_signal(self):
        self.states[self.p.id]['invalid']=6000
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(True,'OK'))
    def test_no_touch_no_trade(self):
        self.states[self.p.id]['tested']=None
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(False,'PARENT_NEVER_TOUCHED'))
    def test_touch_must_be_past(self):
        self.states[self.p.id]['tested']=5000
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(False,'PARENT_TEST_NOT_EARLIER'))
    def test_direct_4h_vc_1h_idm_does_not_need_retouch(self):
        self.states[self.p.id]['tested']=None
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000,require_touch=False),(True,'OK'))
    def test_too_old(self):
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,100),(False,'PARENT_TEST_EXPIRED'))
    def test_unknown_parent(self):
        self.assertEqual(parent_issue_guard(self.p,{},5000,20000),(False,'PARENT_NOT_REGISTERED'))
    def test_id_collision_fails_closed(self):
        self.states[self.p.id]['poi']=Feature(self.p.id,'4h','SNR','LONG',1,2,1,2,'OTHER')
        self.assertEqual(parent_issue_guard(self.p,self.states,5000,20000),(False,'PARENT_ID_COLLISION'))
    def test_frozen_original_engine_identical(self):
        raw=(ROOT/'src'/'mtf_engine.py').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'3d430361a7654b460281e76b1cb976c2a89676388a5adeb752049550992e6d46')
        self.assertEqual(mtf_engine.ALGO,'MTF_ROUTE_RESEARCH_0.3.0')
        self.assertIn('0.5.0_LIFECYCLE_REPAIR',ALGO)

if __name__=='__main__':unittest.main()
