"""MSR-03 causal scope tests. Not trading tests."""
from __future__ import annotations
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from replay import Bar, iso, replay
from scope_audit_v03 import scope_rows, inspect_blind
from htf_pivot_compare_v02 import last_confirmed_swings

MS=900_000


def synthetic(n=900):
    import math
    bars=[]
    for i in range(n):
        o=bars[-1].c if bars else 100.0
        c=100+math.sin(i/18)*2+math.sin(i/4)*.4
        bars.append(Bar('BTCUSDT',i*MS,o,max(o,c)+.2,min(o,c)-.2,c,100))
    return bars


class CausalScopeTests(unittest.TestCase):
    def test_scope_does_not_mutate_original_events(self):
        b=synthetic()
        original=replay(b).events
        scoped=scope_rows(b,original)
        self.assertEqual(original,replay(b).events)
        self.assertEqual(len(scoped),sum(x['event']=='STRUCTURE_BREAK_CONFIRMED' for x in original))

    def test_scope_suffix_mutation_cannot_change_prefix(self):
        a=synthetic()
        original=replay(a[:650]).events
        first=scope_rows(a[:650],original)
        later=[Bar(x.symbol,x.t,x.o,x.h+10,x.l-10,x.c,x.v) for x in a[650:]]
        mutated=replay(a[:650]+later).events
        second=scope_rows(a[:650]+later,mutated)
        end=iso(a[649].known_at)
        self.assertEqual(first,[x for x in second if x['bos_at']<=end])

    def test_unknown_pivots_remain_unknown_not_false(self):
        a=synthetic(300)
        snapshots=last_confirmed_swings(a,16)
        self.assertEqual(snapshots[iso(a[0].known_at)],(None,None))

    def test_blind_packet_missing_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'cases').mkdir()
            with self.assertRaisesRegex(ValueError,'180'):
                inspect_blind(Path(tmp))


if __name__=="__main__":
    unittest.main()
