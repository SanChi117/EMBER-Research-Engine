#!/usr/bin/env python3
"""Adversarial journal verification, including historical VOID events."""
from __future__ import annotations
import hashlib,json,tempfile,shutil,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
import auditlog

def verify_evidence(root, journal):
 entries=[json.loads(line) for line in journal.read_text(encoding='utf8').splitlines()]
 invalidated={e['invalidates_action_id'] for e in entries if e.get('invalidates_action_id')}
 ids={e['action_id'] for e in entries}
 if not invalidated.issubset(ids):raise AssertionError('Unknown invalidated ID')
 checked=0
 for e in entries:
  if e['action_id'] in invalidated:continue
  if e['verdict']=='DONE' and not e['evidence']:raise AssertionError('DONE without evidence')
  for ev in e['evidence']:
   p=root/ev['path']
   if not p.is_file():raise AssertionError('Missing evidence: '+str(p))
   if p.stat().st_size!=ev['bytes']:raise AssertionError('Evidence size changed: '+str(p))
   if e['verdict']=='DONE' and p.stat().st_size==0:raise AssertionError('DONE with zero-byte evidence')
   if hashlib.sha256(p.read_bytes()).hexdigest()!=ev['sha256']:
    raise AssertionError('Evidence hash mismatch: '+str(p))
   checked+=1
 return {'active_entries':len(entries)-len(invalidated),'invalidated':sorted(invalidated),'verified_evidence_blobs':checked}

def main():
 count,tip=auditlog.verify()
 validated=verify_evidence(BASE,BASE/'ЖУРНАЛ_ДЕЙСТВИЙ.jsonl')
 original=auditlog.JOURNAL
 probe={}
 with tempfile.TemporaryDirectory() as temp:
  temp=Path(temp);d=json.loads(original.read_text(encoding='utf8').splitlines()[1])
  mutated=original.read_text(encoding='utf8').splitlines()
  d['planned']='MALICIOUS_REWRITE_OF_PLAN';mutated[1]=json.dumps(d,ensure_ascii=False,sort_keys=True)
  poison=temp/'tampered.jsonl';poison.write_text('\n'.join(mutated)+'\n',encoding='utf8')
  auditlog.JOURNAL=poison
  try:auditlog.verify();probe['tampered_entry_rejected']=False
  except ValueError:probe['tampered_entry_rejected']=True
  dropped=temp/'dropped.jsonl';dropped.write_text('\n'.join(original.read_text(encoding='utf8').splitlines()[1:])+'\n',encoding='utf8')
  auditlog.JOURNAL=dropped
  try:auditlog.verify();probe['missing_first_entry_rejected']=False
  except ValueError:probe['missing_first_entry_rejected']=True
  auditlog.JOURNAL=original
  # Corrupt one evidence file in an isolated replica of just active evidence.
  fake=temp/'bad';fake.mkdir();
  for ev in json.loads(original.read_text(encoding='utf8').splitlines()[0])['evidence']:
   x=fake/ev['path'];x.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/ev['path'],x)
  # Inspect only isolated entry A001, changing its evidence while retaining same length.
  isolated=temp/'single.jsonl';isolated.write_text(original.read_text(encoding='utf8').splitlines()[0]+'\n',encoding='utf8')
  target=fake/json.loads(isolated.read_text(encoding='utf8'))['evidence'][0]['path'];data=bytearray(target.read_bytes());data[0]^=1;target.write_bytes(data)
  try:verify_evidence(fake,isolated);probe['edited_evidence_rejected']=False
  except AssertionError:probe['edited_evidence_rejected']=True
 result={'ledger_hash_chain':'PASS','events':count,'tip_sha256':tip,'evidence_verification':validated,'mutations':probe,
         'validations_pass':all(probe.values()),'note':'A003 was falsely marked DONE during a crash, was explicitly VOIDed by A004; original remains visible for audit. Hash chain is local, independently anchored only if git commit is made.'}
 print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
 return 0 if result['validations_pass'] else 1
if __name__=='__main__':raise SystemExit(main())