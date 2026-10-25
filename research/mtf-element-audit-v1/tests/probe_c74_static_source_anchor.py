#!/usr/bin/env python3
"""Independent C74 contract countercheck, no Binance/network required."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d05"))
from c74_author_academic_golden_failclosed import (
    C73_SHA, PINNED_AUTHOR_CRYPTO_GOLDENS, evaluate_author_academic_golden)
from test_c74_author_academic_golden_failclosed import base
p = ROOT / "evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == C73_SHA and len(b) == 303327
d = json.loads(b)
assert d["source_4h_C46_parent_count"] == 153
assert sum(d["original3m_new1h_poi_first_visit_source_state_totals"].values()) == 153
assert (d["orders"], d["fills"], d["trades"]) == (0, 0, 0)
assert not PINNED_AUTHOR_CRYPTO_GOLDENS
x = evaluate_author_academic_golden(base())
assert x.readiness == "NOT_TRADE_READY"
assert x.author_status == "NOT_VERIFIED"
assert x.academic_route_fork == "UNRESOLVED"
assert x.orders == x.trades == ()
print("C74_FROZEN_C73_SHA_STATIC_CONTRACT_NO_GOLDEN_PASS")
