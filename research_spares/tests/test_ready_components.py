import json, tempfile, unittest
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone

from ember_spares import BinanceUSDMPublic, SQLiteResearchLedger, calculate_indicators, invoke, usd_m_snapshot
from ember_spares.advanced import (historical_signal_frame,liquidation_boundary,orderbook_depth,quote_fill,
  full_trace_parity,two_leg_cash_ledger,correlated_risk_gate,portfolio_replay,
  progress_zone_history,compression_breakout,failure_exit,funding_pressure,
  oi_signal,taker_series,basket_orders,pair_diagnostics,dislocation_plan,dual_entry_risk,
  bootstrap_mean_ci,review_source_for_lookahead,volume_impact_envelope,attribution_by_regime,
  session_preregistered,risk_with_addons,UnavailableEvidence)
from ember_spares.accounting import MarginTier, IsolatedMargin, CashEvent, Exposure, RiskState
from ember_spares.types import Candle,Evidence
from ember_spares.market import Book,OrderSnapshot
from ember_spares.research import TraceRow,ObservedTrade
from ember_spares.structure import Zone
from ember_spares.operations import bar_bracket_uncertainty,resolve_order_replay

T=1_800_000_000

def bar(i, p=100.0, high=101.0, low=99.0, vol=100.):
    o=T+i*60
    return Candle(o,o+60,p,high,low,p,vol,o+60)


def funding(i,value):
    t=T+i*60
    return Evidence(t,t+5,value,'binance:funding')


class ReadyComponents(unittest.TestCase):
    def setUp(self):
        self.bars=[bar(i,100+(i%3)*.1,101+(i%3)*.1,99+(i%3)*.1,100+i) for i in range(65)]
        self.tiers=[MarginTier(0,100000,.005,0)]

    def test_liquidation_root(self):
        p=IsolatedMargin('long',10,100,100,100)
        result=liquidation_boundary(p,self.tiers,minimum_price=75,maximum_price=110)
        self.assertTrue(result['found'])
        self.assertAlmostEqual(result['modeled_mark'],90.4522613065,places=4)

    def test_no_fake_liquidation(self):
        p=IsolatedMargin('long',1,100,100,100)
        self.assertFalse(liquidation_boundary(p,self.tiers,minimum_price=80,maximum_price=120)['found'])

    def test_l2_and_unknown_fill(self):
        values=orderbook_depth([(99,9),(98,8)],[(101,1),(102,2)])
        self.assertGreater(values['depth_imbalance'],0)
        b=Book(99,101,9,1,T,T)
        self.assertFalse(quote_fill('buy',2,b)['fully_covered_top_book'])
        self.assertFalse(quote_fill('buy',2,b)['confirmed_fill'])

    def test_trace_no_hidden_difference(self):
        a=TraceRow(T,'SOLUSDT','long',100,99,102,'original')
        b=TraceRow(T,'SOLUSDT','short',100,99,102,'our')
        self.assertFalse(full_trace_parity([a],[b])['matches'])

    def test_multileg_partial_hedge(self):
        legs={'SOLUSDT':[CashEvent('1',0,'OPEN',2,100,fee=.1)],'ETHUSDT':[CashEvent('2',0,'OPEN',1,200,fee=.1)]}
        r=two_leg_cash_ledger(legs,{'SOLUSDT':'long','ETHUSDT':'short'},{'SOLUSDT':105,'ETHUSDT':198})
        self.assertAlmostEqual(r['net_mark_to_market_usdt'],11.8)
        self.assertFalse(r['legs_hedged'])

    def test_correlation_conservative(self):
        new=Exposure('a','SOLUSDT','long',90,1000)
        r=correlated_risk_gate([],new,max_stop_risk=100,max_gross_notional=5000,max_strategy_stop_risk=80,max_symbol_notional=5000)
        self.assertFalse(r['allow'])

    def test_order_persistence(self):
        order=OrderSnapshot('O',T,T+30,10)
        result=portfolio_replay({'O':order},[(T+10,'O','FILL',3),(T+20,'O','FILL',7)])
        self.assertEqual(result['O'].state.value,'FILLED')
        with self.assertRaises(ValueError):
            portfolio_replay({'O':order},[(T+10,'O','FILL',11)])

    def test_sl_tp_ambiguous(self):
        row=bar(0,100,105,95)
        r=bar_bracket_uncertainty([row],'long',96,104)
        self.assertEqual(r['outcome'],'AMBIGUOUS')
        self.assertEqual((r['worst'],r['best']),('STOP','TARGET'))

    def test_zone_update(self):
        z=Zone('A','demand',90,100,T)
        r=progress_zone_history(z,[bar(1,95,101,90)],decision_at=T+120)
        self.assertEqual(r.touches,1)

    def test_compression(self):
        values=compression_breakout(self.bars,decision_at=self.bars[-1].available_at,lookback=10,max_range_atr=3,volume_multiplier=.5)
        self.assertIn('compressed',values)

    def test_failure_exit(self):
        bars=[bar(0,100,101,99),bar(1,97,101,96),bar(2,96,101,95)]
        self.assertTrue(failure_exit(bars,decision_at=bars[-1].available_at,level=98,breakout_side='long',required_confirmation=2)['invalidation'])

    def test_funding_and_lookahead(self):
        series=[funding(i,.001+(.0001 if i%2 else -.0001)+.000004*i) for i in range(40)]
        r=funding_pressure(series,decision_at=T+40*60,lookback=20)
        self.assertEqual(r['sample_count'],20)
        with self.assertRaises(UnavailableEvidence):
            funding_pressure(series,decision_at=T+2*60)

    def test_oi_alignment(self):
        prices=[Evidence(T,T+1,100,'p'),Evidence(T+60,T+61,101,'p')]
        oi=[Evidence(T,T+2,1000,'oi'),Evidence(T+60,T+62,1020,'oi')]
        r=oi_signal(prices,oi,None,decision_at=T+62)
        self.assertEqual(r['quadrant'],'NEW_LONGS')
        with self.assertRaises(UnavailableEvidence):
            oi_signal(prices,oi,None,decision_at=T+61)

    def test_taker_alignment(self):
        values=[10]*len(self.bars)
        r=taker_series(self.bars,values,decision_at=self.bars[20].available_at,window=5)
        self.assertTrue(0<r['buy_ratio']<1)
        with self.assertRaises(ValueError):
            taker_series(self.bars,[10],decision_at=self.bars[-1].available_at)

    def test_basket_weights_and_prices(self):
        p={'SOLUSDT':[100,101,102,105],'ETHUSDT':[100,105,110,115]}
        result=basket_orders(p,lookback=3,top=2,equity=1000,exposure_fraction=.8,maximum_symbol_weight=.25)
        self.assertAlmostEqual(result['gross_weight'],.5)
        self.assertEqual(result['entries'][0]['symbol'],'ETHUSDT')

    def test_pair_diagnostics_not_guarantee(self):
        x=[float(i) for i in range(1,25)]
        y=[2*e+(.1 if i%2 else -.1) for i,e in enumerate(x)]
        r=pair_diagnostics(y,x,51.,25.)
        self.assertIn('eligible_for_further_tests',r)

    def test_rsi_dislocation_and_risk(self):
        result=dislocation_plan([100]*25,60,28)
        self.assertTrue(result['eligible'])
        p=dual_entry_risk(90,110,'long',1,risk_budget_usdt=100)
        self.assertAlmostEqual(p['worst_case_loss_usdt'],100)

    def test_bootstrap_repeatable(self):
        a=bootstrap_mean_ci([1,-2,3,-1,2,-2]*5,block_size=4,replicates=100,seed=1)
        b=bootstrap_mean_ci([1,-2,3,-1,2,-2]*5,block_size=4,replicates=100,seed=1)
        self.assertEqual(a,b)

    def test_scanner_heuristics(self):
        self.assertIn('NEGATIVE_SHIFT',review_source_for_lookahead('x.shift(-1)'))
        self.assertIn('PINE_LOOKAHEAD_ON',review_source_for_lookahead('lookahead=barmerge.lookahead_on',language='pine'))

    def test_market_impact_not_executed(self):
        a=volume_impact_envelope(100,1,100000,.001)
        self.assertTrue(a['is_scenario_not_observed'])
        self.assertTrue(a['capacity_ok'])

    def test_regime_attribution(self):
        trs=[ObservedTrade('a','SOLUSDT','alpha',10,T),ObservedTrade('b','SOLUSDT','alpha',-4,T)]
        r=attribution_by_regime(trs,{'a':'trend','b':'range'})
        self.assertEqual(r['trend']['total'],10)
        self.assertEqual(session_preregistered(trs,[datetime.fromtimestamp(T,tz=timezone.utc).hour])['included_trades'],2)

    def test_budget_after_adds(self):
        events=[CashEvent('1',0,'OPEN',1,100),CashEvent('2',1,'ADD',1,101)]
        r=risk_with_addons(events,symbol='SOLUSDT',side='long',stop=98,max_stop_loss=4,mark=100,collateral=50,tiers=self.tiers)
        self.assertFalse(r['risk_budget_ok'])

    def test_sqlite_durable_idempotency(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger.sqlite'
            l=SQLiteResearchLedger(path)
            event=CashEvent('id1',0,'OPEN',1,100,fee=.02)
            self.assertEqual(l.record_cash('paper','SOLUSDT','long',event),'RECORDED')
            self.assertEqual(l.record_cash('paper','SOLUSDT','long',event),'DUPLICATE_SAFE')
            self.assertEqual(SQLiteResearchLedger(path).position('paper','SOLUSDT','long').quantity,1)
            with self.assertRaises(ValueError):l.record_cash('paper','SOLUSDT','long',CashEvent('id1',0,'OPEN',2,100))
            s=RiskState('2026-01-01','2026-W01',0,0,0,False)
            v=l.set_risk_if_version('paper',s,expected_revision=None)
            v2,s2=l.post_risk('paper',-110,day='2026-01-01',week='2026-W01',daily_limit=100,weekly_limit=200,max_losses=3)
            self.assertTrue(s2.halted)
            self.assertTrue(SQLiteResearchLedger(path).risk('paper')[1].halted)
            with self.assertRaises(ValueError):l.set_risk_if_version('paper',s,expected_revision=v2)

    def test_guard_unknown_trade_receipts(self):
        order=OrderSnapshot('Q',T,T+60,1)
        with self.assertRaises(ValueError):
            resolve_order_replay(order,[{'event_id':'A','received_at':T+1,'kind':'FILL','quantity':1,'origin':'candle_touch'}])

    def test_binance_fake_transport(self):
        start=1_700_000_000_000
        kline=[start,'100','101','99','100','100',start+59_999,'0',10,'25','0','0']
        responses={
            '/fapi/v1/klines':[kline],
            '/fapi/v1/markPriceKlines':[kline],
            '/fapi/v1/fundingRate':[{'fundingTime':start+1000,'fundingRate':'0.0001'}],
            '/futures/data/openInterestHist':[{'timestamp':start+1000,'sumOpenInterest':'1234'}],
            '/fapi/v1/ticker/bookTicker':{'b':'99','a':'101','B':'10','A':'10','T':start+50},
        }
        calls=[]
        def transport(path,params,timeout):
            calls.append((path,dict(params)))
            return responses[path]
        client=BinanceUSDMPublic(transport=transport)
        cutoff=(start+100_000)//1000
        result=usd_m_snapshot(client,symbol='SOLUSDT',interval='1m',start_ms=start,end_ms=start+100_000,decision_at=cutoff,funding_lag_ms=1000,oi_lag_ms=1000)
        self.assertTrue(result['complete'])
        self.assertEqual(len(calls),4)
        self.assertEqual(len(result['data']['funding']),1)
        book=client.best_book('SOLUSDT',received_ms=start+200)
        self.assertEqual(book.bid,99)
        self.assertEqual(set(x[1]['symbol'] for x in calls),{'SOLUSDT'})

    def test_binance_missing_never_fallback_spot(self):
        client=BinanceUSDMPublic(transport=lambda path,params,timeout: (_ for _ in ()).throw(OSError('451')))
        with self.assertRaises(Exception):client.klines('SOLUSDT','1h',1,10000)

    def test_data_bundle_degrades_explicitly(self):
        r=calculate_indicators(self.bars,decision_at=self.bars[-1].available_at)
        self.assertEqual(r['Z01'].state,'CALCULATED')
        self.assertFalse(r['Z01'].value['valid_for_oi_funding_signal'])
        self.assertEqual(r['Z22'].state,'BLOCKED_DATA')

    def test_plugin_extensions_live(self):
        a=invoke('Z32.scan_source',{'code':'x.shift(-2)'})
        self.assertEqual(a,['NEGATIVE_SHIFT'])
        b=invoke('Z34.impact_envelope',{'order_quantity':50.,'price':1.,'quote_volume':100000.,'spread_fraction':.001})
        self.assertTrue(b['is_scenario_not_observed'])

if __name__=='__main__':unittest.main()
