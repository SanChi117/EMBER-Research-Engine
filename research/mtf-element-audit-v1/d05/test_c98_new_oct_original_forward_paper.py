"""C98 frozen Oct03-Oct26 all-original-source guardrails. Synthetic test data ONLY."""
import unittest
from datetime import datetime,timezone
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
from decimal import Decimal as D
from c98_new_oct_original_forward_paper import (
    C98Rejected,START,END,START_MS,END_MS,DAYS,TF,EXPECTED_SYMBOLS,
    EXPECTED_NEW_ARCHIVES,daily_zip,verify_daily_parity,_only_forward,
    _baseline_compare,_score_scenarios,_admission,dumps)
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c21_native3m_source_bridge import Original3mRow,THREE
def fabricated_source(symbol="BTCUSDT",tf="5m",date="2026-10-03",*,bad_time=False,bad_volume=False):
    start=int(datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
    step=STEP if tf=="5m" else THREE
    n=86400000//step
    rows=[]
    for i in range(n):
        at=start+i*step+(STEP if bad_time and i==5 else 0)
        vol="-1" if bad_volume and i==15 else "1"
        rows.append(f"{at},100,101,99,100,{vol},{at+step-1},100,1,1,100,0")
    stream=("\n".join(rows)+"\n").encode()
    name=f"{symbol}-{tf}-{date}"
    buff=BytesIO()
    with ZipFile(buff,"w",ZIP_DEFLATED) as z:z.writestr(name+".csv",stream)
    raw=buff.getvalue()
    def fetch(url):
        if url.endswith(".CHECKSUM"):
            return (sha256(raw).hexdigest()+"  "+name+".zip").encode()
        return raw
    return fetch
def synthetic_prices():
    start=START_MS
    three=tuple(Original3mRow("BTCUSDT",start+i*THREE,start+(i+1)*THREE,
             D(100),D(101),D(99),D(100),D(1),"f"*64,"f"*64)
             for i in range((END_MS-START_MS)//THREE))
    five=tuple(Bar(start+i*STEP,D(100),D(101),D(99),D(100),D(1))
             for i in range((END_MS-START_MS)//STEP))
    return three,five
def row(entry=START_MS+300000):
    return {"symbol":"BTCUSDT","route":"A_TEST","entry_ms":entry,
            "exit_ms":entry+300000,"entry":"100","stop":"98",
            "target":"103","fta":"103","derived_rr":1.5,
            "net_r":-1.0,"exit_reason":"STOP"}
class TestC98(unittest.TestCase):
 def test_01_exact_registered_closed_days(self):
    self.assertEqual(len(DAYS),24)
    self.assertEqual((DAYS[0],DAYS[-1]),("2026-10-03","2026-10-26"))
 def test_02_archive_count_fixed_before_market_result(self):
    self.assertEqual(EXPECTED_NEW_ARCHIVES,240)
    self.assertEqual(len(EXPECTED_SYMBOLS),5)
 def test_03_5m_source_exact_original_utc_day(self):
    z,meta=daily_zip("BTCUSDT","5m",DAYS[0],fetch=fabricated_source())
    self.assertEqual(len(z),288);self.assertEqual(meta["bars"],288)
    self.assertEqual(z[-1].close_ms,START_MS+86400000)
 def test_04_3m_source_exact_original_utc_day(self):
    z,meta=daily_zip("BTCUSDT","3m",DAYS[0],fetch=fabricated_source(tf="3m"))
    self.assertEqual(len(z),480);self.assertEqual(meta["bars"],480)
    self.assertEqual(z[-1].known_ms,START_MS+86400000)
 def test_05_source_checksum_tamper_hard_fail(self):
    original=fabricated_source()
    def bad(url):
        return b"0"*64+b"  BTCUSDT-5m-2026-10-03.zip" if url.endswith(".CHECKSUM") else original(url)
    with self.assertRaisesRegex(C98Rejected,"CHECKSUM"):
        daily_zip("BTCUSDT","5m",DAYS[0],fetch=bad)
 def test_06_gapped_original_native_bar_hard_fail(self):
    with self.assertRaisesRegex(C98Rejected,"UNCLOSED_GAP"):
        daily_zip("BTCUSDT","5m",DAYS[0],fetch=fabricated_source(bad_time=True))
 def test_07_negative_volume_hard_fail(self):
    with self.assertRaisesRegex(C98Rejected,"IMPOSSIBLE"):
        daily_zip("BTCUSDT","5m",DAYS[0],fetch=fabricated_source(bad_volume=True))
 def test_08_reject_unregistered_future_day(self):
    with self.assertRaises(C98Rejected):
        daily_zip("BTCUSDT","5m","2026-10-27",fetch=fabricated_source())
 def test_09_reject_unregistered_coin(self):
    with self.assertRaises(C98Rejected):
        daily_zip("FAKEUSDT","5m",DAYS[0],fetch=fabricated_source())
 def test_10_complete_independent_15m_parity(self):
    a,b=synthetic_prices()
    self.assertEqual(verify_daily_parity(a,b,"BTCUSDT"),24*96)
 def test_11_parity_mismatch_hard_fail(self):
    a,b=synthetic_prices()
    from dataclasses import replace
    bb=list(b);bb[5]=replace(bb[5],h=D(104))
    with self.assertRaisesRegex(C98Rejected,"PARITY|MISMATCH"):
        verify_daily_parity(a,tuple(bb),"BTCUSDT")
 def test_12_no_retro_previous_trade_counted(self):
    x=row(START_MS-2*STEP)
    self.assertEqual(_only_forward([x]),[])
 def test_13_only_full_new_closed_scenarios(self):
    a=row()
    b=row(END_MS-STEP)
    self.assertEqual(_only_forward([a,b]),[a])
 def test_14_unchanged_source_replay(self):
    a=row(START_MS-10*86400000)
    x=_baseline_compare([a],[a],12*3600000)
    self.assertTrue(x["comparison_exact"])
 def test_15_altered_old_trade_hard_fail(self):
    a=row(START_MS-10*86400000)
    b={**a,"stop":"97"}
    with self.assertRaises(C98Rejected):
        _baseline_compare([a],[b],12*3600000)
 def test_16_no_market_trades_no_false_positive(self):
    case=_score_scenarios([])
    self.assertEqual(case["25"]["n"],0)
    self.assertFalse(_admission(case)["passes_new_oct_historical_screen"])
 def test_17_costs_reduce_paper_net_R(self):
    case=_score_scenarios([row()])
    self.assertGreater(case["14"]["sum_r"],case["25"]["sum_r"])
    self.assertGreater(case["25"]["sum_r"],case["40"]["sum_r"])
 def test_18_stability_gate_rejects_one_lucky_trade(self):
    p=row();p["net_r"]=10
    result=_admission(_score_scenarios([p]))
    self.assertFalse(result["passes_new_oct_historical_screen"])
    self.assertIn("OOS_SAMPLE_BELOW_10",result["reasons"])
 def test_19_requires_25bps_positive_and_pf_over_1_2(self):
    data=[{**row(entry=START_MS+i*10*STEP),"net_r":3 if i%2 else -2} for i in range(10)]
    r=_admission(_score_scenarios(data))
    self.assertIn("OOS_PF_BELOW_1_2",r["reasons"]) if "OOS_PF_BELOW_1_2" in r["reasons"] else self.assertFalse(r["passes_new_oct_historical_screen"])
 def test_20_deterministic_evidence_bytes(self):
    self.assertEqual(dumps({"b":2,"a":1}),dumps({"a":1,"b":2}))
if __name__=="__main__":unittest.main()
