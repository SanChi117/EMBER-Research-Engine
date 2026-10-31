from hashlib import sha256
import unittest
from ember_spares.signals import (
    z_score,fit_ou,ou_z_score,OIRegime,oi_quadrant,taker_pressure,
    pearson,lag_correlations,momentum_ranks,pair_spread,mean_dislocation,
    ModelContract,verify_model_contract,
)

class SignalsTests(unittest.TestCase):
    def test_zscore_zero_variance(self):
        self.assertIsNone(z_score([1,1,1],2))
        self.assertGreater(z_score([1,2,3,4],6),1)
        with self.assertRaises(ValueError): z_score([1],2)

    def test_ou_fit_mean_reversion(self):
        # Deterministic AR(1) with mild innovation.
        rates=[.01]
        for i in range(40):
            rates.append(.5*rates[-1] + (.001 if i%3==0 else -.0003))
        p=fit_ou(rates)
        self.assertIsNotNone(p)
        self.assertGreater(p.half_life_periods,0)
        self.assertIsInstance(ou_z_score(p,.02),float)
        self.assertIsNone(fit_ou([1]*20))
        self.assertIsNone(fit_ou([1,2,3]))

    def test_oi_regimes(self):
        self.assertEqual(oi_quadrant(100,101,50,51),OIRegime.NEW_LONGS)
        self.assertEqual(oi_quadrant(100,99,50,51),OIRegime.NEW_SHORTS)
        self.assertEqual(oi_quadrant(100,101,50,49),OIRegime.SHORT_CLOSING)
        self.assertEqual(oi_quadrant(100,99,50,49),OIRegime.LONG_CLOSING)
        self.assertEqual(oi_quadrant(100,100,50,49),OIRegime.NEUTRAL)
        with self.assertRaises(ValueError): oi_quadrant(100,101,50,51,2)

    def test_taker_ratio(self):
        self.assertAlmostEqual(taker_pressure([4,2],[10,2]),.5)
        self.assertIsNone(taker_pressure([0,0],[0,0]))
        with self.assertRaises(ValueError): taker_pressure([5],[4])
        with self.assertRaises(ValueError): taker_pressure([5],[4,2])

    def test_lead_lag(self):
        xs=[1,4,2,5,3,8,1,9,3]
        ys=[0]+xs[:-1]
        result=lag_correlations(xs,ys,2)
        self.assertAlmostEqual(result[1],1)
        self.assertLess(result[0],1)
        with self.assertRaises(ValueError): lag_correlations(xs,ys[:-1],2)

    def test_momentum_ranks(self):
        values={'BTC':[100,110,120], 'ETH':[10,10,9], 'XRP':[2,4,6]}
        ranks=momentum_ranks(values,2)
        self.assertEqual([x.asset for x in ranks],['XRP','BTC','ETH'])
        with self.assertRaises(ValueError): momentum_ranks(values,3)

    def test_pair_spread(self):
        x=[1,2,3,4,5,6,7,8]
        y=[2*a + noise for a,noise in zip(x,[.1,-.1,.2,-.1,-.2,.1,.1,-.1])]
        p=pair_spread(y,x,20,9)
        self.assertAlmostEqual(p.beta,2,delta=.05)
        self.assertIsNotNone(p.residual_z)
        with self.assertRaises(ValueError): pair_spread([1]*8,[1]*8,1,1)

    def test_dislocation(self):
        self.assertTrue(mean_dislocation([100]*50,69,threshold=-.3))
        self.assertFalse(mean_dislocation([100]*50,71,threshold=-.3))
        with self.assertRaises(ValueError): mean_dislocation([100]*50,70,threshold=0)

    def test_model_artifact_contract(self):
        artifact=b'not executable: just versioned evidence'
        hash_=sha256(artifact).hexdigest()
        m=ModelContract('myModel',hash_,100,('atr','rsi'),.6)
        self.assertTrue(verify_model_contract(m,artifact,{'atr':1,'rsi':2},101))
        self.assertFalse(verify_model_contract(m,artifact,{'atr':1},101))
        self.assertFalse(verify_model_contract(m,b'alt',{'atr':1,'rsi':2},101))
        self.assertFalse(verify_model_contract(m,artifact,{'atr':1,'rsi':2},100))
        with self.assertRaises(ValueError): ModelContract('m','bogus',100,('atr',),.6)

if __name__=='__main__': unittest.main()
