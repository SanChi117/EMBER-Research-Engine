#!/usr/bin/env python3
"""Partition one complete validated C43 45ZIP JSON into immutable market parts.

Keeps the complete canonical aggregate SHA256 (including pretty-print bytes),
plus exact byte SHA256 per market JSON. Never omits source observations,
summarizes trades, or silently truncates. Read-only, no orders.
"""
import hashlib,json,sys
from pathlib import Path

NAMES=("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT")
PREFIX="C43_ORIGINAL_"
SUFFIX="_ALL_CANDIDATE_RERANK.json"

def make_parts(aggregate_path,output_dir):
    original=Path(aggregate_path).read_bytes()
    obj=json.loads(original)
    assert obj["original_usdm_binance_zip"]==45
    assert obj["original_native3m_closed"]==76800
    assert obj["native15m_exact_decimal"]==15360
    assert obj["source_route_count"]==36
    assert obj["parent_correlated_contexts"]==17316
    assert obj["orders"]==obj["trades"]==obj["source_author_goldens"]==0
    assert obj["readiness"]=="NOT_TRADE_READY"
    markets=obj.pop("markets")
    assert tuple(m["symbol"] for m in markets)==NAMES
    target=Path(output_dir)
    target.mkdir(parents=True,exist_ok=True)
    parts=[]
    for market in markets:
        assert len(market["routes"])==36
        assert market["orders"]==market["trades"]==0
        label=PREFIX+market["symbol"]+SUFFIX
        content=(json.dumps(market,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
        path=target/label
        path.write_bytes(content)
        parts.append({"symbol":market["symbol"],"name":label,
                      "sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content)})
        assert len(content)<95_000_000,"C43_MARKET_EXCEEDS_NORMAL_GIT_BLOB"
    manifest={"schema":"EMBER_C43_ORIGINAL_45ZIP_FIVE_MARKET_COMPLETE_SOURCE_MANIFEST_V1",
              "complete_aggregate_source_json_sha256":hashlib.sha256(original).hexdigest(),
              "complete_aggregate_source_json_bytes":len(original),
              "parent_metadata":obj,"market_parts":parts}
    p=target/"C43_ORIGINAL_45ZIP_MANIFEST.json"
    p.write_text(json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return manifest

def verify_parts(directory):
    root=Path(directory)
    manifest=json.loads((root/"C43_ORIGINAL_45ZIP_MANIFEST.json").read_text(encoding="utf-8"))
    assert len(manifest["market_parts"])==5
    markets=[]
    for p in manifest["market_parts"]:
        source=root/p["name"]
        blob=source.read_bytes()
        assert len(blob)==p["bytes"]
        assert hashlib.sha256(blob).hexdigest()==p["sha256"]
        value=json.loads(blob)
        assert value["symbol"]==p["symbol"]
        markets.append(value)
    all_data=dict(manifest["parent_metadata"])
    all_data["markets"]=markets
    joined=(json.dumps(all_data,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    assert len(joined)==manifest["complete_aggregate_source_json_bytes"]
    assert hashlib.sha256(joined).hexdigest()==manifest["complete_aggregate_source_json_sha256"]
    print("C43_FIVE_PARTS_REASSEMBLE_EXACT_CANONICAL_168MB_JSON_PASS",len(joined),
          manifest["complete_aggregate_source_json_sha256"],flush=True)
    return manifest

if __name__=="__main__":
    if len(sys.argv)==3:
        make_parts(sys.argv[1],sys.argv[2])
        verify_parts(sys.argv[2])
    elif len(sys.argv)==2:
        verify_parts(sys.argv[1])
    else:
        raise SystemExit("usage: partition_c43_source_result.py [aggregate.json] evidence-directory")
