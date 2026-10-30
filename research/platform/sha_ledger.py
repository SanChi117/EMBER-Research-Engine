"""Pure append-only SHA256 event-chain verifier. No exchange or order actions."""
from hashlib import sha256
import json

class LedgerError(ValueError):
    pass

GENESIS="0"*64

def canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()

def verify(events):
    previous=GENESIS
    seen=set()
    for i,item in enumerate(events,1):
        if not isinstance(item,dict) or "record_sha256" not in item:
            raise LedgerError("MISSING_SHA")
        payload={k:v for k,v in item.items() if k!="record_sha256"}
        if payload["seq"]!=i or payload["prev_sha256"]!=previous:
            raise LedgerError("BROKEN_CHAIN")
        if payload["event_id"] in seen:
            raise LedgerError("DUPLICATE_EVENT")
        if sha256(canonical(payload)).hexdigest()!=item["record_sha256"]:
            raise LedgerError("TAMPERED_PAYLOAD")
        seen.add(payload["event_id"])
        previous=item["record_sha256"]
    return previous

def extend(events, *, event_id, event_type, payload):
    if not event_id or not event_type or not isinstance(payload,dict):
        raise LedgerError("INVALID_EVENT")
    if any(item["event_id"]==event_id for item in events):
        raise LedgerError("DUPLICATE_EVENT")
    previous=verify(events)
    record={"seq":len(events)+1,"event_id":event_id,"event_type":event_type,
            "payload":payload,"prev_sha256":previous}
    return [*events,{**record,"record_sha256":sha256(canonical(record)).hexdigest()}]
