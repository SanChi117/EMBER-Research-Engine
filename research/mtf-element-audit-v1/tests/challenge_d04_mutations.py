#!/usr/bin/env python3
"""Adversarial D04 integrity proof vs spoofed market source; deterministic."""
import io,sys,zipfile,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_vision_d04 import *
URL='https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-11.zip'
KEY='BTCUSDT-1d-2026-10-11.zip'

def create(row=None,extra=None):
 r=row or ['1791676800000','100','102','99','101','11','1791763199999','1111','100','5','505','0']
 p=io.BytesIO()
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr(KEY[:-4]+'.csv',','.join(r)+'\n')
  if extra is not None:z.writestr('evil.txt',extra)
 b=p.getvalue();return b,(digest(b)+'  '+KEY).encode()

def main():
 # date from URL must agree; obtain correct start/close from parser.
 info=parse_url(URL); start=info['start_ms'];duration=PERIOD['1d']
 base=[str(start),'100','102','99','101','11',str(start+duration-1),'1111','100','5','505','0']
 good,check=create(base)
 assert verify_raw_zip(URL,good,check)['bars']==1
 counts={};unexpected=[]
 def run(label,b,c,u=URL):
  try:verify_raw_zip(u,b,c)
  except D04Rejected as e:counts[label]=counts.get(label,0)+1
  else:unexpected.append(label)
 for i in range(60):
  b=bytearray(good);b[len(b)//2+i%4]^=(1+i)%255 or 1
  run('ZIP_BYTES_CHANGED_SAME_CHECKSUM',bytes(b),check)
 for i in range(40):
  b,ck=create(base[:6]+[str(start+duration-1+i+1)]+base[7:])
  run('WRONG_KLINE_DATE_EVEN_WITH_NEW_CHECKSUM',b,ck)
 for i in range(40):
  u=URL.replace('/futures/um/','/spot/') if i%2 else URL.replace('/futures/um/','/futures/cm/')
  run('SPOT_OR_COINM_MASQUERADE',good,check,u)
 for i in range(30):
  c=(digest(good)+'  WRONG'+str(i)+'.zip').encode()
  run('FORGED_CHECKSUM_NAME',good,c)
 for i in range(30):
  b,ck=create(base,extra='Z'*i)
  run('INJECTED_ZIP_MEMBER',b,ck)
 out={'status':'PASS' if not unexpected and sum(counts.values())==200 else 'FAIL',
      'negative_cases':sum(counts.values()),'counts':counts,'unexpected_acceptance':unexpected,
      'counterexample':{'both_zip_and_checksum_forged':'LOCAL_CHECKSUM_CAN_STILL_VERIFY',
                        'conclusion':'offline checksum is integrity, not independent Binance authentication'}}
 if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
