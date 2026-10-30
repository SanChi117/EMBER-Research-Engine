import io,csv,hashlib,unittest
from zipfile import ZipFile,ZIP_DEFLATED
from decimal import Decimal as D
import c114_aggtrades_source_arbitration as a

def fake(lines=None,bad=False):
    stream=io.StringIO();w=csv.writer(stream)
    w.writerow(["agg_trade_id","price","quantity","first_trade_id","last_trade_id","timestamp","maker"])
    for row in (lines if lines is not None else
                [(1,100,6,100,101,a.FOCUS_START,"false"),
                 (2,101,4,102,103,a.FOCUS_START+1,"true")]):
        w.writerow(row)
    buff=io.BytesIO()
    with ZipFile(buff,"w",compression=ZIP_DEFLATED) as z:
        z.writestr(a.STEM+".csv",stream.getvalue().encode())
    blob=buff.getvalue()
    digest=hashlib.sha256(blob).hexdigest()
    url=a.BASE+"BNBUSDT/"+a.STEM+".zip"
    return lambda u:{url:blob,url+".CHECKSUM":(("0"*64 if bad else digest)+"  "+a.STEM+".zip").encode()}[u]

class AggTradeEvidenceTests(unittest.TestCase):
    def test_aggregated_quantity_is_additive_and_trade_counts_separate(self):
        b,r=a.source(fetch=fake())
        self.assertEqual(b[54]["quantity"],D(10))
        self.assertEqual(b[54]["agg_rows"],2)
        self.assertEqual(b[54]["first_trade_count_approx"],4)
        self.assertTrue(r["provider_checksum_verified"])
    def test_invalid_provider_checksum_rejected(self):
        with self.assertRaises(a.TradeEvidenceError):a.source(fetch=fake(bad=True))
    def test_trade_outside_day_rejected(self):
        x=[(1,100,6,100,101,a.END,"false")]
        with self.assertRaises(a.TradeEvidenceError):a.source(fetch=fake(x))
    def test_decreasing_aggregate_id_rejected(self):
        x=[(2,100,6,100,101,a.FOCUS_START,"false"),
           (1,101,4,102,103,a.FOCUS_START+1,"true")]
        with self.assertRaises(a.TradeEvidenceError):a.source(fetch=fake(x))
if __name__=="__main__":unittest.main()
