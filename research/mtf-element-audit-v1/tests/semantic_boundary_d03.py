#!/usr/bin/env python3
"""Falsification boundary: valid temporal edges can still be semantically false."""
import json,pathlib,sys,hashlib,argparse
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from strict_event_lineage_d03 import CausalEvent,EventLedger

def make(uid,kind,known,parent=(),evidence='SHA_UNVALIDATED'):
    return CausalEvent(uid,kind,'BTCUSDT','BINANCE','USDM_FUTURES','15m',1000,2000,known,parent,(evidence,))

def run():
    g=EventLedger();g.add(make('S','SOURCE',2000,evidence='NO_SUCH_SHA_OR_FILE'))
    g.add(make('P','POI',2050,('S',)))
    g.add(make('TRIGGER_A','TRIGGER',2100,('P',)))
    g.add(make('TRIGGER_B','TRIGGER',2150,('P',)))
    # The proof only says VC follows this *time-compatible ID*. It cannot
    # prove that the price geometry reacted specifically to trigger A or B.
    g.add(make('VC_MISATTRIBUTED','VC',2200,('TRIGGER_A',)))
    return dict(synthetic_scope=True,accepted_semantically_ambiguous_edge=True,
      accepted_nonexistent_evidence_id=True,graph_sha256=g.digest(),
      conclusion='D03 enforces graph/time/symbol invariants only. It cannot validate evidence bytes or whether an assigned VC actually belongs to that trigger.',
      followups=['D04 authenticated evidence dereferencing and source SHA','structural POI/RAID/VC/IDM positive and negative annotated fixtures'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
    result=run();pathlib.Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print('SEMANTIC_COUNTEREXAMPLE_CONFIRMED',result['accepted_semantically_ambiguous_edge'])
