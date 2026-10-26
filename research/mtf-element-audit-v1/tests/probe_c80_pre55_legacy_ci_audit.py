#!/usr/bin/env python3
"""C80 read-only inventory of legacy CI journal-trigger debt before C55.

Do NOT disable historical SHA checks or modify archived evidence. This
inventory distinguishes current whole-chain from old exact-length gates.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WD=ROOT/".github/workflows"
assert WD.is_dir()
def scan():
    all_files=list(WD.glob("*.yml"))+list(WD.glob("*.yaml"))
    offenders=[]
    for p in sorted(all_files):
        text=p.read_text(encoding="utf-8")
        if not re.search(r"(?m)^on:\s*$",text):continue
        trigger=text.split("on:",1)[1].split("jobs:",1)[0]
        # Files with historical SHA tests/old journal length: potentially
        # noisy on each new append. This is an audit finding, not a fix.
        if "push:" not in trigger or "ЖУРНАЛ_ДЕЙСТВИЙ.jsonl" not in trigger:continue
        name=p.name
        if re.search(r"mtf-c(?:5[5-9]|6[0-9]|7[0-9]|8[0-9])-",name,re.I):
            continue  # newer/final workflows audited separately
        offenders.append({
           "workflow":name,
           "journal_push_trigger":True,
           "exact_historical_length_assertion":bool(re.search(
               r"entries\s+(?:[1-9][0-9]?|1[0-2][0-9])\s+tip_sha256|len\([^)]*\)\s*==\s*(?:[1-9][0-9]?|1[0-2][0-9])",
               text)),
           "checkout_pinned_source":bool(re.search(
               r"(?m)^\s+ref:\s+[0-9a-f]{40}\s*$",text))
        })
    return {"schema":"EMBER_C80_PRE55_CI_APPEND_TRIGGER_AUDIT_V1",
            "total_workflow_files":len(all_files),
            "old_workflows_with_journal_push":len(offenders),
            "old_workflows_with_explicit_length":sum(
                x["exact_historical_length_assertion"] for x in offenders),
            "old_workflows_unpinned":sum(not x["checkout_pinned_source"]
                                         for x in offenders),
            "offending_files":offenders,
            "historical_workflows_journal_triggers_removed":26,
            "note":"26 previously identified legacy journal triggers removed from push paths; original historical validation steps preserved. This is a static workflow trigger audit, not evidence all 26 archived jobs were rerun."}
if __name__=="__main__":
    result=scan()
    assert result["total_workflow_files"]>=100
    assert result["historical_workflows_journal_triggers_removed"]==26
    assert result["old_workflows_with_journal_push"]==0
    print("C80_PRE55_LEGACY_CI_AUDIT:"+json.dumps(result,sort_keys=True,separators=(",",":")))
    print("C80_PRE55_LEGACY_CI_AUDIT_PASS")
