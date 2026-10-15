"""B1/C04: synthetic negative controls for real-archive C08 receipt to B1 bridge.

Fixtures contain fabricated but D04-shape-valid 96-row daily Binance-style
ZIPs. A copied C08 receipt is replaced in TEMP DIRECTORY only and NEVER
treated as actual Binance provenance. A separate CI HTTPS test uses the real
unchanged Git-pinned C08 receipt and original bytes.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,io,json,sys,tempfile,unittest,zipfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT.parent/"mtf-course-v05"/"src"))

from course_primitives_v05 import Bar
from strict_event_lineage_d03 import CausalEvent,EventLedger
from poi_price_lineage_b1 import ZoneReference,BarWitness,bar_digest
from c08_source_bound_poi_b1 import (
    C08WitnessRejected,c08_attested_bar,link_c08_test,link_c08_vc
)

TF=900_000
START=int(dt.datetime(2026,10,1,tzinfo=dt.timezone.utc).timestamp()*1000)
URL="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-10-01.zip"
FILE="BTCUSDT-15m-2026-10-01.csv"
RULE="https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view"

def row(i):
    start=START+i*TF
    if i==0:price=("100","103","99","101")
    elif i==1:price=("101","104","100","102")
    elif i==2:price=("105","107","104","106")
    else:price=("106","108","105","107")
    return [str(start),*price,"10",str(start+TF-1),"1000","25","4","400","0"]

def make_zip(*,poison=None):
    allrows=[row(i) for i in range(96)]
    if poison is not None:
        poison(allrows)
    bio=io.StringIO()
    csv.writer(bio,lineterminator="\n").writerows(allrows)
    raw=bio.getvalue().encode("utf8")
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(FILE,raw)
    zipbytes=buff.getvalue()
    name="BTCUSDT-15m-2026-10-01.zip"
    checksum=(hashlib.sha256(zipbytes).hexdigest()+" *"+name+"\n").encode()
    return zipbytes,checksum,hashlib.sha256(raw).hexdigest()

def bar(i):
    v=row(i)
    return Bar(int(v[0]),int(v[6]),float(v[1]),float(v[2]),float(v[3]),float(v[4]),"15m") if False else Bar(
        int(v[0]),int(v[6])+1,float(v[1]),float(v[2]),float(v[3]),float(v[4]),"15m")

def ev(uid,kind,b,parents=(),evidence=()):
    return CausalEvent(uid,kind,"BTCUSDT","BINANCE","USDM_FUTURES","15m",b.start,b.end,b.end,parents,evidence or (uid,))

def setup_ledger():
    b0,b1,b2=bar(0),bar(1),bar(2)
    g=EventLedger()
    g.add(ev("root","SOURCE",b0,evidence=("root",)))
    g.add(ev("poi","POI",b0,("root",),("rule-source",)))
    g.add(ev("test_source","SOURCE",b1,evidence=(bar_digest(b1),)))
    g.add(ev("test","TEST",b1,("poi",),("test_source",)))
    g.add(ev("vc_source","SOURCE",b2,evidence=(bar_digest(b2),)))
    g.add(ev("vc","VC",b2,("test",),("vc_source",)))
    zone=ZoneReference("poi","root",RULE,"LONG","15m",99,100,b0.end,"BTCUSDT","BINANCE","USDM_FUTURES")
    tw=BarWitness("test_source","test",b1,"BTCUSDT","BINANCE","USDM_FUTURES","LONG")
    vw=BarWitness("vc_source","vc",b2,"BTCUSDT","BINANCE","USDM_FUTURES","LONG")
    return g,zone,tw,vw

class C08ArchiveWitnessContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.aggregate=json.loads((ROOT/"evidence"/"c08"/"C08_315_AGGREGATE.json").read_text())
        self.receipts=json.loads((ROOT/"evidence"/"c08"/"C08_BTCUSDT_63_RECEIPTS.json").read_text())
        self.blob,self.checksum,self.csvsha=make_zip()
        self.receipts["receipts"][0]["zip_sha256"]=hashlib.sha256(self.blob).hexdigest()
        self.receipts["receipts"][0]["raw_csv_sha256"]=self.csvsha
        self._save()
        self.g,self.zone,self.test,self.vc=setup_ledger()
    def _save(self):
        (self.root/"C08_315_AGGREGATE.json").write_text(json.dumps(self.aggregate))
        (self.root/"C08_BTCUSDT_63_RECEIPTS.json").write_text(json.dumps(self.receipts))
    def attest(self,witness=None,blob=None,checksum=None):
        return c08_attested_bar(witness or self.test,
            self.blob if blob is None else blob,
            self.checksum if checksum is None else checksum,
            receipt_dir=self.root)

    def test_full_archive_matches_one_exact_test_bar(self):
        p=self.attest()
        self.assertEqual(p.bar_time,self.test.bar.start)
        self.assertEqual(p.witness.bar,self.test.bar)
        self.assertEqual(p.readiness,"NOT_TRADE_READY")

    def test_technical_poilevel_test_with_c08_bar(self):
        p=link_c08_test(self.g,self.zone,self.test,self.test.bar.end,
                        self.blob,self.checksum,receipt_dir=self.root)
        self.assertEqual(p.readiness,"NOT_TRADE_READY")
        self.assertIn("FIRSTNESS_UNPROVEN",p.event.relation)

    def test_technical_vc_on_same_attested_zip(self):
        p=link_c08_vc(self.g,self.zone,self.test,self.vc,self.vc.bar.end,
                      self.blob,self.checksum,self.blob,self.checksum,receipt_dir=self.root)
        self.assertEqual(p.readiness,"NOT_TRADE_READY")
        self.assertIn("SEMANTICS_UNKNOWN",p.event.relation)

    def test_wrong_price_even_when_lineage_sha_can_be_self_asserted(self):
        altered=replace(self.test,bar=Bar(self.test.bar.start,self.test.bar.end,
                   101,104,100,103,"15m"))
        with self.assertRaisesRegex(C08WitnessRejected,"OBSERVED_OHLC_DIFFERS_FROM_RAW_C08"):
            self.attest(witness=altered)

    def test_wrong_time_in_same_daily_archive_is_rejected(self):
        other=replace(self.test,bar=Bar(START+96*TF,START+97*TF,101,104,100,102,"15m"))
        with self.assertRaisesRegex(C08WitnessRejected,"C08_ARCHIVE_COVERAGE_NOT_UNIQUE"):
            self.attest(witness=other)

    def test_forged_zip_same_host_checksum_cannot_override_pinned_receipt(self):
        changed,c,sha=make_zip(poison=lambda rows:rows[1].__setitem__(4,"103"))
        with self.assertRaisesRegex(C08WitnessRejected,"SOURCE_ARCHIVE_DIFFERS_FROM_LOCKED_C08"):
            self.attest(blob=changed,checksum=c)

    def test_old_checksum_with_modified_zip_rejected(self):
        changed,c,sha=make_zip(poison=lambda rows:rows[1].__setitem__(4,"103"))
        with self.assertRaisesRegex(C08WitnessRejected,"RAW_ZIP_OR_CHECKSUM_REJECTED"):
            self.attest(blob=changed,checksum=self.checksum)

    def test_fake_c08_approval_mark_is_rejected(self):
        self.receipts["receipts"][0]["normalized_all_11_columns_matched"]=False
        self._save()
        with self.assertRaisesRegex(C08WitnessRejected,"UNVERIFIED_C08_RECEIPT"):
            self.attest()

    def test_spot_witness_rejected(self):
        bad=replace(self.test,market="SPOT")
        with self.assertRaisesRegex(C08WitnessRejected,"NOT_BINANCE_USDM_FUTURES"):
            self.attest(witness=bad)

    def test_untrusted_venue_rejected(self):
        with self.assertRaisesRegex(C08WitnessRejected,"NOT_BINANCE_USDM_FUTURES"):
            self.attest(witness=replace(self.test,venue="KRAKEN"))

    def test_foreign_symbol_not_part_of_c08(self):
        with self.assertRaisesRegex(C08WitnessRejected,"SYMBOL_OR_TF_NOT_IN_C08"):
            self.attest(witness=replace(self.test,symbol="DOGEUSDT"))

    def test_c08_receipt_duplicate_url_rejected(self):
        self.receipts["receipts"][1]["url"]=self.receipts["receipts"][0]["url"]
        self._save()
        with self.assertRaisesRegex(C08WitnessRejected,"DUPLICATE_C08_RECEIPT"):
            self.attest()

    def test_c08_all_315_global_declared_cannot_be_changed(self):
        self.aggregate["verified_archives"]=314
        self._save()
        with self.assertRaisesRegex(C08WitnessRejected,"INCOMPLETE_C08_GLOBAL_ACCEPTANCE"):
            self.attest()

    def test_c08_symbol_counts_cannot_be_changed(self):
        self.receipts["selected_sources"]=62
        self._save()
        with self.assertRaisesRegex(C08WitnessRejected,"INCOMPLETE_C08_SYMBOL_RECEIPTS"):
            self.attest()

    def test_c08_wrong_normalized_csv_digest(self):
        self.receipts["receipts"][0]["raw_csv_sha256"]="0"*64
        self._save()
        with self.assertRaisesRegex(C08WitnessRejected,"SOURCE_ARCHIVE_DIFFERS_FROM_LOCKED_C08"):
            self.attest()

    def test_archive_member_renaming_fails_closed(self):
        dst=io.BytesIO()
        with zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("unrelated.csv",b"x"*200)
        changed=dst.getvalue()
        checksum=(hashlib.sha256(changed).hexdigest()+" *BTCUSDT-15m-2026-10-01.zip\n").encode()
        with self.assertRaisesRegex(C08WitnessRejected,"RAW_ZIP_OR_CHECKSUM_REJECTED"):
            self.attest(blob=changed,checksum=checksum)

    def test_wrong_vc_bar_price_is_not_approved(self):
        forged=replace(self.vc,bar=Bar(self.vc.bar.start,self.vc.bar.end,105,107,104,105,"15m"))
        with self.assertRaisesRegex(C08WitnessRejected,"OBSERVED_OHLC_DIFFERS_FROM_RAW_C08"):
            link_c08_vc(self.g,self.zone,self.test,forged,self.vc.bar.end,
                        self.blob,self.checksum,self.blob,self.checksum,receipt_dir=self.root)

    def test_invalidation_after_test_cannot_resurrect_when_data_authentic(self):
        self.g.add(ev("invalidation","INVALIDATION",bar(3),("poi",),("invalid",)))
        with self.assertRaisesRegex(ValueError,"POI_CAUSALLY_INVALIDATED"):
            link_c08_test(self.g,self.zone,self.test,bar(3).end,
                          self.blob,self.checksum,receipt_dir=self.root)

    def test_future_as_of_witness_not_approved(self):
        with self.assertRaisesRegex(ValueError,"CHILD_OR_SOURCE_NOT_KNOWN_AS_OF"):
            link_c08_test(self.g,self.zone,self.test,self.test.bar.end-1,
                          self.blob,self.checksum,receipt_dir=self.root)

    def test_replay_same_c08_provenance_and_zero_trade(self):
        g=EventLedger.replay(self.g.export())
        a=link_c08_test(self.g,self.zone,self.test,self.test.bar.end,
                        self.blob,self.checksum,receipt_dir=self.root)
        b=link_c08_test(g,self.zone,self.test,self.test.bar.end,
                        self.blob,self.checksum,receipt_dir=self.root)
        self.assertEqual(a,b)
        self.assertEqual(a.event.readiness,"NOT_TRADE_READY")

if __name__=="__main__":
    unittest.main(verbosity=2)
