#!/usr/bin/env python3
"""C78 independent immutable C73/C72/C77 replay, no fresh ZIP download.

Real Binance source-derived snapshots are anchored to archived hashes.
Checks all 153 contexts and preserves C67/C73/C72 ambiguity, not trades.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c78_academic_causal_gate import assess,tally,C78Rejected
def load(rel):
    return (ROOT/rel).read_bytes()
C73="evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
C72="evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json"
C77="evidence/c77/C77_FRESH_ORIGINAL45ZIP_BRANCH_AWARE_POI_REPLAY.json"
def run():
    ra,rb,rc=load(C73),load(C72),load(C77)
    assert len(ra)==303327
    assert hashlib.sha256(ra).hexdigest()=="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
    assert hashlib.sha256(rc).hexdigest()=="170ffad3d49af83324ea3da12d031c2f53842bf7e1604cee6b1bfb9f4f01e394"
    frozen=json.loads(ra); five=json.loads(rb); older=json.loads(rc)
    assert hashlib.sha1(b"blob "+str(len(rb)).encode()+b"\0"+rb).hexdigest()==frozen["original_frozen_git_blobs"]["C72"]
    assert older["source_contexts"]==frozen["source_4h_C46_parent_count"]==153
    source5={ (m["symbol"],c["original_c46_4h_parent_index"]):c
              for m in five["markets"] for c in m["original_parent_source_cases"]}
    assert len(source5)==153
    records=[]
    for m in frozen["markets"]:
        sym=m["symbol"]
        for c in m["original_parent_source_cases"]:
            k=sym,c["original_c46_4h_parent_index"]
            records.append(assess(dict(c,symbol=sym),dict(source5[k],symbol=sym)))
    out=tally(tuple(records))
    assert out["contexts"]==153
    assert out["parent"]=={"NO_NEW_1H_POI":47,"UNSELECTED_1H_SOURCE":71,"SELECTED_1H_SOURCE":35}
    assert out["touch"]=={"NONE":118,"WICK_FIRST":23,"ONE_VISIT":9,"MULTIPLE_VISITS":3}
    assert out["source_15m"]=={"NONE":141,"IMB":6,"SNR":6}
    assert out["source_5m"]=={"NONE":141,"ALIGNED":4,"OPPOSITE":5,"AMBIGUOUS":3}
    assert out["author_verified"]==out["orders"]==out["fills"]==out["trades"]==0
    out.update({"schema":"EMBER_C78_CAUSAL_FROZEN_SOURCE_ONLY_V1",
        "C73_sha256":hashlib.sha256(ra).hexdigest(),
        "C72_git_blob_sha1":hashlib.sha1(b"blob "+str(len(rb)).encode()+b"\0"+rb).hexdigest(),
        "C77_sha256":hashlib.sha256(rc).hexdigest(),
        "original_archives_freshly_replayed_in_C78":False,
        "academic_first_valid_test_proven":0,
        "academic_15m_Trigger_or_15m_VC_proven":0,
        "academic_5m_VC_proven":0,
        "route_b_idm_approved":0,"route_c_raid_bos_approved":0,
        "all_selected_1h_parent_source_verified_by_C77":35,
        "course_15m_trigger_then_5m_VC_vs_no_trigger_direct_15m_VC":"UNRESOLVED",
        "source_kind_is_author_semantics":False})
    print("C78_FROZEN_SOURCE_ONLY_JSON:"+json.dumps(out,sort_keys=True,separators=(",",":")))
    print("C78_153_SOURCE_ROWS_CAUSAL_GATE_PASS_NOT_TRADE_READY")
    return out
if __name__=="__main__":run()
