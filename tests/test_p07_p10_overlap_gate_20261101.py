"""Independent source logic overlap audit, deterministic real-data receipt."""
import importlib.util
from pathlib import Path


def test_p07_p10_signal_cooccurrence_without_future_information():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"p07_p10_overlap_gate_20261101.py")
    spec=importlib.util.spec_from_file_location("source_overlap_p07_p10",str(p))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    x=module.audit()
    assert x["no_profitability_or_trade_outcomes"]
    assert x["original_counts"]=={"P07":134,"P10":54}
    assert x["source_P07_expired_signals_preserved"]==16
    assert x["same_symbol_same_direction_P10_prior_or_same_P07_by_hours"]=={
        "0":4,"3":18,"6":24,"12":31,"24":36,
    }
    assert x["P07_signals_absent_P10_prior_3h"]==116
    assert x["P07_signals_absent_P10_prior_12h"]==103
