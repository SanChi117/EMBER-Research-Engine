"""Render factual market-structure recognition counts, never PnL."""
import argparse
import json
from collections import Counter
from pathlib import Path

COLUMNS = ['ACCUMULATION_LOCKED', 'SWEEP_RETURN', 'FVG_AFTER_SWEEP',
           'STRUCTURE_BREAK_CONFIRMED', 'EXPIRED_NO_SWEEP',
           'EXPIRED_NO_STRUCTURE', 'REJECT_SWEEP_NO_CONFIRMED_PIVOT']


def report(audit_path: Path, markdown_path: Path) -> dict:
    obj = json.loads(audit_path.read_text(encoding='utf-8'))
    sources = obj['source_receipts']
    if len({x['symbol'] for x in sources}) != len(sources):
        raise ValueError('duplicate symbols in audit')
    sums = Counter()
    for x in sources:
        sums.update(x['events'])
    header = ['Монета', 'Свечи'] + COLUMNS
    lines = ['# EMBER Market Structure Replay — проверка распознавания', '',
             '**Статус:** CODE/REAL_CANDLE_SMOKE, НЕ экспертная истинность, НЕ торговля, НЕ PnL.', '',
             '| ' + ' | '.join(header) + ' |',
             '| ' + ' | '.join(['---'] * len(header)) + ' |']
    for x in sorted(sources, key=lambda y: y['symbol']):
        lines.append('| ' + ' | '.join([x['symbol'], str(x['bars'])] +
                    [str(x['events'].get(c, 0)) for c in COLUMNS]) + ' |')
    lines.append('| **ВСЕГО** | **' + str(sum(x['bars'] for x in sources)) +
                 '** | ' + ' | '.join('**' + str(sums[c]) + '**' for c in COLUMNS) + ' |')
    lines.extend(['', '**Содержательный итог:** число найденных событий не является accuracy.',
                  'Без независимой слепой экспертной разметки нет подтверждения, что BOS/AMD соответствуют графику.',
                  'Файлы futures OHLCV взяты из публичного Binance USDT-M connector. SHA256 исходных CSV и конфигурации есть в source_audit.json; независимой оригинальной Binance Vision ZIP/CHECKSUM аттестации этих samples нет.',
                  'Реальные ордера, PAPER, SMOKE, торговые настройки и прежние отрицательные тесты не менялись.', ''])
    markdown_path.parent.mkdir(parents=True,exist_ok=True)
    markdown_path.write_text('\n'.join(lines),encoding='utf-8')
    return {'sources':len(sources),'bars':sum(x['bars'] for x in sources),'events':dict(sums),
            'path':str(markdown_path)}


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(report(a.audit,a.out),ensure_ascii=False))