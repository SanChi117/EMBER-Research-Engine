#!/usr/bin/env python3
"""C08 new tests: reject a forged archive/manifest and row-level divergence."""
import hashlib
import io
import pathlib
import sys
import unittest
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'tools'))
from strict_vision_d04 import D04Rejected,parse_url
from verify_d04_full_manifest_c08 import (
    NORMALIZED, compare_verified_archive, unique_declared_sources
)

URL='https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-11.zip'
NAME='BTCUSDT-1d-2026-10-11.zip'
OPEN=1791676800000
CLOSE=1791763199999
DATA=[str(OPEN),'100','105','95','102','10',str(CLOSE),
      '1010','42','5','505','0']

def fixture(row=None):
    row=DATA if row is None else row
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr(NAME[:-4]+'.csv',','.join(row)+'\n')
    blob=out.getvalue()
    sha=hashlib.sha256(blob).hexdigest()
    checksum=f'{sha} *{NAME}\n'.encode()
    norm={OPEN:{key:value for key,value in zip(NORMALIZED,DATA[:11])}}
    return blob,checksum,{'url':URL,'sha256':sha,'rows':1},norm

class C08IndependentAttestation(unittest.TestCase):
    def test_valid_source_and_all_eleven_columns(self):
        b,c,entry,norm=fixture()
        x=compare_verified_archive(URL,b,c,entry,norm)
        self.assertEqual(x['rows'],1)
        self.assertTrue(x['normalized_all_11_columns_matched'])
        self.assertEqual(x['status'],'HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED')

    def test_modified_zip_with_old_checksum_is_rejected(self):
        b,c,entry,norm=fixture()
        changed=list(DATA);changed[4]='103'
        bad,_,_,_=fixture(changed)
        with self.assertRaisesRegex(D04Rejected,'ARCHIVE_CHECKSUM_MISMATCH'):
            compare_verified_archive(URL,bad,c,entry,norm)

    def test_modified_zip_even_with_matching_remote_checksum_but_old_manifest_is_rejected(self):
        b,c,entry,norm=fixture()
        changed=list(DATA);changed[4]='103'
        bad,new_checksum,_,_=fixture(changed)
        with self.assertRaisesRegex(D04Rejected,'LOCAL_MANIFEST_ZIP_SHA_DIFFERENCE'):
            compare_verified_archive(URL,bad,new_checksum,entry,norm)

    def test_modified_normalized_bar_is_rejected(self):
        b,c,entry,norm=fixture()
        norm[OPEN]['taker_buy_quote_volume']='506'
        with self.assertRaisesRegex(D04Rejected,'SOURCE_NORMALIZED_COLUMN_MISMATCH'):
            compare_verified_archive(URL,b,c,entry,norm)

    def test_missing_time_is_rejected(self):
        b,c,entry,norm=fixture()
        norm={}
        with self.assertRaisesRegex(D04Rejected,'SOURCE_BAR_NOT_IN_NORMALIZED'):
            compare_verified_archive(URL,b,c,entry,norm)

    def test_duplicate_manifest_source_is_rejected(self):
        _,_,entry,_=fixture()
        record={'symbol':'BTCUSDT','tf':'1d','sources':[entry,entry]}
        with self.assertRaisesRegex(D04Rejected,'DUPLICATE_SOURCE_URL'):
            unique_declared_sources([record])

    def test_reject_spot_and_bad_market_source(self):
        with self.assertRaisesRegex(D04Rejected,'WRONG_MARKET_OR_FILE_TYPE'):
            parse_url(URL.replace('/futures/um/','/spot/'))
        with self.assertRaises(D04Rejected):
            parse_url(URL.replace('data.binance.vision','not-binance.example'))

    def test_reject_wrong_symbol_series(self):
        _,_,entry,_=fixture()
        with self.assertRaisesRegex(D04Rejected,'MANIFEST_SOURCE_SERIES_MISMATCH'):
            unique_declared_sources([{'symbol':'ETHUSDT','tf':'1d','sources':[entry]}])

if __name__=='__main__':
    unittest.main(verbosity=2)
