"""Read-only A233 archival audit; no shared-wallet backtest or trading.
Usage: python a233_audit.py evidence output
Inputs: GitHub artifact ZIPs 2025.zip and 2026.zip, downloaded without modification.
"""
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

EXPECTED = {
    '2025': 'bb1a20d559411458b8edcd04ebfe51b16263b1d36bbb2d24429760cac0a6e098',
    '2026': 'a2feb855954701193f82895820dc00c2dfa64c1a7ee270bab56ef9633bda0339',
}
SOURCE = '22ca6588bbd056e671783f676f1a4010cbfc1bb6'
COINS = ('BTC', 'ETH', 'SOL', 'LINK')

def closed_balance_dd(trades, capital):
    """Balance measured AFTER all closes at a timestamp; excludes unrealized PnL."""
    changes = defaultdict(float)
    for t in trades:
        changes[t['close_timestamp']] += t['profit_abs']
    balance = peak = capital
    dd = 0.0
    for stamp in sorted(changes):
        balance += changes[stamp]
        peak = max(peak, balance)
        dd = max(dd, (peak - balance) / peak)
    return dd * 100

def overlaps(trades):
    """Half-open position intervals [open,close); zero-duration trades excluded."""
    events = defaultdict(lambda: [0, 0.0])
    zero = 0
    for t in trades:
        start, end = t['open_timestamp'], t['close_timestamp']
        if end < start:
            raise ValueError('reversed trade interval')
        if start == end:
            zero += 1
            continue
        for stamp, direction in ((start, 1), (end, -1)):
            events[stamp][0] += direction
            events[stamp][1] += direction * t['stake_amount']
    active = max_active = 0
    stake = max_stake = 0.0
    multi_hours = 0.0
    stamps = sorted(events)
    for i, stamp in enumerate(stamps):
        active += events[stamp][0]
        stake += events[stamp][1]
        max_active = max(max_active, active)
        max_stake = max(max_stake, stake)
        if i + 1 < len(stamps) and active > 1:
            multi_hours += (stamps[i + 1] - stamp) / 3600000
    assert active == 0 and abs(stake) < 1e-5
    return {'max_simultaneous_positions': max_active,
            'hours_with_multiple_positions': multi_hours,
            'max_sum_original_stakes_usdt': max_stake,
            'zero_duration_trades_excluded_from_overlap': zero}

def main(root, out):
    groups = defaultdict(list)
    receipts = []
    seen = set()
    for year, digest in EXPECTED.items():
        raw = (root / (year + '.zip')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest, 'artifact SHA mismatch'
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            for name in sorted(outer.namelist()):
                match = re.search(r'(BTC|ETH|SOL|LINK)-fee(5|12p5).*\.zip$', name)
                if not match:
                    continue
                coin, fee = match.groups()
                key = (year, fee, coin)
                assert key not in seen
                seen.add(key)
                inner_raw = outer.read(name)
                with zipfile.ZipFile(io.BytesIO(inner_raw)) as arc:
                    source_name = next(n for n in arc.namelist() if n.endswith('_VideoDoubleMaFuturesStrategy.py'))
                    source = arc.read(source_name)
                    blob = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
                    assert blob == SOURCE, ('strategy differs', name, blob)
                    config = json.loads(arc.read(next(n for n in arc.namelist() if n.endswith('_config.json'))))
                    candidates = []
                    for n in arc.namelist():
                        if n.endswith('.json'):
                            j = json.loads(arc.read(n))
                            if isinstance(j, dict) and 'strategy' in j:
                                candidates.append(j['strategy']['VideoDoubleMaFuturesStrategy'])
                    assert len(candidates) == 1
                    m = candidates[0]
                trades = m['trades']
                assert m['starting_balance'] == 10000
                assert m['timeframe_detail'] == '5m'
                assert m['trading_mode'] == 'futures' and m['margin_mode'] == 'isolated'
                assert config['exchange']['pair_whitelist'] == [coin + '/USDT:USDT']
                assert config['max_open_trades'] == 1
                assert len(trades) == m['total_trades']
                total = math.fsum(t['profit_abs'] for t in trades)
                assert math.isclose(total, m['profit_total_abs'], abs_tol=1e-5)
                for t in trades:
                    assert not t['is_open'] and t['pair'] == coin + '/USDT:USDT'
                    assert t['leverage'] == 2
                    assert t['fee_open'] == t['fee_close'] == (0.0005 if fee == '5' else 0.00125)
                    assert math.isfinite(t['profit_abs'])
                    groups[(year, fee)].append(dict(t, coin=coin))
                receipts.append({'year': year, 'fee_bps': fee, 'coin': coin, 'zip': name,
                    'sha256': hashlib.sha256(inner_raw).hexdigest(), 'source_blob': blob,
                    'trades': len(trades), 'recomputed_profit_usdt': total,
                    'reported_profit_usdt': m['profit_total_abs']})
    assert seen == {(y, f, c) for y in EXPECTED for f in ('5', '12p5') for c in COINS}
    result = {'cycle': 'A233', 'scope': 'historical four separate wallets; not author portfolio, not new OOS',
              'source_blob': SOURCE, 'artifact_sha256': EXPECTED, 'receipts': receipts, 'results': {}}
    out.mkdir(parents=True, exist_ok=True)
    ledger = []
    for (year, fee), trades in sorted(groups.items()):
        pnl = math.fsum(t['profit_abs'] for t in trades)
        wins = math.fsum(max(t['profit_abs'], 0) for t in trades)
        losses = -math.fsum(min(t['profit_abs'], 0) for t in trades)
        top3 = sum(sorted((t['profit_abs'] for t in trades), reverse=True)[:3])
        result['results'][year + '_fee' + fee] = {
            'trades': len(trades), 'net_usdt': pnl, 'return_pct_on_40000': pnl / 400,
            'closed_trade_balance_drawdown_pct_NOT_MTM': closed_balance_dd(trades, 40000),
            'pooled_cash_profit_factor': wins / losses if losses else None,
            'top3_winners_usdt': top3, 'net_without_top3_diagnostic_usdt': pnl - top3,
            'funding_fees_reported_sum_NOT_added_again': sum(t.get('funding_fees', 0) for t in trades),
            **overlaps(trades),
            'author_BTC_ETH_archival_overlap_diagnostic': overlaps([t for t in trades if t['coin'] in ('BTC', 'ETH')]),
        }
        for t in sorted(trades, key=lambda t: (t['open_timestamp'], t['coin'])):
            ledger.append({'year': year, 'fee_bps': fee, **{k: t[k] for k in (
                'coin', 'open_date', 'close_date', 'is_short', 'stake_amount', 'leverage',
                'profit_abs', 'funding_fees', 'exit_reason')}})
    result['limitations'] = [
        'Drawdown is closed-trade balance only, not mark-to-market equity or liquidation risk.',
        'Archived isolated single-pair trades cannot reconstruct rejected signals of one-slot multi-pair native backtest.',
        'Four independent 10000 wallets are a retrospective diagnostic, not original BTC/ETH one-slot configuration.',
        'Fee stress is not a queue/spread/slippage model; no statistical or forward profitability claim.',
        'Top-3 removal is concentration sensitivity only, not a strategy variant or automatic rejection gate.',
    ]
    (out / 'A233_RESULTS.json').write_text(json.dumps(result, indent=2) + '\n')
    with (out / 'A233_TRADE_LEDGER.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(ledger[0]))
        writer.writeheader()
        writer.writerows(ledger)
    print(json.dumps(result['results'], indent=2))

if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
