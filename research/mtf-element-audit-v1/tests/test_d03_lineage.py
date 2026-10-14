#!/usr/bin/env python3
import copy, pathlib, sys, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from strict_event_lineage_d03 import CausalEvent, EventLedger, D03Rejected

BASE=dict(uid='S',kind='SOURCE',symbol='BTCUSDT',venue='Binance',market='USDM_FUTURES',
          timeframe='4h',origin_open_ms=1000,origin_close_ms=2000,known_at_ms=2000,
          parent_uids=(),evidence_uids=('sha:raw1',),decision_at_ms=None,order_at_ms=None,fill_at_ms=None)

def event(**update):
    d=dict(BASE);d.update(update);return CausalEvent(**d)

def route():
    g=EventLedger();g.add(event())
    g.add(event(uid='P',kind='POI',known_at_ms=2100,parent_uids=('S',),evidence_uids=('sha:poi',)))
    g.add(event(uid='T',kind='TRIGGER',known_at_ms=2200,parent_uids=('P',),evidence_uids=('sha:trig',)))
    g.add(event(uid='V',kind='VC',known_at_ms=2300,parent_uids=('T',),evidence_uids=('sha:vc',)))
    return g

class TestD03(unittest.TestCase):
    def assert_reject(self,code,fn):
        with self.assertRaises(D03Rejected) as x:fn()
        self.assertEqual(x.exception.code,code)

    def test_basic_route(self):
        g=route();self.assertEqual([x.uid for x in g.ancestors('V',as_of_ms=2300)],['S','P','T'])
    def test_asof_time(self):
        g=route();self.assertEqual([x.uid for x in g.snapshot(2199)],['S','P'])
    def test_asof_equal_close(self):
        g=route();self.assertEqual([x.uid for x in g.snapshot(2200)],['S','P','T'])
    def test_asof_historical_immutable_after_add(self):
        g=route();old=g.snapshot(2300)
        g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2500,parent_uids=('P',),evidence_uids=('sha:cancel',)))
        self.assertEqual(g.snapshot(2300),old)
    def test_frozen_events(self):
        from dataclasses import FrozenInstanceError
        ev=event()
        with self.assertRaises(FrozenInstanceError):ev.known_at_ms=0
    def test_copy_export_cannot_mutate(self):
        g=route();h=g.digest();export=g.export();export[0]['parent_uids'].append('FAKE');export[0]['known_at_ms']=0
        self.assertEqual(g.digest(),h)
    def test_replay_round_trip(self):
        g=route();self.assertEqual(EventLedger.replay(g.export()).digest(),g.digest())
    def test_parent_late(self):
        g=route();self.assert_reject('UNKNOWN_PARENT',lambda:g.add(event(uid='X',kind='VC',known_at_ms=2400,parent_uids=('FUTURE',))))
    def test_no_cross_symbol(self):
        g=route();self.assert_reject('CROSS_INSTRUMENT_PARENT',lambda:g.add(event(uid='X',kind='VC',symbol='ETHUSDT',known_at_ms=2400,parent_uids=('P',))))
    def test_no_cross_market(self):
        g=route();self.assert_reject('CROSS_INSTRUMENT_PARENT',lambda:g.add(event(uid='X',kind='VC',market='SPOT',known_at_ms=2400,parent_uids=('P',))))
    def test_no_cross_venue(self):
        g=route();self.assert_reject('CROSS_INSTRUMENT_PARENT',lambda:g.add(event(uid='X',kind='VC',venue='Other',known_at_ms=2400,parent_uids=('P',))))
    def test_no_orphan_vc(self):
        self.assert_reject('ORPHAN_DERIVED_EVENT',lambda:event(uid='X',kind='VC'))
    def test_no_orphan_poi(self):
        self.assert_reject('ORPHAN_DERIVED_EVENT',lambda:event(uid='X',kind='POI'))
    def test_no_empty_evidence(self):
        self.assert_reject('NO_EVIDENCE_REFERENCE',lambda:event(evidence_uids=()))
    def test_pivot_right_bars_known_time(self):
        # Pivot may have originated at 10:00 and become known at 10:30.
        g=EventLedger().add(event())
        g.add(event(uid='PIV',kind='LIQUIDITY',origin_open_ms=1000,origin_close_ms=2000,known_at_ms=3500,parent_uids=('S',)))
        self.assertEqual([x.uid for x in g.snapshot(2999)],['S'])
        self.assertEqual([x.uid for x in g.snapshot(3500)],['S','PIV'])
    def test_after_cancel_parent_direct(self):
        g=route();g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2350,parent_uids=('P',)))
        self.assert_reject('PARENT_ANCESTRY_INVALIDATED',lambda:g.add(event(uid='C',kind='VC',known_at_ms=2400,parent_uids=('P',))))
    def test_after_cancel_grandparent(self):
        g=route();g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2350,parent_uids=('P',)))
        self.assert_reject('PARENT_ANCESTRY_INVALIDATED',lambda:g.add(event(uid='C',kind='VC',known_at_ms=2400,parent_uids=('V',))))
    def test_historical_child_still_visible(self):
        g=route();g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2400,parent_uids=('P',)))
        self.assertEqual([x.uid for x in g.snapshot(2399,active_only=True)],['S','P','T','V'])
        self.assertEqual([x.uid for x in g.snapshot(2500,active_only=True)],['S'])
    def test_cancel_once(self):
        g=route();g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2400,parent_uids=('P',)))
        self.assert_reject('DUPLICATE_INVALIDATION',lambda:g.add(event(uid='Y',kind='INVALIDATION',known_at_ms=2500,parent_uids=('P',))))
    def test_order_and_fill_timing(self):
        g=route();g.add(event(uid='I',kind='INTENT',known_at_ms=2300,decision_at_ms=2300,parent_uids=('V',)))
        g.add(event(uid='O',kind='ORDER',known_at_ms=2400,decision_at_ms=2300,order_at_ms=2400,parent_uids=('I',)))
        g.add(event(uid='F',kind='FILL',known_at_ms=2450,decision_at_ms=2300,order_at_ms=2400,fill_at_ms=2450,parent_uids=('O',)))
        self.assertEqual(len(g.snapshot(2450)),7)
        self.assertEqual(len(g.snapshot(2399)),5)
        self.assertEqual(len(g.snapshot(2449)),6)
    def test_parent_order_not_revive(self):
        g=route();g.add(event(uid='X',kind='INVALIDATION',known_at_ms=2400,parent_uids=('P',)))
        self.assert_reject('PARENT_ANCESTRY_INVALIDATED',lambda:g.add(event(uid='I',kind='INTENT',known_at_ms=2500,decision_at_ms=2500,parent_uids=('V',))))
    def test_no_dupe_uid(self):
        g=route();self.assert_reject('DUPLICATE_EVENT_UID',lambda:g.add(event(uid='S',kind='SOURCE',known_at_ms=2500)))
    def test_no_retro_insert(self):
        g=route();self.assert_reject('RETROACTIVE_INSERTION',lambda:g.add(event(uid='X',kind='VC',known_at_ms=2100,parent_uids=('P',))))
    def test_bad_cyclic_replay(self):
        row=event().as_record();row['parent_uids']=['S'];self.assert_reject('REPLAY_REF_SCHEMA',lambda:EventLedger.replay([dict(row,parent_uids=('S',))]))
    def test_unknown_parent_asof(self):
        g=route();self.assert_reject('CHILD_NOT_KNOWN_AS_OF',lambda:g.ancestors('V',as_of_ms=2299))
    def test_unknown_parent_provenance_is_only_reference(self):
        g=route();self.assertEqual(g.export()[0]['evidence_uids'],['sha:raw1'])

class TestAdversarialGrid(unittest.TestCase):
    def test_invalid_records(self):
        cases=[
         ('BAD_TIME',dict(origin_open_ms=-1)),('BAD_TIME',dict(known_at_ms=True)),('BAD_TIME',dict(origin_close_ms=1.5)),
         ('BAD_ORIGIN_INTERVAL',dict(origin_close_ms=1000)),('UNKNOWN_UNCLOSED_EVENT',dict(known_at_ms=1999)),
         ('DECISION_BEFORE_KNOWN',dict(decision_at_ms=1999)),('ORDER_BEFORE_DECISION',dict(decision_at_ms=2100,order_at_ms=2000)),
         ('ORDER_BEFORE_DECISION',dict(order_at_ms=2200)),('FILL_BEFORE_ORDER',dict(decision_at_ms=2200,order_at_ms=2250,fill_at_ms=2249)),
         ('FILL_BEFORE_ORDER',dict(fill_at_ms=2500)),('MUTABLE_OR_INVALID_REFERENCES',dict(parent_uids=[])),
         ('MUTABLE_OR_INVALID_REFERENCES',dict(evidence_uids=['a'])),('DUPLICATE_REFERENCE',dict(evidence_uids=('a','a'))),
         ('SELF_PARENT',dict(parent_uids=('S',))),('SOURCE_HAS_PARENTS',dict(parent_uids=('A',))),
         ('INVALIDATION_TARGET_REQUIRED',dict(kind='INVALIDATION',parent_uids=('A','B'))),
         ('INTENT_NEEDS_DECISION_TIME',dict(kind='INTENT',parent_uids=('A',))),
         ('ORDER_NEEDS_ORDER_TIME',dict(kind='ORDER',parent_uids=('A',))),
         ('FILL_NEEDS_FILL_TIME',dict(kind='FILL',parent_uids=('A',))),
         ('ORDER_ACK_FUTURE_LEAK',dict(kind='ORDER',parent_uids=('A',),decision_at_ms=2000,order_at_ms=2200)),
         ('FILL_ACK_FUTURE_LEAK',dict(kind='FILL',parent_uids=('A',),decision_at_ms=2000,order_at_ms=2100,fill_at_ms=2200)),
         ('UNKNOWN_KIND',dict(kind='PROMISE')),('UNKNOWN_MARKET',dict(market='foo')),
         ('BAD_STRING',dict(symbol=' ')),('BAD_STRING',dict(uid='')),('DUPLICATE_REFERENCE',dict(parent_uids=('A','A')))
        ]
        for code,args in cases:
            with self.subTest(code=code,args=args):
                try:event(**args)
                except D03Rejected as e:self.assertEqual(e.code,code)
                else:self.fail('Accepted invalid '+str(args))

if __name__=='__main__':unittest.main()
