"""C78 adversarial tests; historic crypto source is immutable, never trades."""
import unittest,json
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
from c78_academic_causal_gate import assess,tally,C78Rejected

ROOT=Path(__file__).resolve().parents[1]
def pairs():
    a=json.loads((ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_text())
    b=json.loads((ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_text())
    lookup={(m["symbol"],c["original_c46_4h_parent_index"]):dict(c,symbol=m["symbol"])
            for m in b["markets"] for c in m["original_parent_source_cases"]}
    return [(dict(c,symbol=m["symbol"]),lookup[m["symbol"],c["original_c46_4h_parent_index"]])
            for m in a["markets"] for c in m["original_parent_source_cases"]]
FIX=pairs()
def sample(kind):
    for a,b in FIX:
        if kind=="selected" and a["first_source15m_event_fully_known_ms"] is not None:return deepcopy(a),deepcopy(b)
        if kind=="touch" and a["state"]=="NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN":return deepcopy(a),deepcopy(b)
        if kind=="unselected" and a["state"]=="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH":return deepcopy(a),deepcopy(b)
        if kind=="no_parent" and a["state"]=="NOT_NEW_1H_POI_SOURCE_BRANCH":return deepcopy(a),deepcopy(b)
    raise AssertionError("missing fixture "+kind)
class C78Tests(unittest.TestCase):
    def test_00_all_real_frozen_cases_no_trades(self):
        out=tally(tuple(assess(a,b) for a,b in FIX))
        self.assertEqual(out["contexts"],153)
        self.assertEqual(out["parent"]["SELECTED_1H_SOURCE"],35)
        self.assertEqual(out["source_5m"]["ALIGNED"],4)
        self.assertEqual(out["source_5m"]["OPPOSITE"],5)
        self.assertEqual(out["source_5m"]["AMBIGUOUS"],3)
        self.assertEqual(out["trades"],0)
    def test_01_no_parent(self):
        a,b=sample("no_parent");self.assertEqual(assess(a,b).parent,"NO_NEW_1H_POI")
    def test_02_unselected(self):
        a,b=sample("unselected");self.assertEqual(assess(a,b).parent,"UNSELECTED_1H_SOURCE")
    def test_03_raw_touch_not_valid_test(self):
        a,b=sample("touch");x=assess(a,b)
        self.assertEqual(x.physical_visit,"WICK_FIRST")
        self.assertFalse(x.author_valid_first_test)
    def test_04_15m_geometric_not_author_trigger(self):
        a,b=sample("selected");x=assess(a,b)
        self.assertFalse(x.author_15m_trigger)
        self.assertFalse(x.author_15m_vc)
        self.assertFalse(x.author_5m_vc)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_05_forbid_promoted_output(self):
        a,b=sample("selected");x=assess(a,b)
        with self.assertRaises(C78Rejected):tally((replace(x,author_entry=True),))

def bad(mod,kind="selected"):
    def check(self):
        a,b=sample(kind)
        mod(a,b)
        with self.assertRaises(C78Rejected):assess(a,b)
    return check

BAD={
"wrong_symbol":lambda a,b:a.update(symbol="FAKEUSDT"),
"wrong_side":lambda a,b:a.update(side="BOTH"),
"wrong_index":lambda a,b:a.update(original_c46_4h_parent_index=-1),
"mismatch_index":lambda a,b:b.update(original_c46_4h_parent_index=999),
"wrong_fork":lambda a,b:b.update(c67_route_a_source_fork_state="fake"),
"fake_ready":lambda a,b:a.update(readiness="READY"),
"fake_ready_c72":lambda a,b:b.update(readiness="READY"),
"fake_15m_trigger":lambda a,b:a.update(author_15m_trigger=True),
"fake_15m_vc":lambda a,b:a.update(author_15m_vc=True),
"fake_5m_vc":lambda a,b:b.update(author_5m_vc=True),
"fake_stronghl":lambda a,b:a.update(author_stronghl=True),
"fake_structural_stop":lambda a,b:b.update(author_structural_sl=True),
"fake_first_valid_test":lambda a,b:a.update(author_1h_poi_valid_first_test=True),
"route_b_leak":lambda a,b:a.update(route_b_idm_used=True),
"route_c_leak":lambda a,b:b.update(route_c_raid_bos_used=True),
"fake_orders":lambda a,b:a.update(orders=["BUY"]),
"fake_fills":lambda a,b:b.update(fills=["FILLED"]),
"bad_5m_state":lambda a,b:b.update(state="AUTHOR_VC"),
"bad_c73_5m_state":lambda a,b:a.update(source_first_5m_after_candidate_state="FORGED"),
"future_3m_touch":lambda a,b:a.update(original_first_source3m_touch_closed_ms=9999999999999),
"fake_prepoi_touch":lambda a,b:a.update(original_first_source3m_touch_closed_ms=1),
"fake_missing_first_rawid":lambda a,b:a.update(original_first_source3m_touch_id=None),
"fake_ep_bool":lambda a,b:a.update(episodes_before_first_15m_pattern=True),
"fake_15m_start_future":lambda a,b:a.update(first_source15m_event_pattern_start_ms=9999999999999),
"fake_15m_clock":lambda a,b:a.update(first_source15m_event_fully_known_ms=1),
"fake_5m_premature":lambda a,b:b.update(first_any_5m_event_known_ms=1),
"fake_5m_gate":lambda a,b:b.update(source_start_5m_gate_ms=2),
"fake_c71_15m":lambda a,b:b.update(c71_provisional_15m_known_ms=2),
"fake_15m_kind":lambda a,b:a.update(c71_first_any_15m_source_state="TRIGGER_AUTHOR"),
"fake_5m_kind_missing":lambda a,b:b.update(first_any_5m_kinds=[]),
"fake_5m_side_missing":lambda a,b:b.update(first_any_5m_sides=[]),
"unselected_to_selected":lambda a,b:a.update(state="NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID"),
}
for name,fn in BAD.items():
    setattr(C78Tests,"test_negative_"+name,bad(fn,"unselected" if name=="unselected_to_selected" else "selected"))
if __name__=="__main__":unittest.main()
