#!/usr/bin/env python3
"""C83 complete independent frozen witness: bytes, SHA, source and replay.

C83 uses old Binance original crypto source snapshots, NOT new live ZIPs.
Lesson text citations are from user-owned Drive source text; no author chart
media/source timestamp attestation or strategy trade exists.
"""
import sys,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/"evidence/c83/C83_ORIGINAL12_P0_OWNER_COURSE_TEXT_CROSSWALK.json"
PIN="038aa9ba074804c5d1fd05140316a27b9f0326dcfbe3bb97d2fd626cdde07dc8"
def run():
    data=W.read_bytes()
    assert len(data)==20131,(len(data),"C83_BYTE_SIZE_DRIFT")
    assert hashlib.sha256(data).hexdigest()==PIN,"C83_PINNED_SHA_CHANGED"
    d=json.loads(data)
    assert d["schema"]=="EMBER_C83_OWNER_TEXT_CROSSWALK_ORIGINAL12_P0_V1"
    assert d["source_only"] is True and d["not_trade_ready"] is True
    assert len(d["crypto_source_P0_review_packets"])==12
    assert len(d["course_text_rules"])==7
    assert d["source_observation_summary"]["source_total_contexts"]==153
    assert d["author_media_exact_match_count"]==0
    assert d["source_observation_summary"]["owner_authenticated_positive_goldens"]==0
    assert d["source_observation_summary"]["owner_authenticated_negative_goldens"]==0
    assert (d["orders"],d["fills"],d["trades"])==(0,0,0)
    assert d["readiness"]=="NOT_TRADE_READY"
    p=d["crypto_source_P0_review_packets"]
    assert len({x["case_key"] for x in p})==12
    assert all(x["source15m_known_ms"]>x["first_3m_source_close_ms"]
               and x["source5m_known_ms"]>x["source15m_known_ms"] for x in p)
    assert all(not any((x["entry_allowed"],x["author_positive_golden"],
                        x["author_negative_golden"],x["author_eligible_15m_trigger"],
                        x["author_valid_first_poi_test"],x["author_5m_vc"]))
               for x in p)
    lessons={z["name"]:z["drive_id"] for z in d["original_owner_lessons"]}
    assert lessons=={
        "Entry by IMB & SNR":"1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ",
        "Rejection Block":"1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT",
        "POI":"1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R"}
    with tempfile.TemporaryDirectory() as temp:
        dst=Path(temp)/"C83_REPLAY.json"
        result=subprocess.run([sys.executable,
          str(ROOT/"tests/probe_c83_owner_12_crosswalk_witness.py"),str(dst)],
          capture_output=True,text=True,check=True)
        assert "C83_ALL12_OWNER_TEXT_CROSSWALK_SOURCE_ONLY_PASS" in result.stdout
        replay=dst.read_bytes()
        assert replay==data,"C83_FRESH_SOURCE_REGENERATION_NOT_BYTE_EQUAL"
    print("C83_INDEPENDENT_PINNED_20131_BYTE_SOURCE_AND_REPLAY_SHA_PASS",PIN)
    print("C83_OWNER_CRYPTO_GOLDENS_ZERO_NO_ENTRIES")
if __name__=="__main__":run()
