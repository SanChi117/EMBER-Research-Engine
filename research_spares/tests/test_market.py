import unittest
from ember_spares.types import Candle, Evidence
from ember_spares.market import (
    asof_evidence, join_at_decision, Book, orderbook_imbalance, microprice,
    maker_fill_certainty, QueueEvidence, FillCertainty, BarOutcome, classify_bracket_bar,
    OrderSnapshot, OrderState, transition_order,
)


def candle(o=100, h=105, l=95, c=102, *, t=100, volume=100):
    return Candle(t,t+60,o,h,l,c,volume,t+60)


class MarketTest(unittest.TestCase):
    def test_evidence_available_not_event_time(self):
        past=Evidence(100,105,1,"exchange")
        late=Evidence(101,200,2,"exchange")
        self.assertEqual(asof_evidence([late,past],150),past)
        self.assertEqual(asof_evidence([late,past],201),late)
        self.assertEqual(asof_evidence([past],201,max_age=50),None)
        self.assertEqual(asof_evidence([past],106,max_age=1),past)

    def test_asof_join_missing(self):
        e=Evidence(10,11,1.1,"source")
        self.assertEqual(join_at_decision({"oi":[e],"funding":[]},11),{"oi":e,"funding":None})
        with self.assertRaises(ValueError): asof_evidence([e],11,-1)

    def test_ohlcv_rejects_nonclosed_and_bad(self):
        with self.assertRaises(ValueError): Candle(100,160,110,105,99,100,5,160)
        with self.assertRaises(ValueError): Candle(100,160,100,105,99,102,5,140)
        with self.assertRaises(ValueError): Candle(100,160,100,105,99,102,-5,160)

    def test_book_microprice(self):
        b=Book(100,102,30,10,10,11)
        self.assertAlmostEqual(orderbook_imbalance(b),.5)
        self.assertAlmostEqual(microprice(b),101.5)
        with self.assertRaises(ValueError): Book(102,100,2,1,10,11)

    def test_queue_conservative(self):
        self.assertEqual(maker_fill_certainty(QueueEvidence(None,100),5),FillCertainty.UNKNOWN)
        self.assertEqual(maker_fill_certainty(QueueEvidence(10,14,True),5),FillCertainty.UNKNOWN)
        self.assertEqual(maker_fill_certainty(QueueEvidence(10,15,True),5),FillCertainty.CONFIRMED)
        with self.assertRaises(ValueError): maker_fill_certainty(QueueEvidence(-1,10,True),5)

    def test_bracket_ambiguity(self):
        self.assertEqual(classify_bracket_bar(candle(),"long",96,104),BarOutcome.AMBIGUOUS)
        self.assertEqual(classify_bracket_bar(candle(),"short",104,96),BarOutcome.AMBIGUOUS)
        self.assertEqual(classify_bracket_bar(candle(h=102,l=98),"long",96,104),BarOutcome.NEITHER)
        self.assertEqual(classify_bracket_bar(candle(h=102,l=95),"long",96,104),BarOutcome.STOP)
        self.assertEqual(classify_bracket_bar(candle(o=95,h=100,l=94,c=99),"long",96,104),BarOutcome.GAP_STOP)
        self.assertEqual(classify_bracket_bar(candle(o=106,h=107,l=100,c=101),"long",96,104),BarOutcome.GAP_TARGET)
        self.assertEqual(classify_bracket_bar(candle(o=105,h=107,l=100,c=101),"short",104,96),BarOutcome.GAP_STOP)
        with self.assertRaises(ValueError): classify_bracket_bar(candle(),"long",105,104)

    def test_order_lifecycle(self):
        a=OrderSnapshot("ord1",0,20,10)
        b=transition_order(a,"FILL",10,3)
        self.assertEqual((b.executed,b.state),(3,OrderState.PARTIAL))
        c=transition_order(b,"FILL",11,7)
        self.assertEqual(c.state,OrderState.FILLED)
        with self.assertRaises(ValueError): transition_order(c,"FILL",12,1)
        with self.assertRaises(ValueError): transition_order(a,"FILL",20,1)
        with self.assertRaises(ValueError): transition_order(a,"EXPIRE",19)
        self.assertEqual(transition_order(b,"EXPIRE",20).state,OrderState.EXPIRED)
        self.assertEqual(transition_order(a,"REJECT",11).state,OrderState.REJECTED)
        self.assertEqual(transition_order(a,"CANCEL",11).state,OrderState.CANCELLED)
        with self.assertRaises(ValueError): transition_order(a,"FILL",5,11)


if __name__ == "__main__": unittest.main()
