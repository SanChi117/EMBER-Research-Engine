"""Blind annotation concordance audit: deterministic one-to-one time matching.

Reference labels are manually prepared BEFORE seeing future outcomes.
This measures agreement with labels, NOT objective correctness of market structure.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def epoch_ms(s: str) -> int:
    dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('label time must be timezone-aware')
    return int(dt.timestamp() * 1000)


def compare(events_jsonl: Path, labels_csv: Path, tolerance_minutes: int = 15) -> dict:
    if tolerance_minutes < 0:
        raise ValueError('invalid tolerance')
    event_rows = [json.loads(line) for line in events_jsonl.read_text(encoding='utf-8').splitlines() if line]
    with labels_csv.open(encoding='utf-8-sig', newline='') as fh:
        labels = list(csv.DictReader(fh))
    if not labels:
        raise ValueError('no independent annotations; cannot score correctness')
    for item in labels:
        if not all(k in item for k in ('symbol','event','known_at')):
            raise ValueError('labels require symbol,event,known_at columns')
    keys = sorted({(x['symbol'], x['event']) for x in labels}
                  | {(x['symbol'], x['event']) for x in event_rows})
    results = []
    for symbol, kind in keys:
        a = sorted([epoch_ms(x['known_at']) for x in labels if x['symbol'] == symbol and x['event'] == kind])
        b = sorted([epoch_ms(x['known_at']) for x in event_rows if x['symbol'] == symbol and x['event'] == kind])
        # Closest permissible match, one-to-one, with equal-price chronology rule.
        candidates = sorted((abs(x-y), i, j) for i,x in enumerate(a) for j,y in enumerate(b)
                            if abs(x-y) <= tolerance_minutes*60000)
        matched_a=set();matched_b=set()
        for _,i,j in candidates:
            if i not in matched_a and j not in matched_b:
                matched_a.add(i);matched_b.add(j)
        tp=len(matched_a);fp=len(b)-tp;fn=len(a)-tp
        results.append({'symbol':symbol,'event':kind,'labels':len(a),'detections':len(b),
                        'matches':tp,'false_positives':fp,'missed_labels':fn,
                        'precision':None if tp+fp==0 else round(tp/(tp+fp),4),
                        'recall':None if tp+fn==0 else round(tp/(tp+fn),4)})
    return {'evidence':'ANNOTATION_AGREEMENT_NOT_MARKET_TRUTH',
            'labels_sha256':hashlib.sha256(labels_csv.read_bytes()).hexdigest(),
            'events_sha256':hashlib.sha256(events_jsonl.read_bytes()).hexdigest(),
            'tolerance_minutes':tolerance_minutes,'results':results}


def main() -> None:
    p=argparse.ArgumentParser(description='Compare sealed causal events with blind annotations')
    p.add_argument('--events',type=Path,required=True)
    p.add_argument('--labels',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--tolerance-minutes',type=int,default=15)
    a=p.parse_args()
    r=compare(a.events,a.labels,a.tolerance_minutes)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'groups':len(r['results']),'out':str(a.out)},ensure_ascii=False))

if __name__=='__main__':
    main()