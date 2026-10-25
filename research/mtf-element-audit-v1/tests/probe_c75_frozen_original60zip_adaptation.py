#!/usr/bin/env python3
"""C75 independently bind adapted source labels to frozen C73 original60ZIP JSON.

No fresh archive downloads. It is a SHA-pinned static replay of 153 C73
research contexts, not an execution of trading strategy or proof of success.
"""
from pathlib import Path
import hashlib
import json
import sys
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d05"))
from c75_external_imb_first_visit_lifecycle import classify_c73_fork
from c74_author_academic_golden_failclosed import C73_SHA

source = ROOT / "evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == C73_SHA
assert len(raw) == 303327
data = json.loads(raw)
assert data["source_4h_C46_parent_count"] == 153
expected = {
    "NOT_NEW_1H_POI_SOURCE_BRANCH": 47,
    "NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH": 71,
    "NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN": 23,
    "NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID": 9,
    "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID": 3,
}
cases = [c for market in data["markets"] for c in market["original_parent_source_cases"]]
assert len(cases) == 153 and dict(Counter(c["state"] for c in cases)) == expected
assert data["original3m_new1h_poi_first_visit_source_state_totals"] == expected
translated = Counter(classify_c73_fork(c)[0] for c in cases)
assert dict(translated) == {
    "SOURCE_INSUFFICIENT": 141, "SOURCE_FIRST_VISIT": 9, "SOURCE_REVISIT": 3}
assert data["author_verified_routeA_15m_trigger_or_15m_vc_split"] == 0
assert (data["orders"], data["fills"], data["trades"]) == (0, 0, 0)
print(json.dumps({
    "mode": "PINNED_FROZEN_C73_STATIC_REVIEW_NOT_FRESH_ZIP_REPLAY",
    "source_sha256": C73_SHA, "cases": 153,
    "adapted_technical_groups": dict(translated),
    "owner_15m_trigger_vs_vc_resolved": 0,
    "author_crypto_goldens": 0, "trades": 0,
    "readiness": "NOT_TRADE_READY"
}, sort_keys=True))
