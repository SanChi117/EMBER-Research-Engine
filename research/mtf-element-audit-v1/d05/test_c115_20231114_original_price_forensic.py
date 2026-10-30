import unittest
from decimal import Decimal as D
from types import SimpleNamespace as NS
from c89_original_native5m_adaptation_backtest import Bar
import c115_20231114_original_3m5m_price_mismatch_forensic as x

def make():
    a=tuple(NS(start_ms=x.DAY_MS+i*180000,
               known_ms=x.DAY_MS+(i+1)*180000,
               open=D(".11892"),high=D(".11935"),low=D(".11851"),
               close=D(".11898"),volume=D(3)) for i in range(480))
    b=tuple(Bar(x.DAY_MS+j*300000,D(".11892"),D(".11935"),D(".11851"),
                D(".11898"),D(5)) for j in range(288))
    return a,b

class C115SourceForensicTests(unittest.TestCase):
    def test_exact_96_original_buckets(self):
        a,b=make()
        z=x.compare("ALGOUSDT",a,b)
        self.assertEqual(z["15m_count"],96)
        self.assertEqual(z["price_mismatch_count"],0)
    def test_original_5m_high_extra_is_flagged_with_known_timestamp(self):
        a,b=make();b=list(b)
        k=3*46
        b[k]=Bar(b[k].open_ms,b[k].o,D(".11940"),b[k].l,b[k].c,b[k].volume)
        z=x.compare("ALGOUSDT",a,tuple(b))
        self.assertEqual(z["price_mismatch_count"],1)
        self.assertEqual(z["original_15m_price_mismatches"][0]["timestamp_ms"],x.TARGET_MS)
        self.assertEqual(z["original_15m_price_mismatches"][0]["price_3m_5m_max_abs_difference"],"0.00005")
    def test_wrong_original_daily_length_rejected(self):
        a,b=make()
        with self.assertRaises(ValueError):x.compare("ALGOUSDT",a[:-1],b)
if __name__=="__main__":unittest.main()
