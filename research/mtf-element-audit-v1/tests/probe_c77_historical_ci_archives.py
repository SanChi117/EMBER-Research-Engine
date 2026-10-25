"""C77 independent audit of C59-C73 historical CI checkpoint isolation."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[3]
WORKFLOWS=ROOT/".github/workflows"
EXPECTED={
59:("mtf-c59-A129-final-independent-129sha.yml","cc1b84746a068e0ef634e3ef0e0d67c7d6a99138"),
60:("mtf-c60-A130-final-independent-130sha.yml","3e23c3b78bb17a0326883c69770318a318ae4221"),
61:("mtf-c61-A131-independent-final-131sha-all-evidence.yml","ae0601d9aee84b0ca8b53b801cfdcde27d097e53"),
62:("mtf-c62-A132-independent-final-132sha.yml","86144d1f89ff801b4a93cf115775e4d66aac816d"),
63:("mtf-c63-A133-final-independent-133sha.yml","3fa2964b7889ebc9044963741ce587b264077dcc"),
64:("mtf-c64-A134-independent-final-134sha.yml","f9e1d924221586e612581232daae287c7188c33d"),
65:("mtf-c65-A135-independent-final-135sha.yml","9388d524f6eacc6dd14c32fd3d37104cfb4dc842"),
66:("mtf-c66-A136-independent-final-136sha.yml","b59145e7fb922cc18ff79473fdfe7936bcbc6a06"),
67:("mtf-c67-A137-final-independent-137sha.yml","a6d112b5d485620e9e598ae43b5954122a62ab17"),
68:("mtf-c68-A138-independent-final-138sha.yml","353f90d87cc995016eb88ef1bbe1fb7322226a7c"),
69:("mtf-c69-A139-independent-final-139sha.yml","ebe4c3f5540820c9fe40dd2298d05a2679f8eb06"),
70:("mtf-c70-A140-independent-final-140sha.yml","7e9bfb4c5b23d695b22079552b054cef9f2288c0"),
71:("mtf-c71-A141-final-independent-141sha.yml","7e0382c90d0ac58b87f1ab121d6cfeb363865217"),
72:("mtf-c72-A142-independent-final-142sha.yml","aee42e569ebe093ff92f4037bcf9e3750a961f13"),
73:("mtf-c73-A143-independent-final-143sha.yml","9ebbb9dffcac6d82e9af622b56e4b9590243d81e"),
}
def verify():
    assert len(EXPECTED)==15
    results=[]
    for c,(name,commit) in EXPECTED.items():
        p=WORKFLOWS/name
        raw=p.read_text(encoding="utf8")
        trigger=raw.split("permissions:",1)[0]
        assert "workflow_dispatch:" in trigger,(c,"no manual trigger")
        assert "push:" in trigger,(c,"missing self-test")
        assert name in trigger,(c,"no self workflow test")
        assert "ЖУРНАЛ_ДЕЙСТВИЙ.jsonl" not in trigger,(c,"legacy auto-append trigger")
        assert re.search(r"(?m)^          ref: "+commit+r"$",raw),(c,"unpinned checkout")
        assert "python tools/auditlog.py verify" in raw,(c,"missing historic full-chain")
        results.append({"cycle":"C"+str(c),"historical_audit_tip":"A"+str(c+70),
                        "pinned_commit":commit,"trigger":"self-change or manual"})
    print(json.dumps({"status":"C77_HISTORICAL_CI_ISOLATION_PASS",
      "count":len(results),"historical":results},sort_keys=True))
if __name__=="__main__":verify()
