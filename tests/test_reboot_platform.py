"""RESET pure market/settlement/SHA contracts: adversarial and deterministic."""
import copy
import unittest
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace
from research.platform import market_contract as m
from research.platform import paper_execution as p
from research.platform import sha_ledger as l

T=1760000040000
ONE=60000
SHA="a"*64

def bar(i,open_price="100",high="104",low="99",close="102",v="1",available=None):
    start=T+i*ONE
    return m.ClosedBar(symbol="SOLUSDT",venue="BINANCE",market_kind="PERP_USDM",
        interval_ms=ONE,open_ms=start,close_ms=start+ONE,
        available_at_ms=available if available is not None else start+ONE,
        ingested_at_ms=available if available is not None else start+ONE,
        open=D(open_price),high=D(high),low=D(low),close=D(close),
        volume=D(v),origin_sha256=SHA,provenance="HISTORICAL_ASSUMED_AT_CLOSE")

def long_entry():
    quote=p.Quote("SOLUSDT","BINANCE",T+ONE+1000,D("99.9"),D("100"))
    plan=p.Plan("signal:1","SOLUSDT","LONG",T+ONE,D("98"),D("105"))
    return p.open_paper(plan,quote,T+ONE+2000)

def short_entry():
    quote=p.Quote("SOLUSDT","BINANCE",T+ONE+1000,D("100"),D("100.1"))
    plan=p.Plan("signal:2","SOLUSDT","SHORT",T+ONE,D("102"),D("96"))
    return p.open_paper(plan,quote,T+ONE+2000)

class ResetMarketTest(unittest.TestCase):
    def test_valid_caused_bar_and_original_1m_adapter(self):
        x=bar(0)
        fake=SimpleNamespace(start_ms=x.open_ms,known_ms=x.close_ms,
                             o=x.open,h=x.high,l=x.low,c=x.close,volume=x.volume)
        a=m.from_c116(fake,symbol="SOLUSDT",venue="BINANCE",origin_sha256=SHA,
                      ingested_at_ms=T+4*ONE,historical_assumed_close=True)
        self.assertEqual(a.open_ms,x.open_ms)
        self.assertEqual(a.provenance,"HISTORICAL_ASSUMED_AT_CLOSE")
    def test_legacy_assumed_close_cannot_be_live_by_implicit_flag(self):
        x=bar(0)
        source=SimpleNamespace(start_ms=x.open_ms,known_ms=x.close_ms,
                             o=x.open,h=x.high,l=x.low,c=x.close,volume=x.volume)
        with self.assertRaises(m.DataUntrusted):
            m.from_c116(source,symbol="SOLUSDT",venue="BINANCE",
                origin_sha256=SHA,ingested_at_ms=x.close_ms+1,historical_assumed_close=False)
    def test_future_bar_cannot_enter_asof(self):
        x=m.closed_asof((bar(0),bar(1)),decision_at_ms=T+ONE+1000,
                        max_last_bar_lag_ms=5000)
        self.assertEqual(len(x),1)
    def test_replay_cannot_be_mislabelled_live(self):
        with self.assertRaisesRegex(m.DataUntrusted,"HISTORICAL_REPLAY"):
            m.closed_asof((bar(0),),decision_at_ms=T+ONE+500,
                          max_last_bar_lag_ms=1000,require_live=True)
    def test_duplicate_minute_is_forbidden(self):
        with self.assertRaisesRegex(m.DataUntrusted,"GAP_DUPLICATE"):
            m.closed_asof((bar(0),bar(0)),decision_at_ms=T+2*ONE,
                          max_last_bar_lag_ms=ONE)
    def test_cross_exchange_cannot_be_silently_mixed(self):
        with self.assertRaisesRegex(m.DataUntrusted,"CROSS_MARKET"):
            m.closed_asof((bar(0),replace(bar(1),venue="BYBIT")),
                          decision_at_ms=T+3*ONE,max_last_bar_lag_ms=ONE)
    def test_stale_market_not_relabelled_signal(self):
        with self.assertRaisesRegex(m.DataUntrusted,"STALE"):
            m.closed_asof((bar(0),),decision_at_ms=T+3*ONE,max_last_bar_lag_ms=ONE)
    def test_provider_checksum_required(self):
        with self.assertRaisesRegex(m.DataUntrusted,"SOURCE_SHA"):
            replace(bar(0),origin_sha256="INVALID")
    def test_nonfinite_or_broken_ohlc_rejected(self):
        with self.assertRaises(m.DataUntrusted):replace(bar(0),close=D("NaN"))
        with self.assertRaises(m.DataUntrusted):replace(bar(0),low=D("105"))
    def test_asof_observed_time_separate_from_close_time(self):
        delayed=bar(0,available=T+2*ONE)
        with self.assertRaisesRegex(m.DataUntrusted,"NO_CLOSED"):
            m.closed_asof((delayed,),decision_at_ms=T+ONE,
                          max_last_bar_lag_ms=ONE)

class ResetPaperTest(unittest.TestCase):
    def test_valid_long_paper_and_notional_risk_caps(self):
        z=long_entry()
        self.assertLessEqual(z.quantity*z.price,D("50"))
        self.assertLessEqual(z.risk,D("0.5"))
        self.assertGreater(z.next_full_minute_ms,z.quote.observed_at_ms)
    def test_stale_quote_or_future_signal_rejected(self):
        z=long_entry()
        with self.assertRaisesRegex(m.DataUntrusted,"FUTURE_OR_STALE"):
            p.open_paper(z.plan,z.quote,z.quote.observed_at_ms+20000)
        with self.assertRaisesRegex(m.DataUntrusted,"FUTURE_OR_STALE"):
            p.open_paper(replace(z.plan,confirmed_at_ms=z.quote.observed_at_ms+1),
                         z.quote,z.quote.observed_at_ms+2000)
    def test_crossed_quote_and_invalid_geometry_rejected(self):
        z=long_entry()
        with self.assertRaisesRegex(m.DataUntrusted,"CROSSED"):
            p.open_paper(z.plan,replace(z.quote,bid=D("101")),z.quote.observed_at_ms)
        with self.assertRaisesRegex(m.DataUntrusted,"GEOMETRY"):
            p.open_paper(replace(z.plan,stop=D("101")),
                         z.quote,z.quote.observed_at_ms)
    def test_stop_first_on_both_touched_same_minute(self):
        z=long_entry()
        first=bar(2,open_price="100",high="107",low="97",close="103")
        x=p.evaluate_paper(z,[first],T+3*ONE)
        self.assertEqual(x.cause,"STOP")
        self.assertLess(x.net_r,D("0"))
    def test_gap_beyond_stop_is_not_filled_at_stop(self):
        z=long_entry()
        first=bar(2,open_price="95",high="97",low="92",close="94")
        x=p.evaluate_paper(z,[first],T+3*ONE)
        self.assertEqual(x.cause,"STOP")
        self.assertLess(x.exit_price,z.plan.stop)
        self.assertLess(x.net_r,D("-1"))
    def test_short_gap_worse_than_stop(self):
        z=short_entry()
        first=bar(2,open_price="105",high="106",low="104",close="105")
        x=p.evaluate_paper(z,[first],T+3*ONE)
        self.assertEqual(x.cause,"STOP")
        self.assertGreater(x.exit_price,z.plan.stop)
        self.assertLess(x.net_r,D("-1"))
    def test_target_paid_both_fees_and_slippage(self):
        z=long_entry()
        x=p.evaluate_paper(z,[bar(2,open_price="101",high="106",
                                   low="100",close="105")],T+3*ONE)
        self.assertEqual(x.cause,"TARGET")
        self.assertLess(x.net_r,(z.plan.target-z.price)/abs(z.price-z.plan.stop))
    def test_no_bar_is_halted_not_profitable_timeout(self):
        z=long_entry()
        self.assertEqual(p.evaluate_paper(z,[],T+3*ONE).status,"HALTED")
    def test_missing_next_minute_or_partial_entry_minute_rejected(self):
        z=long_entry()
        with self.assertRaisesRegex(m.DataUntrusted,"MISSING_EXIT"):
            p.evaluate_paper(z,[bar(3)],T+4*ONE)
        with self.assertRaisesRegex(m.DataUntrusted,"PARTIAL_ENTRY"):
            p.evaluate_paper(z,[bar(1)],T+4*ONE)
    def test_not_yet_closed_minute_not_falsely_settled(self):
        z=long_entry()
        x=p.evaluate_paper(z,[bar(2,open_price="101",high="107",low="99",
                                   close="104")],T+2*ONE+1000)
        self.assertEqual(x.status,"HALTED")
        self.assertIsNone(x.net_r)

class ResetLedgerTest(unittest.TestCase):
    def test_append_and_verify_sha_chain(self):
        a=l.extend([],event_id="a",event_type="SOURCE",payload={"sha":SHA})
        b=l.extend(a,event_id="b",event_type="SIMULATED",payload={"net_r":"-1.2"})
        self.assertEqual(l.verify(b),b[-1]["record_sha256"])
        self.assertEqual(len(a),1)
    def test_mutation_and_duplicate_are_rejected(self):
        a=l.extend([],event_id="a",event_type="SOURCE",payload={"sha":SHA})
        with self.assertRaises(l.LedgerError):
            l.extend(a,event_id="a",event_type="SIMULATED",payload={})
        corrupt=copy.deepcopy(a)
        corrupt[0]["payload"]["sha"]="b"*64
        with self.assertRaisesRegex(l.LedgerError,"TAMPERED"):
            l.verify(corrupt)
if __name__=="__main__":
    unittest.main()
