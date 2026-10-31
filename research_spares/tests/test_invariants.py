"""Adversarial invariants for the independent module contracts."""
import unittest
from ember_spares.accounting import CashEvent, replay_cash_events, Exposure, portfolio_risk_gate
from ember_spares.market import classify_bracket_bar, BarOutcome, OrderSnapshot, transition_order
from ember_spares.structure import Zone, advance_zone
from ember_spares.types import Candle, Evidence
from ember_spares.signals import momentum_ranks


class Invariants(unittest.TestCase):
    def test_ledger_partial_closures_conserve_realised_pnl(self):
        for quantity in [0.5,1,5,100]:
            entries=[CashEvent('open',1,'OPEN',quantity,100)]
            splits=[quantity*.1,quantity*.2,quantity*.3,quantity*.4]
            events=entries + [CashEvent(f'close{i}',i+2,'REDUCE',v,110) for i,v in enumerate(splits)]
            p=replay_cash_events('BTC','long',events)
            self.assertAlmostEqual(p.quantity,0,places=8)
            self.assertAlmostEqual(p.realised_pnl,10*quantity,places=8)

    def test_risk_cannot_be_net_canceled(self):
        a=Exposure('S1','BTC','long',50,1000)
        b=Exposure('S2','BTC','short',60,1000)
        good,reason=portfolio_risk_gate([a],b,100,3000)
        self.assertFalse(good)
        self.assertEqual(reason,'STOP_RISK_BUDGET')

    def test_unobserved_evidence_not_tradable(self):
        e=Evidence(100,1000,3,'OI')
        from ember_spares.market import asof_evidence
        for now in range(100,1000,25):
            self.assertIsNone(asof_evidence([e],now))

    def test_bracket_both_hit_never_success(self):
        for high in [105,120,1000]:
            for low in [10,50,95]:
                c=Candle(0,60,100,high,low,100,1,60)
                self.assertEqual(classify_bracket_bar(c,'long',96,104),BarOutcome.AMBIGUOUS)

    def test_duplicate_zone_update_detected(self):
        zone=Zone('x','demand',90,100,0)
        bar=Candle(10,70,95,100,90,95,1,70)
        zone=advance_zone(zone,bar)
        with self.assertRaises(ValueError): advance_zone(zone,bar)

    def test_order_nonnegative_terminal(self):
        o=OrderSnapshot('x',0,10,3)
        o=transition_order(o,'FILL',1,2)
        o=transition_order(o,'EXPIRE',10)
        self.assertEqual(o.executed,2)
        with self.assertRaises(ValueError): transition_order(o,'FILL',11,1)

    def test_no_rank_if_future_reference_missing(self):
        with self.assertRaises(ValueError): momentum_ranks({'BTC':[100,110]},2)

if __name__ == '__main__': unittest.main()
