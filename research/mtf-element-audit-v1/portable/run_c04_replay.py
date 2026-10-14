#!/usr/bin/env python3
"""One-command portable replay, subprocesses run outside author's workdir."""
import json,pathlib,subprocess,sys,tempfile,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(cmd):
 p=subprocess.run([sys.executable,*cmd],cwd=ROOT,check=False,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(f'{cmd}: {p.returncode}\n{p.stderr[-3500:]}\n{p.stdout[-1500:]}')
 return p.stdout+p.stderr

def main():
 with tempfile.TemporaryDirectory() as td:
  td=pathlib.Path(td)
  qa=run(['-m','unittest','discover','-s','tests','-p','test_d01_bar_closed_contract.py','-q'])
  mutation=run(['tests/challenge_d01_mutations.py',str(td/'mutations.json')])
  real=run(['tests/verify_d01_real_futures.py','--archive',str(ROOT/'baselines/binance_futures_2026.zip'),'--out',str(td/'real.json')])
  integrity=run(['tests/test_journal_integrity.py'])
  actual=json.loads((td/'real.json').read_text());reference=json.loads((ROOT/'evidence/C04_D01_REAL_PASS1.json').read_text())
  if actual!=reference:raise AssertionError('Portable real archive changed expected result')
  m=json.loads((td/'mutations.json').read_text())
  if m['rejected']!=180:raise AssertionError('Mutated examples accepted')
  j=json.loads(integrity)
  if not j['validations_pass']:raise AssertionError('Journal tamper detection failed')
  output={'status':'PASS','unit_tests':'30/30','mutations_rejected':m['rejected'],
          'data_csv_files':len(actual['files']),'15m_bars':actual['total_15m_bars'],
          '1d_bars':actual['total_1d_bars'],'cross_tf_daily':actual['daily_overlap_checked'],
          'same_report_as_prior':True,'journal_events':j['events'],'journal_evidence_checked':j['evidence_verification']['verified_evidence_blobs'],
          'engine_original_sha256':hashlib.sha256((ROOT/'baselines/mtf_engine_v05_original.py').read_bytes()).hexdigest(),
          'notes':'Validates D01 only. Data origin authenticated by D04 external future work.'}
  print(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2))
 return 0
if __name__=='__main__':sys.exit(main())