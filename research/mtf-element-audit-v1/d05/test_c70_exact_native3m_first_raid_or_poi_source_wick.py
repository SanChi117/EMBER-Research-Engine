"""C70 source SHA native3m first wick no invented owner VC/SL."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import BASE,H,Q,native,hours,review
from test_c69_exact_native15m_first_liquidity_raid_vs_poi_test import raid_source
from c16_c08_monthly_daily_htf_lineage import SEPT_START
from c21_native3m_source_bridge import Original3mRow,THREE
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import first_original_native15m_source_contact
from c70_exact_native3m_first_raid_or_poi_source_wick import original3m_first_wick_within_c69
SHA="b"*64
def rows(native15,wick_index=3):
    asof=native15[-1].known_at_ms
    lookup={z.start_ms:z for z in native15}
    result=[]
    for start in range(SEPT_START,asof,THREE):
        base=start//Q*Q
        z=lookup.get(base)
        if z is None:
            o=h=l=c=D(100);v=D(1)
        else:
            k=(start-base)//THREE
            o=z.open
            c=z.close if k==4 else z.open
            h=z.high if k==wick_index else max(o,c)
            l=z.low if k==wick_index else min(o,c)
            v=z.volume/D(5)
        result.append(Original3mRow("BTCUSDT",start,start+THREE,o,h,l,c,v,
                                    SHA+":"+str(start),SHA))
    return tuple(result)
def run(hh=None,nn=None,rr=None,source=None,wick=3):
    if hh is None:hh=hours()
    if nn is None:nn=native()
    if rr is None:rr=review(hh=hh,e1=(),e15=()) if hh==hours(raid=True) else review(hh=hh)
    if source is None:
        source=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
    return original3m_first_wick_within_c69(rr,source,nn,rows(nn,wick),as_of_ms=nn[-1].known_at_ms)
class C70Precise3mSource(unittest.TestCase):
    def test_first_original3m_raid_occurs_within_real_first_native15m(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr)
        self.assertEqual(x.source_status,"RAID_FIRST_ORIGINAL3M_WICK_ONLY_NOT_AUTHOR")
        self.assertEqual(x.actual_first_native3m_start_ms,BASE+21*Q+3*THREE)
        self.assertTrue(x.five_original3m_to_native15m_ohlcv_equal)
    def test_raid_first_3m_cannot_be_called_owner_1h_confirmed_before_1h_close(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr)
        self.assertLess(x.actual_first_native3m_closed_ms,x.earliest_source_claim_eligible_ms)
        self.assertEqual(x.earliest_source_claim_eligible_ms,BASE+6*H)
    def test_3m_earliest_wick_first_bar_of_15m(self):
        hh,nn=raid_source("first")
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr,wick=0)
        self.assertEqual(x.actual_first_native3m_start_ms,BASE+20*Q)
    def test_3m_first_wick_and_later_15m_body_close_are_separate(self):
        hh,nn=raid_source("body")
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr)
        self.assertEqual(x.source_status,"RAID_FIRST_ORIGINAL3M_WICK_ONLY_NOT_AUTHOR")
        self.assertTrue(x.actual_first_native3m_wick_only)
    def test_first_3m_source_body_close_below_liquidity(self):
        hh,nn=raid_source("body")
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr,wick=4)
        self.assertEqual(x.source_status,"RAID_FIRST_ORIGINAL3M_CLOSE_THROUGH_LEVEL_NOT_AUTHOR")
    def test_new1h_poi_first_original3m_wick_not_owner_valid(self):
        x=run()
        self.assertEqual(x.source_status,"NEW1H_POI_FIRST_ORIGINAL3M_WICK_TEST_NOT_AUTHOR_VALID")
        self.assertFalse(x.author_first_valid_poi_test)
        self.assertTrue(x.five_original3m_to_native15m_ohlcv_equal)
    def test_ambiguous_multiple_levels_not_promoted_to_3m_source_entry(self):
        hh,nn=raid_source("first",multi=True)
        rr=review(hh=hh,e1=(),e15=())
        x=run(hh,nn,rr,wick=0)
        self.assertEqual(x.source_status,"NO_C69_UNAMBIGUOUS_SOURCE_CONTACT")
        self.assertIsNone(x.actual_first_native3m_id)
    def test_original3m_wrong_price_high_detected_from_15m_parity(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=list(rows(nn));idx=(c69.first_exact_original15m_contact_start_ms-SEPT_START)//THREE
        raw[idx+3]=replace(raw[idx+3],high=D(120))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            original3m_first_wick_within_c69(rr,c69,nn,tuple(raw),as_of_ms=nn[-1].known_at_ms)
    def test_original3m_wrong_close_detected_from_15m_parity(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=list(rows(nn));idx=(c69.first_exact_original15m_contact_start_ms-SEPT_START)//THREE
        raw[idx+4]=replace(raw[idx+4],close=D(99))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            original3m_first_wick_within_c69(rr,c69,nn,tuple(raw),as_of_ms=nn[-1].known_at_ms)
    def test_original3m_wrong_volume_detected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=list(rows(nn));idx=(c69.first_exact_original15m_contact_start_ms-SEPT_START)//THREE
        raw[idx+2]=replace(raw[idx+2],volume=D(4))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            original3m_first_wick_within_c69(rr,c69,nn,tuple(raw),as_of_ms=nn[-1].known_at_ms)
    def test_original3m_sha_row_id_forgery_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=list(rows(nn));raw[0]=replace(raw[0],raw_id="NO")
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(rr,c69,nn,tuple(raw),as_of_ms=nn[-1].known_at_ms)
    def test_original3m_timestamp_gap_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=rows(nn)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(rr,c69,nn,raw[:10]+raw[11:],as_of_ms=nn[-1].known_at_ms)
    def test_original3m_unknown_source_symbol_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=list(rows(nn));raw[0]=replace(raw[0],symbol="ETHUSDT")
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(rr,c69,nn,tuple(raw),as_of_ms=nn[-1].known_at_ms)
    def test_source_15m_forged_bar_ID_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            original3m_first_wick_within_c69(rr,replace(c69,first_exact_original15m_contact_id="FAKE"),
                nn,rows(nn),as_of_ms=nn[-1].known_at_ms)
    def test_owner_stronghl_forgery_rejected(self):
        hh,nn=raid_source()
        rr=replace(review(hh=hh,e1=(),e15=()),author_stronghl=True)
        c69=first_original_native15m_source_contact(review(hh=hh,e1=(),e15=()),hh,nn,as_of_ms=nn[-1].known_at_ms)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(rr,c69,nn,rows(nn),as_of_ms=nn[-1].known_at_ms)
    def test_route_b_idm_forgery_rejected(self):
        hh,nn=raid_source()
        rr=replace(review(hh=hh,e1=(),e15=()),route_b_idm_used=True)
        c69=first_original_native15m_source_contact(review(hh=hh,e1=(),e15=()),hh,nn,as_of_ms=nn[-1].known_at_ms)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(rr,c69,nn,rows(nn),as_of_ms=nn[-1].known_at_ms)
    def test_owner_source_3m_candle_not_order_without_poi_validation(self):
        x=run()
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
        self.assertFalse(x.author_stronghl or x.author_volume_confirmation)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_asof_future_3m_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        raw=rows(nn)
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):
            original3m_first_wick_within_c69(rr,c69,nn,raw[:-1],as_of_ms=nn[-1].known_at_ms)
    def test_zero_preknown_source_level_not_accepted_as_raid(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        with self.assertRaisesRegex(ValueError,"BAD_PREKNOWN"):
            original3m_first_wick_within_c69(rr,replace(c69,preknown_level_price="0"),
                nn,rows(nn),as_of_ms=nn[-1].known_at_ms)
    def test_cross_symbol_parent_rejected(self):
        hh,nn=raid_source()
        rr=review(hh=hh,e1=(),e15=())
        c69=first_original_native15m_source_contact(rr,hh,nn,as_of_ms=nn[-1].known_at_ms)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            original3m_first_wick_within_c69(replace(rr,symbol="SOLUSDT"),c69,
                nn,rows(nn),as_of_ms=nn[-1].known_at_ms)
if __name__=="__main__":unittest.main()
