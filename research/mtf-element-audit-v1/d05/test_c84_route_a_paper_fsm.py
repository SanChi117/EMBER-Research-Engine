"""C84 original 153-case archive tests and route A adversarial transition tests."""
import json,unittest
from pathlib import Path
from dataclasses import replace
from c84_route_a_paper_fsm import Event,State,C84Rejected,advance,simulate,original153_projection,summarize
from c83_owner_course_text_crosswalk import C83Rejected
ROOT=Path(__file__).resolve().parents[1]
A=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
B=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
C=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
e=lambda name,clock,kind="":Event(name,clock,kind)
FULL=[e("4H_POI",10,"SNR"),e("4H_FIRST_TEST",20),
      e("1H_NEW_POI",30,"RB_RAID"),e("1H_TOUCH",40),
      e("1H_FIRST_TEST",50),e("15M_TRIGGER",60,"SSL_RAID"),
      e("5M_VC",70,"SNR")]

class TestRealOriginalCrypto(unittest.TestCase):
    def test_01_all153(self):
        x=original153_projection(A,B,C)
        self.assertEqual(len(x),153)
        self.assertEqual(summarize(x)["priority"],{"0":12,"1":23,"2":71,"3":47})
    def test_02_original12_5m_types(self):
        r=summarize(original153_projection(A,B,C))
        self.assertEqual(r["observations"]["SOURCE_5M_ALIGNED"],4)
        self.assertEqual(r["observations"]["SOURCE_5M_OPPOSITE"],5)
        self.assertEqual(r["observations"]["SOURCE_5M_AMBIGUOUS"],3)
    def test_03_source_not_entry(self):
        r=original153_projection(A,B,C)
        self.assertFalse(any(x["entry_allowed"] or x["orders"] or x["trades"] for x in r))
        self.assertEqual(summarize(r)["author_accepted_transitions"],0)
    def test_04_first_and_repeat_visits(self):
        r=original153_projection(A,B,C)
        self.assertEqual(sorted(x["source_visits"] for x in r if x["priority"]==0),[1]*9+[2,2,4])
    def test_05_identical_replay(self):
        self.assertEqual(original153_projection(A,B,C),original153_projection(A,B,C))
    def test_06_c73_mutated_sha_rejected(self):
        with self.assertRaises(C83Rejected):original153_projection(A+b"x",B,C)
    def test_07_c72_mutated_sha_rejected(self):
        with self.assertRaises(C83Rejected):original153_projection(A,B+b"x",C)
    def test_08_c81_modified_rejected(self):
        with self.assertRaises(C83Rejected):original153_projection(A,B,C+b"x")
    def test_09_forged_author_source_rejected(self):
        q=json.loads(C);q[0]["author_verified"]=True
        with self.assertRaises(C83Rejected):original153_projection(A,B,json.dumps(q).encode())
    def test_10_future5m_before15m_rejected(self):
        q=json.loads(C);q[0]["first5m_known_ms"]=q[0]["source15m_known_ms"]-1
        with self.assertRaises(C83Rejected):original153_projection(A,B,json.dumps(q).encode())
    def test_11_trades_spoof_in_output_rejected(self):
        r=original153_projection(A,B,C);r[0]["trades"]=["FAKE"]
        with self.assertRaises(C84Rejected):summarize(r)

class TestAcademicSimulation(unittest.TestCase):
    def test_12_complete_trigger_then5m(self):
        r=simulate(FULL)
        self.assertEqual(r.phase,"SCENARIO_ONLY")
        self.assertFalse(r.author_verified or r.entry_allowed or r.orders or r.trades)
    def test_13_no_trigger_direct15m_vc(self):
        r=simulate(FULL[:5]+[e("15M_DIRECT_VC",60,"IMB")])
        self.assertEqual(r.phase,"SCENARIO_ONLY")
    def test_14_4h_1h_trigger15m_vc(self):
        r=simulate(FULL[:2]+[e("1H_TRIGGER",30,"BSL_RAID"),
                 e("15M_VC_AFTER_1H_TRIGGER",40,"SNR")])
        self.assertEqual(r.phase,"SCENARIO_ONLY")
    def test_15_4h_raid_separate_1h_new_poi(self):
        r=simulate([FULL[0],e("4H_RAID",20)]+FULL[2:])
        self.assertEqual(r.phase,"SCENARIO_ONLY")
    def test_16_observed_geometry_no_transition(self):
        s=advance(State(),replace(FULL[0],status="SOURCE_TECHNICAL"))
        self.assertEqual(s.phase,"START")
        with self.assertRaises(C84Rejected):advance(s,FULL[1])
    def test_17_unknown_no_transition(self):
        s=simulate([replace(FULL[0],status="UNKNOWN")])
        self.assertEqual(s.phase,"START")
    def test_18_forged_owner_label_rejected(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],status="AUTHOR_VERIFIED")])
    def test_19_forged_owner_media_rejected(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],purported_author_media=True)])
    def test_20_route_b_rejected(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],route="B")])
    def test_21_route_c_rejected(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],route="C")])
    def test_22_same_time_not_closed(self):
        with self.assertRaises(C84Rejected):simulate([FULL[0],replace(FULL[1],close_ms=10)])
    def test_23_future5m_before15m(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:-1]+[replace(FULL[-1],close_ms=59)])
    def test_24_invalid_first_test_without_touch(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:3]+[FULL[4]])
    def test_25_revisit_not_first_test(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:4]+[e("1H_TOUCH",45),FULL[4]])
    def test_26_direct5m_without15m_trigger(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:5]+FULL[-1:])
    def test_27_direct15m_vc_after_trigger(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:-1]+[e("15M_DIRECT_VC",70,"SNR")])
    def test_28_vc_kind_unsupported_rb(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:-1]+[e("5M_VC",70,"RB")])
    def test_29_rb_requires_raid_or_imb(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:2]+[e("1H_NEW_POI",30,"RB")])
    def test_30_nested4h1h_imb_rejected(self):
        with self.assertRaises(C84Rejected):
            simulate([e("4H_POI",10,"IMB"),FULL[1],e("1H_TRIGGER",30,"ELIGIBLE_IMB")])
    def test_31_nested1h15m_imb_uncertified(self):
        x=simulate(FULL[:2]+[e("1H_NEW_POI",30,"IMB")]+FULL[3:5]+
                   [e("15M_TRIGGER",60,"ELIGIBLE_IMB"),FULL[-1]])
        self.assertEqual(x.phase,"SCENARIO_ONLY")
        self.assertFalse(x.author_verified)
    def test_32_missing_source_bar(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],missing_bars=True)])
    def test_33_data_gap(self):
        with self.assertRaises(C84Rejected):simulate([e("DATA_GAP",10)])
    def test_34_invalidation_terminal(self):
        with self.assertRaises(C84Rejected):simulate([FULL[0],e("INVALIDATE",20),e("4H_FIRST_TEST",30)])
    def test_35_forged_trade_state(self):
        with self.assertRaises(C84Rejected):advance(replace(State(),orders=("BUY",)),FULL[0])
    def test_36_1h_trigger_no_5m_shortcut(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:2]+[e("1H_TRIGGER",30,"SSL_RAID"),e("5M_VC",40,"SNR")])
    def test_37_4h_raid_cannot_1h_trigger(self):
        with self.assertRaises(C84Rejected):simulate([FULL[0],e("4H_RAID",20),e("1H_TRIGGER",30,"SSL_RAID")])
    def test_38_status_outside_enum(self):
        with self.assertRaises(C84Rejected):simulate([replace(FULL[0],status="AUTHOR_RULE")])
    def test_39_after_terminal_no_extra_signal(self):
        with self.assertRaises(C84Rejected):simulate(FULL+[e("1H_TOUCH",80)])
    def test_40_wrong_15m_trigger_class(self):
        with self.assertRaises(C84Rejected):simulate(FULL[:5]+[e("15M_TRIGGER",60,"RB")])

if __name__=="__main__":unittest.main()
