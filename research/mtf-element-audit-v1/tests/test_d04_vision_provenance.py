#!/usr/bin/env python3
"""D04 negative acceptance, no market action or PnL."""
import hashlib,io,os,sys,tempfile,unittest,zipfile,json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_vision_d04 import *
from strict_vision_d04 import _SingleHostRedirect

BTC15='https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-10-11.zip'
BTC1D='https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-11.zip'

def sample_source(url=BTC15,*,replace_row=None,wrong_member=False,extra_member=False):
 s=parse_url(url);rows=[]
 for i in range(s['expected_rows']):
  tm=s['start_ms']+i*PERIOD[s['tf']]
  row=[str(tm),'100','102','99','101','11',str(tm+PERIOD[s['tf']]-1),'1111','100','5','505','0']
  if replace_row:row=replace_row(i,row)
  rows.append(','.join(row))
 content=('\n'.join(rows)+'\n').encode()
 f=io.BytesIO()
 with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('outside.csv' if wrong_member else s['filename'][:-4]+'.csv',content)
  if extra_member:z.writestr('attacker.txt','oh no')
 raw=f.getvalue(); checksum=(digest(raw)+'  '+s['filename']+'\n').encode()
 return raw,checksum

class TestVisionURL(unittest.TestCase):
 def test_valid_futures(self):
  x=parse_url(BTC15)
  self.assertEqual(x['expected_rows'],96)
  self.assertEqual(parse_url(BTC1D)['expected_rows'],1)
 def reject(self,url):
  with self.assertRaises(D04Rejected):parse_url(url)
 def test_spot(self):self.reject(BTC15.replace('/futures/um/','/spot/'))
 def test_coin_m(self):self.reject(BTC15.replace('/futures/um/','/futures/cm/'))
 def test_http(self):self.reject(BTC15.replace('https:','http:'))
 def test_evil_host(self):self.reject(BTC15.replace('data.binance.vision','data.binance.vision.evil.tld'))
 def test_unicode_hostname(self):self.reject(BTC15.replace('vision','visiоn'))
 def test_credentials(self):self.reject(BTC15.replace('https://','https://evil.tld@'))
 def test_port(self):self.reject(BTC15.replace('.vision/','.vision:443/'))
 def test_query(self):self.reject(BTC15+'?type=spot')
 def test_fragment(self):self.reject(BTC15+'#spot')
 def test_percent_path(self):self.reject(BTC15.replace('BTCUSDT','BTC%55SDT'))
 def test_backslash(self):self.reject(BTC15.replace('/15m/','\\15m/'))
 def test_symbol_filename_mismatch(self):self.reject(BTC15.replace('BTCUSDT-15m','ETHUSDT-15m'))
 def test_wrong_timeframe(self):self.reject(BTC15.replace('-15m-','-5m-'))
 def test_mismatched_timeframe(self):self.reject(BTC15.replace('/15m/','/1d/'))
 def test_bad_date(self):self.reject(BTC15.replace('2026-10-11','2026-02-30'))
 def test_date_granularity(self):self.reject(BTC15.replace('/daily/','/monthly/'))
 def test_bad_archive_suffix(self):self.reject(BTC15.replace('.zip','.csv'))
 def test_path_traversal(self):self.reject(BTC15.replace('BTCUSDT/15m','BTCUSDT/../15m'))
 def test_extra_slash(self):self.reject(BTC15.replace('/data/','//data/'))

class TestVisionArchive(unittest.TestCase):
 def setUp(self):self.a,self.chk=sample_source()
 def assert_code(self,code,raw=None,ck=None,url=BTC15):
  with self.assertRaises(D04Rejected) as ctx:verify_raw_zip(url,raw if raw is not None else self.a,ck if ck is not None else self.chk)
  self.assertEqual(ctx.exception.code,code)
 def test_accept(self):
  r=verify_raw_zip(BTC15,self.a,self.chk)
  self.assertEqual(r['bars'],96)
  self.assertEqual(r['status'],'SOURCE_CHECKSUM_AND_BARS_VERIFIED')
 def test_changed_content_without_checksum(self):self.assert_code('ARCHIVE_CHECKSUM_MISMATCH',raw=self.a+b'abc')
 def test_malformed_checksum(self):self.assert_code('INVALID_CHECKSUM_FORMAT_OR_NAME',ck=b'bad')
 def test_checksum_wrong_filename(self):self.assert_code('INVALID_CHECKSUM_FORMAT_OR_NAME',ck=self.chk.replace(b'BTCUSDT-15m',b'ETHUSDT-15m'))
 def test_changed_csv_with_recomputed_checksum_but_wrong_time(self):
  raw,chk=sample_source(replace_row=lambda i,r:[str(int(r[0])+900000)]+r[1:] if i==2 else r)
  self.assert_code('MISSING_OR_WRONG_DATE_KLINES',raw,chk)
 def test_hidden_member(self):
  raw,chk=sample_source(extra_member=True);self.assert_code('UNEXPECTED_ZIP_MEMBERS',raw,chk)
 def test_traversal_member(self):
  raw,chk=sample_source(wrong_member=True);self.assert_code('UNEXPECTED_ZIP_MEMBERS',raw,chk)
 def test_negative_volume(self):
  def neg(i,r):r[5]='-7' if i==3 else r[5];return r
  a,b=sample_source(replace_row=neg);self.assert_code('BAD_NUMERIC_5',a,b)
 def test_spot_with_good_local_sha(self):
  self.assert_code('WRONG_MARKET_OR_FILE_TYPE',url=BTC15.replace('/futures/um/','/spot/'))
 def test_empty_zip(self):
  raw=b'notzip';ck=(digest(raw)+'  BTCUSDT-15m-2026-10-11.zip').encode();self.assert_code('CORRUPT_ZIP',raw,ck)
 def test_missing_hour(self):
  def skip(i,r):r[0]=str(int(r[0])+900000) if i>=40 else r[0];return r
  a,b=sample_source(replace_row=skip);self.assert_code('MISSING_OR_WRONG_DATE_KLINES',a,b)
 def test_checksum_recomputed_can_be_forged(self):
  # Crucial limitations: a self-generated .CHECKSUM is not source authenticity.
  r=verify_raw_zip(BTC15,self.a,self.chk)
  self.assertEqual(r['status'],'SOURCE_CHECKSUM_AND_BARS_VERIFIED')
  self.assertNotIn('HTTPS_BINANCE_VISION_HOST_AND_CHECKSUM',r.values())
 def test_redirect_to_evil_host(self):
  class Request:full_url=BTC15
  handler=_SingleHostRedirect()
  with self.assertRaises(D04Rejected):handler.redirect_request(Request(),None,302,'','','https://evil.example/abc.zip')

class TestOfflineManifest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.history=ROOT/'baselines/d04_history_2026'
  if not (cls.history/'manifest_vision.json').exists():raise unittest.SkipTest('Baseline archive absent')
 def test_manifest_integrity_not_authenticity(self):
  o=verify_offline_consolidated_manifest(self.history)
  self.assertEqual(o['series_verified'],10)
  self.assertEqual(o['total_bars'],98680)
  self.assertEqual(o['source_authenticity'],'NOT_ATTESTED_FROM_OFFLINE_MANIFEST')
 def test_manifest_spot_label_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=json.loads((self.history/'manifest_vision.json').read_text());m[0]['sources'][0]['url']=m[0]['sources'][0]['url'].replace('/futures/um/','/spot/')
   (p/'manifest_vision.json').write_text(json.dumps(m))
   # Avoid copying CSVs; provenance fail occurs first in first manifest entry.
   (p/(m[0]['symbol']+'_'+m[0]['tf']+'.csv')).write_bytes((self.history/(m[0]['symbol']+'_'+m[0]['tf']+'.csv')).read_bytes())
   with self.assertRaises(D04Rejected) as e:verify_offline_consolidated_manifest(p)
   self.assertEqual(e.exception.code,'WRONG_MARKET_OR_FILE_TYPE')
 def test_normalized_csv_mutation_detected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);m=json.loads((self.history/'manifest_vision.json').read_text());(p/'manifest_vision.json').write_bytes((self.history/'manifest_vision.json').read_bytes())
   path=m[0]['symbol']+'_'+m[0]['tf']+'.csv'
   raw=bytearray((self.history/path).read_bytes());raw[-5]^=1;(p/path).write_bytes(raw)
   with self.assertRaises(D04Rejected) as e:verify_offline_consolidated_manifest(p)
   self.assertEqual(e.exception.code,'NORMALIZED_CSV_SHA_MISMATCH')

if __name__=='__main__':unittest.main()
