"""C81 original source queue adversarial tests. All user declarations quarantined."""
import unittest,json
from pathlib import Path
from dataclasses import replace
from c81_source_authenticated_review_queue import (build,validate_queue,submit_for_review,
    C81Rejected,QueueItem,C73_SHA,C72_GIT_BLOB)
ROOT=Path(__file__).resolve().parents[1]
C73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
C72=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
QUEUE=build(C73,C72)
def changed(data,which,key,value):
    d=json.loads(data)
    if which=="market":d["markets"][0][key]=value
    else:d["markets"][0]["original_parent_source_cases"][which][key]=value
    return json.dumps(d,sort_keys=True).encode("utf8")
class C81Tests(unittest.TestCase):
    def test_01_all_153_unverified_source_queue(self):
        a=validate_queue(QUEUE)
        self.assertEqual(a["total"],153)
        self.assertEqual(a["priority_counts"],{0:12,1:23,2:71,3:47})
        self.assertEqual(a["orders"],0)
    def test_02_initial_author_label_registry_empty(self):
        self.assertTrue(all(not x.author_verified and not x.entry_allowed and x.owner_document_anchor is None and x.claimed_author_label is None for x in QUEUE))
    def test_03_all_original5m_after_original15m(self):
        selected=[x for x in QUEUE if x.priority==0]
        self.assertEqual(len(selected),12)
        self.assertTrue(all(x.first_original_3m_close_ms<x.source15m_known_ms<x.first5m_known_ms for x in selected))
    def test_04_priorities_no_trade_inference(self):
        self.assertTrue(all(x.readiness=="NOT_TRADE_READY" and not x.orders and not x.fills and not x.trades for x in QUEUE))
    def test_05_backwards_c73_and_c72_cryptographic_frozen(self):
        import hashlib
        self.assertEqual(hashlib.sha256(C73).hexdigest(),C73_SHA)
        self.assertEqual(hashlib.sha1(b"blob "+str(len(C72)).encode()+b"\0"+C72).hexdigest(),C72_GIT_BLOB)
    def test_06_stable_source_order(self):
        self.assertEqual(QUEUE,build(C73,C72))
    def test_07_cross_symbol_unique_ids(self):
        self.assertEqual(len(set(x.source_key for x in QUEUE)),153)
    def test_08_all_five_actual_cryptocurrencies(self):
        self.assertEqual(set(x.symbol for x in QUEUE),{"BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"})
    def test_09_human_provided_hash_not_authentication(self):
        z=submit_for_review(QUEUE[0],document_sha256="a"*64,source_anchor="video frame 02",reviewer_declared="I am the author")
        self.assertEqual(z["review_status"],"QUARANTINED_EXTERNAL_OWNER_MEDIA_UNAUTHENTICATED")
        self.assertFalse(z["author_verified"])
        self.assertEqual(z["orders"],[])
    def test_10_review_queue_declares_no_positive_or_negative(self):
        s=validate_queue(QUEUE)
        self.assertEqual(s["proven_positive_goldens"]+s["proven_negative_goldens"],0)
    def test_11_sorted_by_priority_not_profit(self):
        self.assertEqual([x.priority for x in QUEUE[:12]],[0]*12)
        self.assertEqual([x.priority for x in QUEUE[12:35]],[1]*23)
    def test_12_immutable_slots(self):
        from dataclasses import FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):QUEUE[0].author_verified=True
    def test_13_declared_reviewer_is_not_attestation(self):
        d=submit_for_review(QUEUE[1],document_sha256="f"*64,source_anchor="slide 12",reviewer_declared="Reviewed by 2 independent AI")
        self.assertFalse(d["independent_reviewer_verification_complete"])
    def test_14_original_parent_4H_1H_fork_unchanged(self):
        self.assertEqual(sum(x.parent_fork.startswith("NEW_1H_VC_FIRST_SOURCE_TEST_") for x in QUEUE),35)

def reject_queue(change):
    def test(self):
        row=list(QUEUE)
        change(row)
        with self.assertRaises(C81Rejected):validate_queue(tuple(row))
    return test

BAD_QUEUE={
 "duplicate_source_id":lambda q:q.__setitem__(1,q[0]),
 "reversed_priority_order":lambda q:q.reverse(),
 "forged_author_verified":lambda q:q.__setitem__(0,replace(q[0],author_verified=True)),
 "forged_author_authenticated":lambda q:q.__setitem__(0,replace(q[0],author_source_authenticated=True)),
 "fake_owner_source_label":lambda q:q.__setitem__(0,replace(q[0],claimed_author_label="VALID")),
 "fake_owner_video_anchor":lambda q:q.__setitem__(0,replace(q[0],owner_document_anchor="doc:slide5")),
 "fake_reviewer_proof":lambda q:q.__setitem__(0,replace(q[0],reviewer_attestations=("signed",))),
 "fake_entry":lambda q:q.__setitem__(0,replace(q[0],entry_allowed=True)),
 "fake_orders":lambda q:q.__setitem__(0,replace(q[0],orders=("BUY",))),
 "fake_fill":lambda q:q.__setitem__(0,replace(q[0],fills=("DONE",))),
 "fake_trade":lambda q:q.__setitem__(0,replace(q[0],trades=("LONG",))),
 "fake_ready":lambda q:q.__setitem__(0,replace(q[0],readiness="READY")),
 "fake_source_key":lambda q:q.__setitem__(0,replace(q[0],source_key="BTCUSDT/forged")),
 "fake_priority":lambda q:q.__setitem__(0,replace(q[0],priority=3)),
 "case_deleted":lambda q:q.pop(),
 }
for name,fn in BAD_QUEUE.items():setattr(C81Tests,"test_bad_"+name,reject_queue(fn))

def reject_media(**kwargs):
    def test(self):
        x=dict(document_sha256="a"*64,source_anchor="page3",reviewer_declared="reviewer")
        x.update(kwargs)
        with self.assertRaises(C81Rejected):submit_for_review(QUEUE[0],**x)
    return test
for name,kwargs in {
 "bad_hash":{"document_sha256":"a"},
 "uppercase_hash":{"document_sha256":"A"*64},
 "bad_anchor":{"source_anchor":""},
 "bad_anchor_type":{"source_anchor":123},
 "bad_reviewer":{"reviewer_declared":""},
 "bad_reviewer_type":{"reviewer_declared":123},
 "none_hash":{"document_sha256":None},
 "none_reviewer":{"reviewer_declared":None}
}.items():setattr(C81Tests,"test_bad_media_"+name,reject_media(**kwargs))

class C81SourceSpoof(unittest.TestCase):
    def test_bad_source_73_sha(self):
        x=bytearray(C73);x[-20]^=1
        with self.assertRaises(C81Rejected):build(bytes(x),C72)
    def test_bad_source_72_sha(self):
        x=bytearray(C72);x[-10]^=1
        with self.assertRaises(C81Rejected):build(C73,bytes(x))
    def test_json_copy_does_not_have_original_identity(self):
        with self.assertRaises(C81Rejected):build(json.dumps(json.loads(C73)).encode(),C72)
    def test_user_provided_lists_not_original_bytes(self):
        with self.assertRaises(C81Rejected):build([],[])
    def test_forged_queue_ready(self):
        with self.assertRaises(C81Rejected):validate_queue(tuple(replace(x,readiness="READY") for x in QUEUE))
    def test_untrusted_c80_claim_is_not_source_authority(self):
        d=submit_for_review(QUEUE[0],document_sha256="a"*64,source_anchor="frame2",reviewer_declared="AUTHOR")
        self.assertFalse(d["entry_allowed"])
        self.assertFalse(d["author_verified"])

if __name__=="__main__":unittest.main()
