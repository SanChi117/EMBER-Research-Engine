#!/usr/bin/env python3
"""Validate normalized 2026 USDⓈ-M CSVs, declare offline provenance LIMIT explicitly."""
from __future__ import annotations
import json,sys,hashlib,zipfile,tempfile,shutil,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_vision_d04 import verify_offline_consolidated_manifest,digest,D04Rejected

def main():
 output=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evidence/C07_LOCAL_OFFLINE_2026.json'
 folder=ROOT/'baselines/d04_history_2026'
 a=verify_offline_consolidated_manifest(folder)
 b=verify_offline_consolidated_manifest(folder)
 if a!=b:raise AssertionError('NONDETERMINISTIC_SOURCE_AUDIT')
 # Deliberate forgery: copy all 10 CSV, change BTC open price and update *only* self-contained manifest SHA.
 # Proves manifest digest is integrity-only and cannot attest genuine Binance origin.
 with tempfile.TemporaryDirectory() as tmp:
  tmp=Path(tmp)
  for f in folder.glob('*.csv'):shutil.copyfile(f,tmp/f.name)
  orig=json.loads((folder/'manifest_vision.json').read_text())
  path=tmp/'BTCUSDT_15m.csv';blob=path.read_bytes()
  # Replace a single OHLC digit, keep time grid and row count the same.
  lines=blob.splitlines(keepends=True)
  first_data=lines[1].decode()
  fields=first_data.split(',');fields[1]='99999.99';lines[1]=(','.join(fields)).encode()
  forged=b''.join(lines);path.write_bytes(forged)
  for rec in orig:
   if (rec['symbol'],rec['tf'])==('BTCUSDT','15m'):rec['sha256']=digest(forged)
  (tmp/'manifest_vision.json').write_text(json.dumps(orig))
  spoof=verify_offline_consolidated_manifest(tmp)
  if spoof['status']!='OFFLINE_INTEGRITY_ONLY':raise AssertionError('DEMO_NOT_REPRODUCED')
 a.update({'repeat_byte_equivalent':True,'countercheck':{'tampered_CSV_plus_self_claimed_manifest_passed_OFFLINE_integrity':True,
           'interpretation':'Proof that local self-consistent hashes cannot establish the market source. This forged data must be rejected by independent ZIP+checksum receipts.'}})
 output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(a,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':a['status'],'series':a['series_verified'],'bars':a['total_bars'],'source_archives_claimed':a['declared_source_archives'],'forgery_demo':True}))
if __name__=='__main__':main()
