"""Strict OFFLINE converter for Binance Vision USD-M Futures 15m ZIP archives.

No network calls and no fallback to spot or coin-m data.
Input paths MUST come from data/futures/um/{daily,monthly}/klines/{symbol}/15m/ .
A same-origin .CHECKSUM file is an integrity check, not publisher authentication.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from replay import Bar, STEP_MS, iso, read_csv

NAME = re.compile(r'^(?P<symbol>[A-Z0-9]+)-15m-(?:\d{4}-\d{2}|\d{4}-\d{2}-\d{2})\.zip$')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for piece in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(piece)
    return digest.hexdigest()


def convert(paths: list[Path], dest: Path, *, require_checksum: bool = True) -> dict[str, Any]:
    if not paths:
        raise ValueError('no archive paths')
    rows: dict[int, Bar] = {}
    receipts = []
    symbol: str | None = None
    for path in sorted(paths):
        match = NAME.fullmatch(path.name)
        if not match:
            raise ValueError(f'not USD-M 15m archive filename: {path.name}')
        name_sym = match.group('symbol')
        if symbol is not None and symbol != name_sym:
            raise ValueError('mixed symbols')
        symbol = name_sym
        digest = sha256(path)
        sidecar = Path(str(path) + '.CHECKSUM')
        if require_checksum:
            if not sidecar.exists():
                raise ValueError(f'checksum missing: {sidecar}')
            declared = sidecar.read_text(encoding='utf-8').split()[0].lower()
            if not re.fullmatch('[0-9a-f]{64}', declared) or declared != digest:
                raise ValueError(f'checksum mismatch: {path}')
        expected_member = path.name[:-4] + '.csv'
        with zipfile.ZipFile(path) as z:
            if z.namelist() != [expected_member]:
                raise ValueError(f'unexpected ZIP member(s): {path.name}')
            with z.open(expected_member) as stream:
                reader = csv.reader(io.TextIOWrapper(stream, encoding='utf-8-sig', newline=''))
                count = 0
                for line in reader:
                    if not line or line[0].strip() in ('open_time', 'Open time', 'timestamp'):
                        continue
                    if len(line) < 6:
                        raise ValueError(f'short Binance kline in {path}')
                    t = int(line[0]); b = Bar(name_sym, t, *map(float, line[1:6]))
                    if t in rows:
                        raise ValueError(f'duplicate timestamp {t} in {path.name}')
                    if t % STEP_MS or min(b.o, b.h, b.l, b.c) <= 0 or b.v < 0 or b.h < max(b.o,b.c) or b.l > min(b.o,b.c):
                        raise ValueError(f'invalid kline in {path.name}')
                    rows[t] = b; count += 1
                if count == 0:
                    raise ValueError(f'empty archive: {path.name}')
        receipts.append({'name': path.name, 'sha256': digest, 'rows': count,
                         'same_origin_checksum_pass': require_checksum})
    ordered = [rows[t] for t in sorted(rows)]
    for i in range(1, len(ordered)):
        if ordered[i].t - ordered[i-1].t != STEP_MS:
            raise ValueError(f'gap between {iso(ordered[i-1].t)} and {iso(ordered[i].t)}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('w', encoding='utf-8', newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['symbol','time','open','high','low','close','volume'])
        for b in ordered:
            writer.writerow([b.symbol,b.t,b.o,b.h,b.l,b.c,b.v])
    verified, normalized_sha = read_csv(dest)
    assert len(verified)==len(ordered)
    manifest={'symbol':symbol, 'normalized_csv':str(dest), 'normalized_csv_sha256':normalized_sha,
              'rows':len(ordered), 'first_open':iso(ordered[0].t),
              'last_closed_at':iso(ordered[-1].known_at),
              'archive_receipts':receipts,
              'origin_verdict':'SAME_ORIGIN_CHECKSUM_ONLY' if require_checksum else 'UNVERIFIED_ORIGIN',
              'warning':'Same-origin SHA256 does NOT independently attest Binance as publisher.'}
    manifest_file=Path(str(dest)+'.manifest.json')
    manifest_file.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return manifest


def main() -> None:
    p=argparse.ArgumentParser(description='Convert downloaded Binance Vision USD-M 15m ZIPs into strict offline research CSV')
    p.add_argument('--zip',nargs='+',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--allow-unverified',action='store_true',help='NO publisher integrity claim')
    a=p.parse_args()
    print(json.dumps(convert(a.zip,a.out,require_checksum=not a.allow_unverified),ensure_ascii=False))


if __name__ == '__main__':
    main()