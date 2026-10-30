import unittest
from decimal import Decimal as D
import c114_causal_4h_poi_native5m_contract as c

def bar(ms,tf,o=10,h=12,l=9,close=11):
    return c.Candle(ms,ms+tf,D(o),D(h),D(l),D(close),tf)

class C114CausalContractTests(unittest.TestCase):
    def test_3m_and_5m_must_be_independent(self):
        a=tuple(bar(i*c.M3,c.M3) for i in range(5))
        b=tuple(bar(i*c.M5,c.M5) for i in range(3))
        self.assertTrue(c.strict_cross_native(a,b,0,15*c.MINUTE))
    def test_native_5m_rejects_3m_resample(self):
        a=tuple(bar(i*c.M3,c.M3) for i in range(5))
        with self.assertRaises(c.SourceError):
            c.strict_cross_native(a,a,0,15*c.MINUTE)
    def test_5m_missing_candle_rejected(self):
        a=tuple(bar(i*c.M3,c.M3) for i in range(5))
        b=tuple(bar(i*c.M5,c.M5) for i in (0,2))
        with self.assertRaises(c.SourceError):c.strict_cross_native(a,b,0,15*c.MINUTE)
    def test_independent_sources_disagree_at_shared15m_rejected(self):
        a=tuple(bar(i*c.M3,c.M3) for i in range(5))
        b=tuple(bar(i*c.M5,c.M5,10,13,9,11) for i in range(3))
        with self.assertRaisesRegex(c.SourceError,"DISAGREEMENT"):
            c.strict_cross_native(a,b,0,15*c.MINUTE)
    def test_wrong_native_anchor_rejected(self):
        with self.assertRaises(c.SourceError):bar(1000,c.M5)
    def test_closed_pivot_only_after_right_two(self):
        prices=[10,11,15,11,9]
        rows=tuple(bar(i*c.M5,c.M5,8,x,6,8) for i,x in enumerate(prices))
        self.assertFalse(any(p.kind=="H" for p in c.closed_pivots(rows,4*c.M5)))
        found=c.closed_pivots(rows,5*c.M5)
        self.assertEqual(len([p for p in found if p.kind=="H"]),1)
        self.assertEqual(found[0].confirmed_ms,5*c.M5)
    def test_fvg_only_three_closed_contiguous_h4(self):
        rows=[bar(i*c.H4,c.H4,10,12,9,11) for i in range(3)]
        rows[2]=bar(2*c.H4,c.H4,14,16,13,15)
        poi=c.h4_fvg(rows)
        self.assertEqual((poi.side,poi.lower,poi.upper,poi.created_ms),("LONG",D(12),D(13),3*c.H4))
    def test_false_fvg_from_missing_middle_candle_fails(self):
        with self.assertRaises(c.SourceError):
            c.h4_fvg([bar(0,c.H4),bar(2*c.H4,c.H4),bar(3*c.H4,c.H4)])
    def test_first_touch_cannot_precede_parent_formation(self):
        poi=c.POI("LONG",D(9),D(10),c.H4,"p")
        with self.assertRaises(c.SourceError):c.first_touch_asof(poi,(),c.H4-1)
    def test_first_touch_requires_closed_native3m(self):
        poi=c.POI("LONG",D(9),D(10),0,"p")
        rows=(bar(0,c.M3,11,12,9,11),)
        self.assertIsNone(c.first_touch_asof(poi,rows,c.M3-1))
        self.assertEqual(c.first_touch_asof(poi,rows,c.M3),c.M3)
    def test_choch_requires_two_pretouch_pivots_each_kind(self):
        poi=c.POI("LONG",D(9),D(10),0,"p")
        rows=(bar(0,c.M5,11,14,10,13),)
        self.assertEqual(c.choch_after_touch(poi,0,rows,(),c.SIX_H)[1],"NO_PRETOUCH_STRUCTURAL_SOURCE")
    def test_closed_choch_must_be_after_touch(self):
        touch=60*c.M5
        pivots=(c.Pivot("H",4*c.M5,8*c.M5,D(16)),
                c.Pivot("H",12*c.M5,16*c.M5,D(13)),
                c.Pivot("L",6*c.M5,10*c.M5,D(8)),
                c.Pivot("L",14*c.M5,18*c.M5,D(7)))
        poi=c.POI("LONG",D(9),D(10),0,"p")
        before=bar(59*c.M5,c.M5,10,15,9,14)
        after=bar(60*c.M5,c.M5,10,15,9,14)
        when,why=c.choch_after_touch(poi,touch,(before,after),pivots,touch+c.SIX_H)
        self.assertEqual(why,"CONFIRMED_CHoCH")
        self.assertEqual(when,61*c.M5)
    def test_future_choch_not_counted(self):
        touch=60*c.M5
        pivots=(c.Pivot("H",4*c.M5,8*c.M5,D(16)),
                c.Pivot("H",12*c.M5,16*c.M5,D(13)),
                c.Pivot("L",6*c.M5,10*c.M5,D(8)),
                c.Pivot("L",14*c.M5,18*c.M5,D(7)))
        poi=c.POI("LONG",D(9),D(10),0,"p")
        late=bar(133*c.M5,c.M5,10,15,9,14)
        self.assertEqual(c.choch_after_touch(poi,touch,(late,),pivots,touch+c.SIX_H)[1],"NO_CHoCH_BY_LANDMARK")
    def test_no_past_pivot_inference_from_future(self):
        touch=60*c.M5
        future=(c.Pivot("H",4*c.M5,8*c.M5,D(16)),
                c.Pivot("H",12*c.M5,61*c.M5,D(13)),
                c.Pivot("L",6*c.M5,10*c.M5,D(8)),
                c.Pivot("L",14*c.M5,18*c.M5,D(7)))
        poi=c.POI("LONG",D(9),D(10),0,"p")
        self.assertEqual(c.choch_after_touch(poi,touch,(bar(60*c.M5,c.M5,10,15,9,14),),future,touch+c.SIX_H)[1],"NO_PRETOUCH_STRUCTURAL_SOURCE")
    def test_landmark_requires_next_actual_3m_open(self):
        rows=(bar(0,c.M3),bar(c.M3,c.M3))
        self.assertEqual(c.landmark_3m_open(rows,c.M3),D(10))
        with self.assertRaises(c.SourceError):c.landmark_3m_open(rows,2*c.M3)
    def test_dont_invent_dealing_range(self):
        self.assertEqual(c.premium_discount((),0,D(11))[0],"NO_RANGE")
    def test_confirmed_range_midpoint(self):
        pivots=(c.Pivot("L",0,10,D(10)),c.Pivot("H",0,10,D(20)))
        self.assertEqual(c.premium_discount(pivots,10,D(12))[0],"DISCOUNT")
        self.assertEqual(c.premium_discount(pivots,10,D(17))[0],"PREMIUM")
        self.assertEqual(c.premium_discount(pivots,9,D(17))[0],"NO_RANGE")

if __name__=="__main__":unittest.main()
