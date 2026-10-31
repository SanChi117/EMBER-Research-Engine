import unittest
from ember_spares import parity_from_exports,invoke
from ember_spares.adapters import normalized_signal_rows,trade_report_rows

class OriginalEngineAdapters(unittest.TestCase):
    def test_parity_with_source_mapping(self):
        source=[{'UTC':'2026-01-02T00:00:00Z','Market':'SOLUSDT','Direction':'BUY','Entry':'100','SL':'98','TP':'104'}]
        fields={'decision_at':'UTC','symbol':'Market','side':'Direction','entry':'Entry','stop':'SL','target':'TP'}
        reimpl=[{'decision_at':'2026-01-02T00:00:00+00:00','symbol':'SOLUSDT','side':'long','entry':100,'stop':98,'target':104}]
        r=parity_from_exports(source,reimpl,original_source='pinned:original123',challenger_source='pinned:ember456',original_fields=fields)
        self.assertTrue(r['parity'])
        reimpl[0]['stop']=97
        self.assertFalse(parity_from_exports(source,reimpl,original_source='a',challenger_source='b',original_fields=fields)['parity'])
    def test_timezone_must_be_explicit(self):
        with self.assertRaises(ValueError):
            normalized_signal_rows([{'decision_at':'2026-01-02 00:00:00','symbol':'SOLUSDT','side':'long','entry':'100','stop':'99','target':'102'}],source='x')
    def test_trade_export(self):
        r=trade_report_rows([{'id':5,'pair':'SOL/USDT','close_date':'2026-01-02T00:00:00Z','profit_abs':'12.50'}],source='source')
        self.assertEqual(r[0].net_pnl_usdt,12.5)
    def test_invoke_parity_export(self):
        rec=[{'decision_at':100,'symbol':'SOLUSDT','side':'short','entry':100,'stop':101,'target':98}]
        r=invoke('Z38.parity_exports',{'original_rows':rec,'other_rows':rec,'original_source':'a','challenger_source':'b'})
        self.assertTrue(r['parity'])
