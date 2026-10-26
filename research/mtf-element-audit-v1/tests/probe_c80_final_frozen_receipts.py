#!/usr/bin/env python3
"""C80 acceptance: no fake owner goldens, all 26 old CI append triggers fixed."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"d05"),str(ROOT/"tests")]
from c80_owner_golden_intake import PINNED_AUTHOR_CASE_ATTESTATIONS
from probe_c80_pre55_legacy_ci_audit import scan
d=json.loads((ROOT/"evidence/c80/C80_ORIGINAL153_OWNER_GOLDEN_INTAKE_ZERO_AND_PRE55_CI_AUDIT.json").read_text())
assert d["schema"]=="EMBER_C80_ORIGINAL153_OWNER_GOLDEN_INTAKE_AND_PRE55_CI_AUDIT_V1"
s=d["original_market_source"]
assert s["frozen_crypto_contexts_checked"]==153
assert s["synthetic_negative_claims_reviewed"]==153
assert s["original_source_15m_positive_hypotheses_screened"]==12
assert s["authentic_owner_positive_goldens"]==s["authentic_owner_negative_goldens"]==0
assert s["original_archive_zip_retrieval_this_cycle"] is False
assert not PINNED_AUTHOR_CASE_ATTESTATIONS
assert hashlib.sha256((ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()).hexdigest()==s["pinned_C73_sha256"]
blob=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
assert hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()==s["pinned_C72_git_blob_sha1"]
a=scan()
assert a["old_workflows_with_journal_push"]==0
assert d["CI_legacy_preC55"]["historical_workflows_with_removed_journal_push_triggers"]==26
assert d["CI_legacy_preC55"]["remaining_preC55_journal_push_triggers"]==0
assert d["CI_legacy_preC55"]["every_old_CI_automatically_reexecuted"] is False
assert d["adversarial"]["validation_cases_per_python"]==48
assert d["readiness"]=="PAPER_ONLY_NOT_TRADE_READY"
assert d["author_authenticated"]==d["orders"]==d["fills"]==d["trades"]==0
report=(ROOT/"cycles/B1_C80_AUTHOR_GOLDEN_INTAKE_ORIGINAL153_PRE55_CI_REPORT.md").read_text()
assert "48 тестов" in report and "26" in report and "NOT_TRADE_READY" in report
print("C80_FROZEN_SHA_SOURCE_AND_26_LEGACY_CI_INTEGRITY_PASS")
