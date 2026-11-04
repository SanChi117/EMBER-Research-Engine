"""Run with: python -m unittest discover -s research/market_structure_replay_20261104 -p 'test*.py'."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import Bar, ClosedTF, Settings, future_outcomes, read_csv, replay

MS = 900_000


def sample(n=700, symbol='BTCUSDT'):
    rows = []
    for i in range(n):
        # Deterministic oscillation with occasional engineered sweeps; no outcome assumptions.
        close = 100 + 1.9 * __import__('math').sin(i / 11) + .6 * __import__('math').sin(i / 3)
        open_ = rows[-1].c if rows else 100
        rows.append(Bar(symbol, i * MS, open_, max(open_, close) + .25,
                        min(open_, close) - .25, close, 100 + i))
    return rows


class ReplayTests(unittest.TestCase):
    def test_future_mutation_cannot_change_prior_events(self):
        rows = sample()
        head = rows[:560]
        original = replay(head).events
        future = [Bar(x.symbol, x.t, x.o, x.h * 3, x.l / 3,
                      x.c * 2, x.v) for x in rows[560:]]
        combined = replay(head + future).events
        self.assertEqual(original, [e for e in combined if e['known_at'] <=
                                    '1970-01-06T20:00:00Z'])

    def test_completed_htf_only(self):
        tf = ClosedTF(4)
        rows = sample(8)
        for i in range(3):
            self.assertIsNone(tf.add(rows[i]))
        first = tf.add(rows[3])
        self.assertEqual(first['known_at'], 4 * MS)
        self.assertEqual(first['c'], rows[3].c)
        self.assertIsNone(tf.add(rows[4]))

    def test_future_labels_not_used_by_replay(self):
        rows = sample()
        before = replay(rows).events
        diagnostics = future_outcomes(rows, before)
        self.assertEqual(before, replay(rows).events)
        self.assertTrue(isinstance(diagnostics, list))

    def test_no_incomplete_future_labels(self):
        rows = sample()
        events = [{'event':'STRUCTURE_BREAK_CONFIRMED', 'symbol':'BTCUSDT',
                   'candidate_id':'x', 'known_at':__import__('replay').iso(rows[-2].known_at),
                   'side':1}]
        self.assertEqual(future_outcomes(rows, events), [])

    def test_gap_is_hard_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'missing.csv'
            with path.open('w', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['symbol','time','open','high','low','close','volume'])
                w.writerow(['BTCUSDT',0,100,101,99,100,1])
                w.writerow(['BTCUSDT',2*MS,100,101,99,100,1])
            with self.assertRaisesRegex(ValueError, 'gap'):
                read_csv(path)

    def test_multi_symbol_rejected(self):
        b = sample(20)
        b[-1] = Bar('ETHUSDT', b[-1].t, b[-1].o, b[-1].h, b[-1].l, b[-1].c, b[-1].v)
        with self.assertRaisesRegex(ValueError, 'cross-symbol'):
            replay(b)

    def test_bad_ohlc_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'bad.csv'
            path.write_text('symbol,time,open,high,low,close,volume\nBTCUSDT,0,100,99,98,100,1\n')
            with self.assertRaisesRegex(ValueError, 'invalid OHLCV'):
                read_csv(path)

    def test_short_prefix_match_boundaries(self):
        rows = sample(610)
        full = replay(rows).events
        for cutoff in (160, 320, 511, 608):
            end = rows[cutoff - 1].known_at
            got = replay(rows[:cutoff]).events
            selected = [e for e in full if __import__('datetime').datetime.fromisoformat(
                e['known_at'].replace('Z', '+00:00')).timestamp() * 1000 <= end]
            self.assertEqual(got, selected)


class VisionArchiveTests(unittest.TestCase):
    def test_archive_checksum_and_gap_validation(self):
        import hashlib
        import zipfile
        from import_vision_zip import convert
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            arc = root / 'BTCUSDT-15m-2026-09-01.zip'
            with zipfile.ZipFile(arc, 'w') as z:
                body = '\n'.join(f'{1788220800000+i*MS},100,101,99,100,22' for i in range(96))+'\n'
                z.writestr('BTCUSDT-15m-2026-09-01.csv', body)
            (root / (arc.name + '.CHECKSUM')).write_text(hashlib.sha256(arc.read_bytes()).hexdigest()+'  '+arc.name+'\n')
            dest = root/'normalized.csv'
            m = convert([arc], dest)
            self.assertEqual(m['rows'],96)
            self.assertEqual(m['origin_verdict'],'SAME_ORIGIN_CHECKSUM_ONLY')
            (root/(arc.name+'.CHECKSUM')).write_text('0'*64+'  '+arc.name+'\n')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                convert([arc],dest)


class AnnotationTests(unittest.TestCase):
    def test_empty_labels_rejected(self):
        from compare_annotations import compare
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'events.jsonl').write_text('')
            (p/'labels.csv').write_text('symbol,event,known_at\n')
            with self.assertRaisesRegex(ValueError,'no independent annotations'):
                compare(p/'events.jsonl', p/'labels.csv')

    def test_no_double_matching(self):
        from compare_annotations import compare
        import json
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'events.jsonl').write_text(''.join(json.dumps({
                'symbol':'BTCUSDT','event':'SWEEP_RETURN','known_at':t})+'\n'
                for t in ['2026-09-01T00:15:00Z','2026-09-01T00:30:00Z']))
            (p/'labels.csv').write_text('symbol,event,known_at\nBTCUSDT,SWEEP_RETURN,2026-09-01T00:20:00Z\n')
            r=compare(p/'events.jsonl',p/'labels.csv',15)
            self.assertEqual(r['results'][0]['matches'],1)
            self.assertEqual(r['results'][0]['false_positives'],1)


if __name__ == "__main__":
    unittest.main()