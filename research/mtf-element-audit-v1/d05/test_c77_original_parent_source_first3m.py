"""C77 source-only fixtures (all SYNTHETIC, not Binance observations)."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import Original3mRow,THREE
from c62_academic_snr_rb_imb_liquidity_source_separation import SourceBlockCase,PreknownGap
from c77_original_parent_source_first3m import inspect,C77Rejected,summarize
T=1788220800000
S="a"*64
def candles():
    ranges=[(95,97,96),(98,99,99),(99,103,102),(94,98,97),(99,105,103),(106,110,108)]
    return tuple(Original3mRow("BTCUSDT",T+i*THREE,T+(i+1)*THREE,D(str(c)),D(str(h)),D(str(l)),D(str(c)),D("1"),S+":"+str(T+i*THREE),S) for i,(l,h,c) in enumerate(ranges))
def parent(kind="RB"):
    b=candles()
    d={"symbol":"BTCUSDT","side":"LONG","source_1h_poi_kind":"1H_NEW_VC_"+kind+"_SOURCE",
       "source_1h_poi_created_at_ms":T,"source_1h_poi_bottom":"100","source_1h_poi_top":"104",
       "original_first_source3m_touch_closed_ms":b[2].known_ms,"original_first_source3m_touch_id":b[2].raw_id,
       "first_source15m_event_pattern_start_ms":b[-1].start_ms,"episodes_before_first_15m_pattern":2,
       "second_visit_original3m_id":b[4].raw_id,
       "state":"NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID",
       "readiness":"NOT_TRADE_READY","orders":[],"fills":[],"trades":[]}
    for k in ("author_15m_trigger","author_15m_vc","author_5m_vc","author_entry","author_stronghl","author_structural_sl","author_1h_poi_valid_first_test","route_b_idm_used","route_c_raid_bos_used"):
        d[k]=False
    return d
def catalog(kind="RB",cls=None):
    if kind=="IMB":return (), (PreknownGap("LONG","100","104",T,(S+":1",)*3),)
    status=cls or ("RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY" if kind=="RB" else "SNR_ACCEPTED_CLOSE_WITH_SOURCE_IMB_PROXY")
    b=SourceBlockCase("RB" if kind=="RB" else "SNR_OR_MB","LONG",T-3600000,T,S+":1",S+":2",None if kind=="RB" else S+":3","SSL",None,"LIQUIDITY_SOURCE_PROXY",status)
    return (b,),()
def run(p=None,kind="RB",blocks=None,gaps=None,bars=None,asof=None):
    v=bars if bars is not None else candles()
    a,b=catalog(kind)
    return inspect(p if p is not None else parent(kind), a if blocks is None else blocks,
                   b if gaps is None else gaps,v,v[-1].known_ms if asof is None else asof)
class TestC77(unittest.TestCase):
    def test_rb(self):
        x=run();self.assertEqual(x[0],"RB");self.assertEqual(x[3],2)
    def test_snr(self):
        self.assertEqual(run(kind="SNR")[1],"SOURCE_SNR_CONFIRMED_WORK")
    def test_imb(self):
        self.assertEqual(run(kind="IMB")[1],"SOURCE_1H_IMB_GAP_ONLY")
    def test_count(self):
        self.assertEqual(summarize([run(),run(kind="SNR")])["trades"],0)
    def test_no_parent(self):
        x=parent();x.update(source_1h_poi_kind=None,state="NOT_NEW_1H_POI_SOURCE_BRANCH")
        self.assertEqual(run(p=x)[0],"NO_PARENT")
    def test_no_touch(self):
        x=parent();x.update(state="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH",
         original_first_source3m_touch_closed_ms=None,original_first_source3m_touch_id=None)
        b=tuple(replace(v,low=D("90"),high=D("99"),open=D("95"),close=D("96")) for v in candles())
        self.assertIsNone(run(p=x,bars=b)[2])
    def test_single_visit(self):
        x=parent();v=candles();x.update(first_source15m_event_pattern_start_ms=v[4].start_ms,
           episodes_before_first_15m_pattern=1,second_visit_original3m_id=None,
           state="NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID")
        self.assertEqual(run(p=x)[3],1)
def forbidden(change):
    def test(self):
        x=parent();x.update(change)
        with self.assertRaises(C77Rejected):run(p=x)
    return test
for name,d in {
    "author_vc":{"author_15m_vc":True},"trigger":{"author_15m_trigger":True},
    "author_5m":{"author_5m_vc":True},"stronghl":{"author_stronghl":True},
    "route_b":{"route_b_idm_used":True},"route_c":{"route_c_raid_bos_used":True},
    "trades":{"trades":["BUY"]},"ready":{"readiness":"READY"},
    "wrong_symbol":{"symbol":"XYZUSDT"},"bad_side":{"side":"NEUTRAL"},
    "unknown_kind":{"source_1h_poi_kind":"UNKNOWN"},
    "future_creation":{"source_1h_poi_created_at_ms":T+100000000},
    "bad_price":{"source_1h_poi_bottom":"NaN"},
    "inverted_price":{"source_1h_poi_bottom":"200"},
    "wrong_touch":{"original_first_source3m_touch_closed_ms":T+THREE},
    "wrong_id":{"original_first_source3m_touch_id":"fake"},
    "faked_revisit":{"episodes_before_first_15m_pattern":1},
    "false_repeat":{"second_visit_original3m_id":"fake"},
    "future_pattern":{"first_source15m_event_pattern_start_ms":T+100000000},
    "bad_pattern":{"first_source15m_event_pattern_start_ms":T+THREE},
}.items():setattr(TestC77,"test_neg_"+name,forbidden(d))
class TestC77Adversarial(unittest.TestCase):
    def test_bare_rb_rejected(self):
        b,_=catalog(cls="RB_TWO_OPPOSITE_HOURLY_CANDLES_WITHOUT_VERIFIED_WICK_RAID")
        with self.assertRaises(C77Rejected):run(blocks=b)
    def test_mb_not_snr(self):
        b,_=catalog("SNR","MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION")
        with self.assertRaises(C77Rejected):run(kind="SNR",blocks=b)
    def test_double_match(self):
        b,_=catalog()
        with self.assertRaises(C77Rejected):run(blocks=(b[0],b[0]))
    def test_fake_c62_author(self):
        b,_=catalog()
        with self.assertRaises(C77Rejected):run(blocks=(replace(b[0],author_volume_confirmation=True),))
    def test_future_3m(self):
        v=candles()
        with self.assertRaises(C77Rejected):run(asof=v[-1].known_ms-1)
    def test_missing_bar(self):
        v=candles()
        with self.assertRaises(C77Rejected):run(bars=v[:1]+v[2:])
    def test_bad_gap_author(self):
        b,g=catalog("IMB")
        with self.assertRaises(C77Rejected):run(kind="IMB",gaps=(replace(g[0],status="AUTHOR"),))
if __name__=="__main__":unittest.main()
