import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from course_primitives_v05 import (Bar,Pivot,Raid,POI,Evidence,StrongHL,confirmed_pivots,
 confirmed_hourly_raids,bos_after_raid,confirmed_strong_hl,select_idm,PoiLifecycle,TF_MS,confirmed_imb,imbs_after_trigger,quote_bos_next_open)

def b(tf,i,o=100,h=101,l=99,c=100):
    step=TF_MS[tf]
    return Bar(i*step,(i+1)*step,o,h,l,c,tf)

class CoursePrimitivesTests(unittest.TestCase):
    def test_pivot_only_known_after_right_confirmation(self):
        bs=[b('3m',i,h=v,l=90) for i,v in enumerate([100,101,106,104,103,102])]
        self.assertEqual(confirmed_pivots(bs[:4]),[])
        piv=confirmed_pivots(bs[:5]);self.assertEqual(len(piv),1)
        self.assertEqual(piv[0].origin,2*TF_MS['3m']);self.assertEqual(piv[0].known,5*TF_MS['3m'])
    def test_pivot_not_strong_without_source_evidence(self):
        with self.assertRaises(ValueError): confirmed_strong_hl(side='LONG',extreme=90,origin=0,
                 contact=Evidence('POI_CONTACT','LONG',1,90,'p'),confirmation=Evidence('PIVOT','LONG',2,90,'x'))
    def test_stronghl_needs_contact_before_vc(self):
        c=Evidence('LIQUIDITY_CONTACT','LONG',200,92,'raid');vc=Evidence('VC_IMB','LONG',300,93,'vc')
        strong=confirmed_strong_hl(side='LONG',extreme=91,origin=100,contact=c,confirmation=vc)
        self.assertEqual(strong.known,300)
        with self.assertRaises(ValueError):confirmed_strong_hl(side='LONG',extreme=91,origin=100,contact=vc,confirmation=c)
        with self.assertRaises(ValueError):confirmed_strong_hl(side='LONG',extreme=91,origin=100,contact=c,confirmation=Evidence('BOS','LONG',100,93,'early'))
    def test_raid_requires_wick_above_and_reclaim(self):
        bs=[b('1h',i) for i in range(9)]
        bs[7]=b('1h',7,102,108,98,104)
        p=Pivot('pool','1h','HIGH',105,1*TF_MS['1h'],5*TF_MS['1h'])
        raids=confirmed_hourly_raids(bs,[p]);self.assertEqual(len(raids),1)
        self.assertEqual(raids[0].side,'SHORT');self.assertEqual(raids[0].known,8*TF_MS['1h'])
    def test_raid_body_close_through_no_reclaim(self):
        bs=[b('1h',i) for i in range(9)]
        bs[7]=b('1h',7,103,108,99,106)
        p=Pivot('pool','1h','HIGH',105,1*TF_MS['1h'],5*TF_MS['1h'])
        self.assertEqual(confirmed_hourly_raids(bs,[p]),[])
    def test_raid_must_be_fresh(self):
        bs=[b('1h',i) for i in range(33)];bs[31]=b('1h',31,102,108,98,104)
        p=Pivot('old','1h','HIGH',105,0,3*TF_MS['1h'])
        self.assertEqual(confirmed_hourly_raids(bs,[p]),[])
    def test_raid_first_fractal_only(self):
        bs=[b('1h',i) for i in range(10)]
        bs[7]=b('1h',7,102,108,98,104);bs[8]=b('1h',8,102,107,98,103)
        p=Pivot('pool','1h','HIGH',105,1*TF_MS['1h'],5*TF_MS['1h'])
        self.assertEqual(len(confirmed_hourly_raids(bs,[p])),1)
    def _bos_setup(self,tf='3m'):
        step=TF_MS[tf];hour=TF_MS['1h'];start=2*hour
        base=start//step
        bs=[b(tf,base+i,o=100,h=103,l=98,c=100) for i in range(10)]
        bs[5]=b(tf,base+5,o=99,h=100,l=95,c=96)
        # source BOS pivot low 97 and raid high 108: structurally below raid
        p=Pivot('low',tf,'LOW',97,start-step,2*hour)
        raid=Raid('r','SHORT','pool',105,108,hour,2*hour)
        return bs,p,raid
    def test_bos_requires_actual_3m_close(self):
        bs,p,r=self._bos_setup();rs=bos_after_raid(bs,[p],[r]);self.assertEqual(len(rs),1)
        self.assertEqual(rs[0].tf,'3m');self.assertEqual(rs[0].known,bs[5].end)
    def test_bos_prefix_causality(self):
        bs,p,r=self._bos_setup()
        for n in range(1,6):self.assertEqual(bos_after_raid(bs[:n],[p],[r]),[])
        self.assertEqual(len(bos_after_raid(bs[:6],[p],[r])),1)
    def test_bos_must_wait_for_raid_confirmation(self):
        bs,p,r=self._bos_setup();late=Raid('r','SHORT','pool',105,108,2*TF_MS['1h'],3*TF_MS['1h'])
        self.assertEqual(bos_after_raid(bs,[p],[late]),[])
    def test_bos_rejects_15m_proxy(self):
        with self.assertRaises(ValueError):bos_after_raid([b('15m',i) for i in range(3)],[],[])
    def test_bos_rejects_wick_only_break(self):
        bs,p,r=self._bos_setup();bs[5]=b('3m',bs[5].start//TF_MS['3m'],o=99,h=100,l=95,c=99)
        self.assertEqual(bos_after_raid(bs,[p],[r]),[])
    def test_bos_rejects_new_higher_extreme_before_confirmation(self):
        bs,p,r=self._bos_setup();bs[3]=b('3m',bs[3].start//TF_MS['3m'],o=100,h=109,l=98,c=100)
        self.assertEqual(bos_after_raid(bs,[p],[r]),[])
    def test_bos_5m_has_separate_route(self):
        bs,p,r=self._bos_setup('5m');self.assertEqual(len(bos_after_raid(bs,[p],[r])),1)
    def test_bos_quote_uses_next_open_and_1h_fta(self):
        bs,p,r=self._bos_setup();bos=bos_after_raid(bs,[p],[r])[0]
        target=Pivot('fta','1h','LOW',90,0,r.known)
        quote=quote_bos_next_open(raid=r,bos=bos,next_bar=bs[6],first_1h_fta=target)
        self.assertEqual(quote.entry,bs[6].o)
        self.assertEqual(quote.stop,r.extreme)
        self.assertEqual(quote.target,90)
        self.assertGreater(quote.net_rr,0)
    def test_bos_quote_rejects_future_fta(self):
        bs,p,r=self._bos_setup();bos=bos_after_raid(bs,[p],[r])[0]
        target=Pivot('unconfirmed','1h','LOW',90,0,bos.known+100)
        with self.assertRaises(ValueError):quote_bos_next_open(raid=r,bos=bos,next_bar=bs[6],first_1h_fta=target)
    def test_bos_quote_rejects_bad_target_direction(self):
        bs,p,r=self._bos_setup();bos=bos_after_raid(bs,[p],[r])[0]
        target=Pivot('wrong','1h','HIGH',104,0,r.known)
        with self.assertRaises(ValueError):quote_bos_next_open(raid=r,bos=bos,next_bar=bs[6],first_1h_fta=target)
    def test_bos_quote_rejects_same_bos_bar_as_fill(self):
        bs,p,r=self._bos_setup();bos=bos_after_raid(bs,[p],[r])[0]
        target=Pivot('fta','1h','LOW',90,0,r.known)
        with self.assertRaises(ValueError):quote_bos_next_open(raid=r,bos=bos,next_bar=bs[5],first_1h_fta=target)
    def test_bos_quote_preserves_natural_stop_when_costs_increase(self):
        bs,p,r=self._bos_setup();bos=bos_after_raid(bs,[p],[r])[0]
        target=Pivot('fta','1h','LOW',90,0,r.known)
        base=quote_bos_next_open(raid=r,bos=bos,next_bar=bs[6],first_1h_fta=target,costs_per_side=0)
        expensive=quote_bos_next_open(raid=r,bos=bos,next_bar=bs[6],first_1h_fta=target,costs_per_side=.002)
        self.assertEqual(expensive.stop,base.stop)
        self.assertLess(expensive.net_rr,base.net_rr)

    def test_idm_inside_and_in_front_supported(self):
        poi=POI('poi','1h','LONG',95,100,1);strong=StrongHL('s','LONG',90,'c','v',0,2)
        pivs=[Pivot('in','15m','LOW',97,3,5),Pivot('front','15m','LOW',102,4,6)]
        ids=select_idm(poi=poi,strong=strong,pivots=pivs,as_of=10,entry_tf='15m')
        self.assertEqual({x.location for x in ids},{'INSIDE_POI','IN_FRONT_OF_POI'})
    def test_idm_unconfirmed_pivot_blocked(self):
        poi=POI('poi','4h','SHORT',100,105,1);strong=StrongHL('s','SHORT',115,'c','v',0,2)
        pivs=[Pivot('late','1h','HIGH',103,1,12)]
        self.assertEqual(select_idm(poi=poi,strong=strong,pivots=pivs,as_of=11,entry_tf='1h'),[])
    def test_idm_wrong_stop_side_and_wrong_hierarchy(self):
        poi=POI('poi','4h','SHORT',100,105,1);strong=StrongHL('s','SHORT',102,'c','v',0,2)
        pivs=[Pivot('weak','1h','HIGH',103,1,3)]
        self.assertEqual(select_idm(poi=poi,strong=strong,pivots=pivs,as_of=4,entry_tf='1h'),[])
        with self.assertRaises(ValueError):select_idm(poi=poi,strong=strong,pivots=pivs,as_of=4,entry_tf='3m')
    def test_poi_no_test_before_known_and_first_touch_only(self):
        poi=POI('p','1h','LONG',95,100,2*TF_MS['15m']);life=PoiLifecycle(poi)
        self.assertEqual(life.advance(b('15m',1,o=101,h=102,l=97,c=101)),'FRESH')
        self.assertEqual(life.advance(b('15m',2,o=101,h=102,l=97,c=101)),'TESTED')
        stamp=life.tested_at
        self.assertEqual(life.advance(b('15m',3,o=101,h=102,l=97,c=101)),'TESTED')
        self.assertEqual(stamp,life.tested_at)
    def test_poi_invalidates_before_first_touch(self):
        poi=POI('p','1h','LONG',95,100,0);life=PoiLifecycle(poi)
        self.assertEqual(life.advance(b('15m',0,o=99,h=100,l=93,c=94)),'INVALIDATED')
        self.assertEqual(life.advance(b('15m',1,o=99,h=100,l=96,c=99)),'INVALIDATED')
    def test_fvg_three_closed_candles_and_middle_color_not_mandatory(self):
        bars=[b('5m',0,o=100,h=102,l=99,c=101),
              b('5m',1,o=104,h=106,l=101,c=102), # middle red
              b('5m',2,o=105,h=108,l=104,c=107)]
        self.assertEqual(confirmed_imb(bars[:2]),[])
        gaps=confirmed_imb(bars)
        self.assertEqual(len(gaps),1)
        self.assertEqual((gaps[0].lo,gaps[0].hi),(102,104))
        self.assertEqual(gaps[0].known,bars[-1].end)
    def test_5m_vc_only_after_trigger(self):
        bars=[b('5m',0,o=100,h=102,l=99,c=101),b('5m',1,o=104,h=106,l=101,c=102),
              b('5m',2,o=105,h=108,l=104,c=107),b('5m',3,o=110,h=112,l=109,c=111),
              b('5m',4,o=113,h=115,l=112,c=114),b('5m',5,o=116,h=118,l=115,c=117)]
        self.assertEqual(len(imbs_after_trigger(bars=bars,trigger_known=0,side='LONG')),4)
        self.assertEqual(imbs_after_trigger(bars=bars,trigger_known=bars[2].end,side='SHORT'),[])
        self.assertEqual(len(imbs_after_trigger(bars=bars,trigger_known=bars[2].end,side='LONG')),1)
    def test_5m_vc_does_not_accept_15m_proxy(self):
        with self.assertRaises(ValueError):imbs_after_trigger(bars=[],trigger_known=0,side='LONG',tf='15m')
    def test_idm_existing_pivot_before_poi_confirmation(self):
        poi=POI('poi','4h','LONG',90,95,500)
        strong=StrongHL('s','LONG',85,'r','vc',100,500)
        piv=[Pivot('liquidity','1h','LOW',93,200,400)]
        self.assertEqual(len(select_idm(poi=poi,strong=strong,pivots=piv,as_of=600,entry_tf='1h')),1)

    def test_reject_mixed_tfs_and_gaps(self):
        with self.assertRaises(ValueError):confirmed_pivots([b('3m',0),b('3m',2)])
        with self.assertRaises(ValueError):bos_after_raid([b('3m',0),b('5m',1)],[],[])

if __name__=='__main__':unittest.main()