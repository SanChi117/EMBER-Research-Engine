"""Static checks of exact originals, plus one synthetic Python/pandas semantics probe.
No trading, no PnL, no claim of exhaustive causality proof.
"""
import ast
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
receipts = json.loads((ROOT / 'source_receipts.json').read_text())
result = []
for row in receipts:
    raw = (ROOT / 'sources' / (row['name'] + '.py')).read_bytes()
    # Tool-written copy may add a trailing newline; verify exact source variant.
    matched = None
    for source in (raw, raw[:-1] if raw.endswith(b'\n') else raw):
        blob = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
        if blob == row['blob']:
            matched = source
            break
    assert matched is not None, row['name']
    tree = ast.parse(matched.decode())
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    cls = next(c for c in classes if any(isinstance(b, ast.Name) and b.id == 'IStrategy' for b in c.bases))
    attrs = {}
    for n in cls.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try:
                attrs[n.targets[0].id] = ast.literal_eval(n.value)
            except (ValueError, TypeError):
                pass
    result.append(dict(row, sha_verified=True, syntax_valid=True, class_name=cls.name,
        attributes={k:attrs[k] for k in ('timeframe','can_short','startup_candle_count','stoploss',
            'use_exit_signal','position_adjustment_enable','max_open_trades') if k in attrs}))

mtf = (ROOT / 'sources/mtf_hybrid.py').read_text()
assert 'timeperiod=19200' in mtf and 'startup_candle_count = 500' in mtf
assert "shift(96)" in mtf
vol = (ROOT / 'sources/volatility.py').read_text()
assert 'trade.nr_of_successful_entries < 2' in vol
ftr = (ROOT / 'sources/ftr.py').read_text()
assert '(~self.use_session_filter.value) | dataframe["liquid_session"]' in ftr
semantics = []
for flag in (True, False):
    session = pd.Series([False, True])
    observed = ((~flag) | session).tolist()
    intended = ((not flag) | session).tolist()
    semantics.append({'python_bool_flag':flag,'session_input':[False,True],
        'original_expression':observed,'logical_not_comparator':intended})
assert semantics[0]['original_expression'] == [True, True]
assert semantics[0]['logical_not_comparator'] == [False, True]
record = {'scope':'source checks only; bool probe uses Python bool, parameter runtime type not proven',
          'pandas_version':pd.__version__, 'sources':result, 'ftr_session_probe':semantics,
          'mtf_minimum_history_observation':{'ema_bars':19200,'lag_bars':96,'startup_bars':500,
              'note':'EMA19200 at 15m is not an EMA200 calculated on daily closes; neutral fallback can admit signals while EMA missing.'},
          'volatility_adjustment_observation':'guard allows at most 2 successful entries per trade in inspected method, not unlimited DCA'}
(ROOT / 'A234_SOURCE_CHECK_RESULTS.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
