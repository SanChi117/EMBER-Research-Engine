# A202 — VERIFIED оригинальный dip_catcher (REAL Binance Futures 5m native Freqtrade): ECONOMIC PASS, SPEED FAIL, RISK FAIL

Дата 31.10.2026. **Не является сигналом сделки, автоматически исполнимой системой или доказанным OOS edge.** PAPER RESEARCH ONLY.

## Reproducible genuine-source receipts

- Original `viktors1982/trading` pinned commit `e572140b1b8cb550cb244c67d363087b81bd4ab8`, original `freqtrade/strategies/dip_catcher.py` git blob `76ab2b3f91dc7beaa0be8021a245caa2b3f4186f`. No changes to source entries, stoploss, ROI or params.
- GitHub Actions [41156913032](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41156913032) SUCCESS: exactly eight native Freqtrade `2026.4` trade ZIPs, 4 symbols BTC ETH SOL LINK × 2 fee tiers. Genuine audited continuous Binance Vision USD-M 5m trade-price and 1h mark/funding [2026-05-13,2026-10-01) UTC. Each isolated, **1× leverage**, independent wallet1000 USDT, fixed proposed stake100 USDT, max one open trade per symbol.
- Artifact GitHub ID **13025456717**, outer SHA256 `fd57dc5685bab819e768ed6a3c1134bb421421f485751d43d94d4a03d1b86df6` — independently downloaded and hash-matched exactly to GitHub digest; eight inner original ZIPs independently reopened, per-trade `profit_abs` sums, per-archive SHA, direction, 1× and number of trades independently verified.
- BASE fee0.0005 each execution, STRESS fee0.00125 each execution, **no additional slippage/bid-ask spread or limit queue fill rejection**. Positivity may degrade live. Funding as Binance original settled source.
- Independently compared to pre-registered A202 rules BEFORE results: at least 2 of 4 pairs simultaneously both tiers N≥35, net>0, PF≥1.2, wallet DD<15%, top3 win<60%, total >=141 trades /141d each tier.

## Экономика, 4 отдельно моделируемых кошелька (НЕ общий портфель)

| Pair | N base / stress | net wallet BASE | PF BASE | maxDD BASE | net wallet STRESS | PF STRESS | maxDD STRESS | QUALIFIES ECON? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BTC | 67 / 60 | +2.107758% | 1.80383 | 1.24595% | +0.816678% | 1.25239 | 1.30927% | YES |
| ETH | 96 / 88 | +6.431572% | 2.45011 | 1.28831% | +4.979745% | 2.10329 | 1.35375% | YES |
| SOL | 146 / 130 | +3.863385% | 1.32786 | 3.14504% | +1.357194% | 1.11294 | 3.55188% | **NO**, stress PF<1.20 |
| LINK | 161 / 144 | +5.760211% | 1.50546 | 1.90921% | +4.775757% | 1.44092 | 1.97344% | YES |

**ECONOMIC RESEARCH GATE: PASS 3/4 (BTC, ETH, LINK).** 470 BASE, 422 STRESS completed trades /141 days across **4 independent, max one position-per-coin** series, arithmetic 3.33 and 2.99 trades/day respectively; NOT proven capacity for single shared margin account or actual order flow. Success does not imply profitability after real slippage.

Original source LONG+SHORT active, independently cross-checked per BASE:
- BTC LONG30 SHORT37, ROI exits62, STOP4, 1 other end-of-series; win92.54%.
- ETH LONG51 SHORT45, ROI90, STOP5; win93.75%.
- SOL LONG87 SHORT59, ROI131, STOP14; win89.73%.
- LINK LONG91 SHORT70, ROI146, STOP14; win90.68%.
- No DCA, no trailing activated, no leverage override by original class.

## Абсолютное время удержания — стоп по скорости

| Pair BASE | median HOLD | p90 HOLD | max HOLD |
|---|---:|---:|---:|
| BTC | 7.83 часов | 130.77 ч | 697.5 ч (29 дней) |
| ETH | 5.17 часов | 107.83 ч | 567.92 ч (23.7 дня) |
| SOL | 4.75 часов | 77.29 ч | 251.92 ч (10.5 дня) |
| LINK | 5.67 часов | 55.83 ч | 235.42 ч (9.8 дня) |

В оригинале `stoploss=-0.08` (8% **цены**, даже при 1×), time-based exit отсутствует, ROI динамически снижается до 1% после 60m. При предлагаемом пользователем плече 20–30× ликвидация почти наверняка будет раньше 8% стопа в зависимости от margin tier и комиссий. **SPEED / EXECUTION RISK GATES: FAIL 0/4**, поскольку для всех символов p90>24 часа и стоп неприемлемо широк. Это препятствует подключению к торговому PAPER или реальному исполнению, несмотря на economics.

## Эталон Freqle — не тот же experiment
[Freqle league dip_catcher](https://freqle.org/strategy/72c23c05faa67eaa): 33 инструмента, **10 общих слотов**, период 2022–2024, 21,150 trades, net+747.5%, PF1.37, DD6.71, 1×, stake100, wallet1000, avg HOLD12h26m, max HOLD669h25m, no fresh walk-forward. **Не равняется** нашему 4-карманному Binance May–Sep2026. В Freqle отсутствует `--timeframe-detail 1m`; 5m intra-bar stop/ROI order may bias.

## Дополнительная независимая проверка чувствительности к исполнению (по сырым STRESS trades)

Статические Binance market metadata Freqtrade включают quantization: **BTC фактический stake в исходных STRESS сделках ~58–87 USDT, средний ~70.67**, а не всегда proposed $100 (шаг количества 0.001 BTC). Для ETH/SOL/LINK средние stake 99.0/99.6/99.5. Поэтому пользовательскому депозиту нельзя обещать «100 USD на каждую BTC сделку» без проверки лотов.

Зная реальные суммы `stake_amount` и `net_USDT`, вычислена **описательная**, пост-хок «подушка дополнительного совокупного roundtrip расхода» при неизменных сделках и размерах: `net_USDT/sum(stake_amount)×10000 bps`:
- BTC **19.3 bps**, ETH **57.1 bps**, SOL **10.5 bps**, LINK **33.3 bps** сверх уже смоделированных 12.5bps за каждое исполнение.
- Это **не** калибровка ожидаемого slippage, не точный threshold биржевого исполнения и не тест с полной переигровкой очереди заявок: дополнительный спред меняет частоту и набор сделок, путь исполнений. Но показывает слабый запас BTC и SOL; ETH/LINK статистически интереснее, хотя исходный SL8% остаётся стоп-фактором.
- Применять эти подушки как новые параметры отбора на той же истории ЗАПРЕЩЕНО (пост-хок).

## Решение

- **A202 = ECONOMIC PASS 3/4, SPEED FAIL 0/4, RISK FAIL, EXECUTION APPROVAL FALSE.**
- Сохранить исходный код и 8 истинных native trades ZIP для научного воспроизведения. **Не «оптимизировать» оригинал после уже видимых результатов** на May–Sep 2026.
- Next: frozen identical source+execution on **genuinely unseen later period** (October 2026 daily real Binance data, with explicit source hashes, fee tiers, zero extra slippage caveat); collect longitudinal trades, funding, symbol composition and p90 duration.
- If Oct confirms economic signal, possible **separate** adaptation experiment with upfront short SL/time cap, fresh subsequent market data for final OOS. Never claim adapted risk model has original positive PnL, never enable 20–30× before fully new validation.
- User's live positions, existing PAPER schedules and SMOKE untouched.

Proof: [A202 GitHub Actions 41156913032](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41156913032), artifact 13025456717, ZIP digest given above.
