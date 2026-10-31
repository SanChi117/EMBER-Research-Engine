import unittest
from ember_spares.research import (
    TraceRow,diff_traces,ObservedTrade,paired_ablation,
    information_coefficient,bonferroni_pvalue,pnl_attribution,FeatureAvailability,
    leakage_violations,capacity_limit_quantity,session_pnl,Holding,exposure_report,
)
from ember_spares.registry import REGISTRY,get_component

class ResearchTests(unittest.TestCase):
    def test_parity_reports_missing_and_sl(self):
        a=[TraceRow(100,'BTC','long',100,90,120,'source')]
        b=[TraceRow(100,'BTC','long',100,91,120,'ported'), TraceRow(200,'ETH','short',100,110,90,'ported')]
        diffs=diff_traces(a,b)
        self.assertEqual(len(diffs),2)
        self.assertEqual({d['difference'] for d in diffs},{'stop','MISSING_FROM_ORIGINAL'})
        with self.assertRaises(ValueError): diff_traces(a+a,b)
        self.assertEqual(diff_traces(a,a),[])

    def test_matched_ablation(self):
        a=[ObservedTrade('a','BTC','S',1,100),ObservedTrade('b','ETH','S',-3,110)]
        b=[ObservedTrade('a','BTC','S',2,100),ObservedTrade('c','ETH','S',10,200)]
        out=paired_ablation(a,b)
        self.assertEqual(out['matched'],1)
        self.assertEqual(out['removed'],['b'])
        self.assertEqual(out['added'],['c'])
        self.assertEqual(out['matched_delta_pnl'],1)
        self.assertEqual(out['total_delta_pnl'],14)

    def test_stats_and_trials(self):
        self.assertAlmostEqual(information_coefficient([1,2,3],[10,20,30]),1)
        self.assertAlmostEqual(bonferroni_pvalue(.01,50),.5)
        self.assertEqual(bonferroni_pvalue(.5,50),1)
        with self.assertRaises(ValueError): bonferroni_pvalue(-.1,2)

    def test_concentration(self):
        a=[ObservedTrade('1','BTC','S',10,0,'breakout'), ObservedTrade('2','ETH','S',-8,0,'breakout'),
           ObservedTrade('3','BTC','S',5,0,'pullback'),ObservedTrade('4','ETH','S',-1,0,'pullback')]
        result=pnl_attribution(a)
        self.assertEqual(result['total'],6)
        self.assertEqual(result['by_symbol']['BTC'],15)
        self.assertEqual(result['without_symbol']['BTC'],-9)
        self.assertEqual(result['top3_share_of_gross_wins'],1)

    def test_availability_checks(self):
        rows=[FeatureAvailability('HTF',100,200,'data'),FeatureAvailability('pivot',100,150,'data',negative_shift_bars=-1),
              FeatureAvailability('ema19200',100,150,'data',warmup_required=19200,warmup_available=500)]
        v=leakage_violations(rows,160)
        self.assertIn('HTF:FUTURE_OR_UNAVAILABLE',v)
        self.assertIn('pivot:NEGATIVE_SHIFT',v)
        self.assertIn('ema19200:INSUFFICIENT_WARMUP',v)

    def test_capacity_only_upper_bound(self):
        self.assertEqual(capacity_limit_quantity(100000,100,.01),10)
        with self.assertRaises(ValueError): capacity_limit_quantity(100,10,1.1)

    def test_sessions_utc(self):
        result=session_pnl([ObservedTrade('a','BTC','S',5,0),ObservedTrade('b','BTC','S',-3,3600)])
        self.assertEqual(result[0]['net_pnl_usdt'],5)
        self.assertEqual(result[1]['net_pnl_usdt'],-3)

    def test_union_exposure(self):
        a=[Holding('S','BTC',0,80),Holding('S','ETH',40,100),Holding('S','BTC',130,150)]
        e=exposure_report(a,0,200)
        self.assertEqual(e['occupied_seconds'],120)
        self.assertAlmostEqual(e['time_in_market_fraction'],.6)
        with self.assertRaises(ValueError): exposure_report(a,100,100)

    def test_registry_37_no_z12(self):
        self.assertEqual(len(REGISTRY),37)
        self.assertEqual(len({c.id for c in REGISTRY}),37)
        self.assertNotIn('Z12',{c.id for c in REGISTRY})
        self.assertEqual(get_component('Z06').entrypoint,'replay_cash_events')
        with self.assertRaises(KeyError): get_component('Z12')

    def test_every_entrypoint_exists(self):
        from importlib import import_module
        for item in REGISTRY:
            with self.subTest(id=item.id):
                m=import_module('ember_spares.'+item.module)
                self.assertTrue(callable(getattr(m,item.entrypoint)))

if __name__=='__main__': unittest.main()
