#!/usr/bin/env python3
"""C83: deterministic 12 original crypto P0 course crosswalk source witness.

No image has a timestamp-authenticated match to crypto source history.
No author positive/negative golden is inferred from an illustrative chart.
"""
import sys,hashlib,json
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c83_owner_course_text_crosswalk import inspect_all,COURSE_CITATIONS,COURSE_ROUTE_ID,COURSE_RB_ID,COURSE_POI_ID
r=lambda p:(ROOT/p).read_bytes()
a=r("evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json")
b=r("evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json")
c=r("evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json")
rows,summary=inspect_all(a,b,c)
assert len(rows)==12 and all(not x.exact_course_media_timestamp_attested for x in rows)
assert summary["owner_authenticated_positive_goldens"]==0
assert summary["owner_authenticated_negative_goldens"]==0
document={
 "schema":"EMBER_C83_OWNER_TEXT_CROSSWALK_ORIGINAL12_P0_V1",
 "source_only":True,"not_trade_ready":True,
 "source_receipts":{
  "C73_sha256":hashlib.sha256(a).hexdigest(),
  "C72_git_blob_sha1":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest(),
  "C81_153_queue_sha256":hashlib.sha256(c).hexdigest()},
 "original_owner_lessons":[
  {"name":"Entry by IMB & SNR","drive_id":COURSE_ROUTE_ID,
   "locator":"https://drive.google.com/file/d/"+COURSE_ROUTE_ID+"/view",
   "scope":"Original author text only, illustrations not Binance-timestamp authenticated"},
  {"name":"Rejection Block","drive_id":COURSE_RB_ID,
   "locator":"https://drive.google.com/file/d/"+COURSE_RB_ID+"/view",
   "scope":"Original RB first-true-test and liquidity/IMB sweep lesson text"},
  {"name":"POI","drive_id":COURSE_POI_ID,
   "locator":"https://drive.google.com/file/d/"+COURSE_POI_ID+"/view",
   "scope":"Original support/resistance and POI strength lesson text"}],
 "course_text_rules":[{"anchor":v[0],"drive_id":v[1],"short_exact_source_text":v[2]}
                      for v in COURSE_CITATIONS],
 "source_observation_summary":summary,
 "crypto_source_P0_review_packets":[asdict(x) for x in rows],
 "first_author_authenticated_positive_crypto_golden":None,
 "first_author_authenticated_negative_crypto_golden":None,
 "author_media_exact_match_count":0,
 "unproven":["AUTHOR_VALID_FIRST_1H_POI_TEST",
            "15M_TRIGGER_VS_DIRECT_15M_VC",
            "TRUE_5M_VOLUME_CONFIRMATION",
            "STRONGHL_AND_STRUCTURAL_SL_TP",
            "MATCHING_AUTHOR_CHART_TIMESTAMPED_BINANCE_SOURCE"],
 "route_B_IDM_unmodified":True,"route_C_Raid_BOS_unmodified":True,
 "orders":0,"fills":0,"trades":0,"PnL":None,"readiness":"NOT_TRADE_READY"}
content=json.dumps(document,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
if len(sys.argv)>1:
 out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(content,encoding="utf8")
print("C83_FULL_SOURCE_JSON:"+json.dumps(document,ensure_ascii=False,sort_keys=True,separators=(",",":")))
print("C83_ALL12_OWNER_TEXT_CROSSWALK_SOURCE_ONLY_PASS",flush=True)
