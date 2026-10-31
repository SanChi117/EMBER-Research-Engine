import tempfile
from pathlib import Path
import unittest
from ember_spares.accounting import (
    MarginTier, IsolatedMargin, maintenance_required, margin_state, Leg, multileg_pnl,
    CashEvent, replay_cash_events, Exposure, portfolio_risk_gate, RiskState,
    update_risk, save_risk_state, load_risk_state, staircase_risk,
)

class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.tiers=[MarginTier(0,10000,.01), MarginTier(10000,100000,.02,100)]

    def test_margin_tiers_and_isolated_loss(self):
        self.assertAlmostEqual(maintenance_required(2000,self.tiers),20)
        self.assertAlmostEqual(maintenance_required(12000,self.tiers),140)
        p=IsolatedMargin("long",10,100,90,60,5,1)
        state=margin_state(p,self.tiers)
        self.assertAlmostEqual(state["equity"],-46)
        self.assertTrue(state["below_maintenance"])
        with self.assertRaises(ValueError): maintenance_required(110000,self.tiers)
        with self.assertRaises(ValueError): maintenance_required(900,[MarginTier(100,2000,.05)])
        with self.assertRaises(ValueError): maintenance_required(900,[MarginTier(0,500,.05),MarginTier(600,2000,.06)])

    def test_short_equity(self):
        p=IsolatedMargin("short",2,200,150,100,4,0)
        s=margin_state(p,self.tiers)
        self.assertAlmostEqual(s["equity"],196)
        self.assertFalse(s["below_maintenance"])

    def test_multileg_signed_pnl_and_funding(self):
        legs=[Leg("BTC","long",1,100,110,1,2),Leg("ETH","short",2,50,45,1,-.5)]
        a=multileg_pnl(legs)
        self.assertAlmostEqual(a["gross_usdt"],20)
        self.assertAlmostEqual(a["net_usdt"],16.5)
        self.assertAlmostEqual(a["signed_notional_usdt"],20)

    def test_cash_ledger_weighted_average_and_partial(self):
        events=[CashEvent("e1",1,"OPEN",2,100,1),CashEvent("e2",2,"ADD",2,110,1),
                CashEvent("e3",3,"FUNDING",funding=3),CashEvent("e4",4,"REDUCE",3,120,1)]
        p=replay_cash_events("BTC","long",events)
        self.assertEqual(p.quantity,1)
        self.assertAlmostEqual(p.avg_entry,105)
        self.assertAlmostEqual(p.realised_pnl,45)
        self.assertEqual(p.paid_fees,3)
        self.assertEqual(p.paid_funding,3)
        p2=replay_cash_events("BTC","long",events+[CashEvent("e5",5,"REDUCE",1,90,0)])
        self.assertEqual(p2.quantity,0)
        self.assertAlmostEqual(p2.realised_pnl,30)

    def test_cash_ledger_invalid_events(self):
        with self.assertRaises(ValueError): replay_cash_events("BTC","long",[CashEvent("a",1,"REDUCE",1,90)])
        with self.assertRaises(ValueError): replay_cash_events("BTC","long",[CashEvent("a",1,"OPEN",1,90),CashEvent("a",2,"ADD",1,90)])
        with self.assertRaises(ValueError): replay_cash_events("BTC","long",[CashEvent("a",1,"OPEN",1,90),CashEvent("b",1,"ADD",1,90)])
        p=replay_cash_events("BTC","short",[CashEvent("a",1,"OPEN",1,200),CashEvent("b",2,"REDUCE",1,150)])
        self.assertEqual(p.realised_pnl,50)

    def test_portfolio_budget(self):
        a=Exposure("mean","BTC","long",20,2000)
        b=Exposure("trend","BTC","short",40,3000)
        self.assertEqual(portfolio_risk_gate([a],b,100,6000),(True,"OK"))
        self.assertEqual(portfolio_risk_gate([a],b,50,6000),(False,"STOP_RISK_BUDGET"))
        self.assertEqual(portfolio_risk_gate([a],b,100,4000),(False,"SYMBOL_NOTIONAL_BUDGET"))

    def test_risk_latch_across_day_and_restart(self):
        r=RiskState("2026-01-01","2026-W01",0,0,0,False)
        r=update_risk(r,-11,day="2026-01-01",week="2026-W01",daily_limit=10,weekly_limit=20,max_losses=3)
        self.assertTrue(r.halted)
        r=update_risk(r,10,day="2026-01-02",week="2026-W01",daily_limit=10,weekly_limit=20,max_losses=3)
        self.assertTrue(r.halted)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"nested"/"risk.json"
            save_risk_state(path,r)
            self.assertEqual(load_risk_state(path),r)
            path.write_text('{"halted":false}')
            with self.assertRaises(ValueError): load_risk_state(path)

    def test_risk_loss_streak(self):
        r=RiskState("D","W",0,0,0,False)
        for i in range(3):
            r=update_risk(r,-1,day="D",week="W",daily_limit=100,weekly_limit=100,max_losses=3)
        self.assertTrue(r.halted)
        self.assertEqual(r.consecutive_losses,3)

    def test_staircase(self):
        self.assertEqual(staircase_risk(100,[(0,.01),(1000,.005)],100),1)
        self.assertEqual(staircase_risk(2000,[(0,.01),(1000,.005)],100),10)
        with self.assertRaises(ValueError): staircase_risk(100,[(100,.01)],100)

if __name__ == '__main__': unittest.main()
