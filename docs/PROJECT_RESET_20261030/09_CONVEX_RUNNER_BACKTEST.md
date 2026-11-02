# RESET-07 — CONVEX_RUNNER 2024–2026 / first frozen run

**Evidence status:** `MODEL_COMPLETED / FIDELITY_CAVEATS / OWNER_REVIEW_REQUIRED`.
**Internal rules verdict:** `LOTTERY` (LOTTERY). This is **NOT** independently validated alpha, and **NOT** authorization to trade.

## Fixed input and isolation

Owner RESET-07 dated 2026-11-02. Rules preregistered before any historical pull at commit `d4734aa5ef8d76a8a0ca103b88d89b18a40a80a6`. Twenty 4h+1d Binance USDT-M API kline arrays for all 10 named coins saved at `3b55a8a8a036aa9a24dd265c3f3e2558c0557f7e`. SHA256 independently logged by CI Python 3.10/3.11/3.12 and pinned in `research/convex_runner/raw_sha256_manifest.json` commit `483dcb4d85aa426eebd12635661b878ff894218e`; zero internal gaps identified. Warmup 2023 is not a trading period; ARB, SUI, TIA launched later, and no artificial candles were added.

One tested period: **2024-01-01 00:00 UTC through 2026-10-31 23:59 UTC**. Four scenarios: LONG 1%, LONG 2%, SHORT 1%, SHORT 2%; separate 10-symbol portfolios starting at simulated $920 each. Long uses breakout of previous 120 closed 4h highs, short mirrored lows; 2/2 confirmed pivots, Wilder ATR14, 1.75 ATR buffer, full 365-day trailing percentile and 30-day range CHOP, stop-first, next-4h-open fill, 4bps fee +2bps adverse slip on each side. No funding, no optimization after result.

## Numerical results (from full Binance source data, not synthetic fixtures)

| Side | Risk | Tickets | PF | WR | Avg R | Max losses in row | Max DD | Kill $736 touched | Final equity | Top5 / gross profit |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| LONG | 1% | 156 | 1.037 | 48.1% | 0.037 | 12 | 21.0% | no | 946.97 | 24.6% |
| LONG | 2% | 151 | 0.971 | 47.7% | 0.031 | 12 | 35.4% | YES | 882.97 | 26.7% |
| SHORT | 1% | 139 | 0.954 | 50.4% | -0.002 | 12 | 20.4% | no | 893.03 | 18.8% |
| SHORT | 2% | 134 | 0.915 | 49.3% | -0.025 | 10 | 33.2% | YES | 834.08 | 21.1% |

Yearly portfolio returns by *realized-equity accounting* (not independently audited mark-to-market yearly closing balances):

| Variant | 2024 | 2025 | 2026 to Oct 31 |
|---|---:|---:|---:|
| LONG 1% | 5.85% | -0.67% | -2.10% |
| LONG 2% | 7.98% | -7.52% | -3.89% |
| SHORT 1% | -12.48% | 8.66% | 2.07% |
| SHORT 2% | -18.63% | 12.82% | -1.25% |

Buy-and-hold SOL benchmark for same window (Binance perpetual 1d open vs last close, no funding/fees): **-6.225%**. This is a single-asset benchmark and does not prove alpha or comparable drawdown.

### Largest five net-winning trades in each variant

| Scenario | Rank | Symbol | Net PnL USDT | Net R | Exit mode |
|---|---:|---|---:|---:|---|
| LONG 1% | 1 | DOGEUSDT | 45.183 | 4.873 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 2 | ARBUSDT | 38.366 | 4.316 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 3 | NEARUSDT | 37.381 | 4.213 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 4 | SUIUSDT | 34.057 | 3.989 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 5 | LINKUSDT | 32.727 | 3.681 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 1 | DOGEUSDT | 91.066 | 4.873 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 2 | ARBUSDT | 67.422 | 4.316 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 3 | SUIUSDT | 67.020 | 3.989 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 4 | LINKUSDT | 57.512 | 3.681 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 5 | NEARUSDT | 51.645 | 4.213 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 1 | APTUSDT | 23.821 | 2.850 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 2 | ARBUSDT | 22.948 | 2.745 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 3 | SOLUSDT | 21.782 | 2.540 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 4 | ARBUSDT | 19.947 | 2.347 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 5 | ARBUSDT | 17.232 | 1.991 | TP_2R_BEFORE_RUNNER |
| SHORT 2% | 1 | APTUSDT | 42.954 | 2.850 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 2 | ARBUSDT | 41.379 | 2.745 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 3 | SOLUSDT | 41.242 | 2.540 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 4 | ARBUSDT | 38.601 | 2.347 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 5 | ARBUSDT | 32.352 | 1.991 | TP_2R_BEFORE_RUNNER |

Top-5 contributions appear in the summary table. Full raw per-trade JSON, skipped events, original SHA256 file hashes, and second exact rerun evidence are in CI artifacts:
- [Python 3.11 full verified JSON](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41361579425/artifacts/13105801857)
- [Python 3.12 full verified JSON](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41361579425/artifacts/13105771868)
- [Python 3.10 full verified JSON](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41361579425/artifacts/13105406672)

All Python 3.10/3.11/3.12 special CI jobs SUCCESS; two executions on Python 3.11 produced identical full JSON via `cmp`. Test fixture output must never be confused with this provider-sourced run.

## Frozen criterion verdict

Owner threshold REPEATABLE: PF >1.3 on 1% and 2%, >=60 tickets, DD <=30%, top-5 <60% gross profit, both 2024 and 2025–2026 positive. That threshold **was not met**. The preregistered LOTTERY criteria apply to three of the four variants with PF <=1; both 2% variants touch modeled kill. `RESET07_FINAL_VERDICT=LOTTERY` is the correct verdict **for this frozen executable implementation**.

## Fidelity limitations / no second optimized run

1. **1R vs TP**: under 4h OHLC ambiguity the preregistration arms the runner only after the completed candle and allows a 2R TP fill earlier on that candle. In continuous favorable price motion the 1R level is necessarily touched before the 2R level; this convention can overcount initial TP fills compared with immediate intrabar cancellation in the owner's literal TЗ. **Therefore this is not a perfect realization of the TP-removal clause.**
2. **Kill handling**: simulations record mark-equity <=736 as a kill-touch for the explicit lottery gate but keep running afterward. Final-equity figures for 2% are hypothetical continuation, **NOT an executable account path honoring the kill halt**.
3. **Swing trailing**: trail pivots are tracked during open positions, not initialized with full earlier confirmed swing history; some early exits may differ. Causal confirmation prevents future leakage but does not prove parity with owner's structure.
4. **Source provenance**: SHA256 pins the verbatim JSON arrays returned from Binance connected public USDT-M API, **not Binance Vision original ZIP checksum files**; 4h and 1d were checked independently for internal UTC continuity, but original exchange archives not independently reconciled.
5. **No funding, exchange lot-step, spread, margin liquidation, or event-time tick sequence**. OHLC priority is a model, not a market execution guarantee. Top entries +3127 PUMP and +670 FIL mentioned in owner spec cannot be compared as PUMP and FIL are excluded from the 10-symbol universe, and the user real-account risk sizes cannot be normalized.
6. **Research architecture**: this test examines *position management after a breakout alarm*; it does not validate a profitable entry formation. CONVEX_RUNNER_001 remains `BLOCKED_UNTIL_BACKTEST` and `live_allowed=false`.

**Owner safety instruction followed:** no post-result parameter tuning and no second experimental rule-set. Correcting the fidelity issues requires separate explicitly reviewed, preregistered TЗ/branch; do not silently reinterpret these numbers as definitive falsification of every convex runner model.

## Reproduction

```bash
python -m research.convex_runner.data_contract --manifest research/convex_runner/raw_sha256_manifest.json
python -m pytest tests/test_reset07.py -q
python -m research.convex_runner.backtest --sha-manifest research/convex_runner/raw_sha256_manifest.json --stdout
```

GitHub Actions run: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41361579425 .

---

# RESET-07 §5.1 — отдельный замороженный тест LIMIT-TOUCH / 7-DAY TTL

**Владелец указал использовать ту же ветку** `research/reset07-convex-runner-backtest-20261102`. Исходные результаты RESET-07 выше **не изменены**. Этот раздел — вторая версия, новые допущения, оригинальное исследование остаётся воспроизводимым.

**Вердикт первой реализации дополнения:** `LOTTERY` (**ЛОТЕРЕЯ**, при соблюдении замороженных правил указанной модели), без разрешения PAPER/LIVE. Зафиксировано в `research/convex_runner/limit_v2_preregistration.json` коммитом `54b4894db160edae3b1f047f1080c6dfc0e53b67` до нового экономического прогона. Старые данные не заменялись, исходный SHA256-манифест совпадает: `386bfb2ddc6e22f9d71995e1db14a74cb3b24329b2cbc5990bc8bd0f73643dd8`.

## Изменение модели входа, НО НЕ параметров управления

- Ограничение владельца: **7 календарных суток** (42 последовательные 4h-свечи); после истечения — `EXPIRED_UNFILLED`, не сделка.
- **Исполнительское допущение**, не прямо установленное ТЗ: лимит на прежнем 20-дневном максимуме (лонг) / минимуме (шорт), то есть повторное касание уровня пробоя. Установлен в следующий 4h-бар ПОСЛЕ закрытия сигнального.
- Запись `LIMIT_PLACED` → `LIMIT_FILLED_TOUCH_ASSUMED` только при последующем касании 4h high/low до expiry; отдельно `TOUCH_BUT_SKIPPED_BUDGET` и `EXPIRED_UNFILLED`.
- Условный fill **не подтверждает очередь заявок/биржевое исполнение**. При касании и стопе в той же свече выставляется `same_bar_stop_ordering_undetermined=true` и консервативный стоп, а не приписанная прибыль.
- Сохранены 1%/2%, 15x, 6 одновременных, 10% риск серии, CHOP 365d + 30d, ATR 1.75, 4bps комиссия + 2bps проскальзывание на каждую сторону, первоначальный способ сопровождения раннера и учёта kill-touch (см. замечания далее).

## Четыре запуска — исходные данные Binance USDT-M, 2024–2026

| Сценарий | Лимитов | Условно заполнено | Fill-rate модели | EXPIRED 7d | Бюджет-отклонения | Закрыто | PF | DD | Kill-touch | Equity $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| LONG 1% | 233 | 162 | 69.5% | 25 | 46 | 162 | 0.984 | 18.8% | нет | 908.15 |
| LONG 2% | 241 | 160 | 66.4% | 25 | 56 | 160 | 0.970 | 33.7% | ДА | 881.80 |
| SHORT 1% | 264 | 147 | 55.7% | 30 | 87 | 147 | 1.148 | 18.1% | нет | 1012.50 |
| SHORT 2% | 273 | 145 | 53.1% | 31 | 97 | 145 | 1.032 | 32.7% | ДА | 953.57 |

**Число заявок = число фактически зарегистрированных модельных лимиток**. Контроль: заполнено + истекло + отказ бюджета + незавершённые у конца периода = размещено. Пропущенные ещё до регистрации сигналы в знаменатель не включены. `signals_right_censored_end=0` в четырёх полных прогонах.

Дополнительные метрики:

| Сценарий | WR | Средний R | Серия убытков | Top-5 / gross wins | 2024 | 2025 | 2026 до 31.10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| LONG 1% | 50.0% | 0.0075 | 9 | 19.4% | -0.02% | 4.42% | -5.45% |
| LONG 2% | 50.6% | 0.0193 | 9 | 20.9% | -3.66% | 4.39% | -4.70% |
| SHORT 1% | 51.7% | 0.0895 | 12 | 16.8% | -6.96% | 8.53% | 8.99% |
| SHORT 2% | 50.3% | 0.0683 | 12 | 19.0% | -13.22% | 1.67% | 17.47% |

## Топ-5 выигрышных сделок по каждому сценарию

| Сценарий | № | Пара | Net PnL USDT | Net R | Выход |
|---|---:|---|---:|---:|---|
| LONG 1% | 1 | SUIUSDT | 34.61 | 4.232 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 2 | NEARUSDT | 33.56 | 3.749 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 3 | SOLUSDT | 29.90 | 3.284 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 4 | ARBUSDT | 21.35 | 2.442 | RUNNER_4H_SWING_CLOSE |
| LONG 1% | 5 | APTUSDT | 18.48 | 1.992 | TP_2R_BEFORE_RUNNER |
| LONG 2% | 1 | NEARUSDT | 63.34 | 3.749 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 2 | SUIUSDT | 61.31 | 4.232 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 3 | SOLUSDT | 57.35 | 3.284 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 4 | ARBUSDT | 39.05 | 2.442 | RUNNER_4H_SWING_CLOSE |
| LONG 2% | 5 | APTUSDT | 37.29 | 1.992 | TP_2R_BEFORE_RUNNER |
| SHORT 1% | 1 | ARBUSDT | 26.18 | 2.876 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 2 | APTUSDT | 26.05 | 2.863 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 3 | ARBUSDT | 25.29 | 2.780 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 4 | ARBUSDT | 22.03 | 2.512 | RUNNER_4H_SWING_CLOSE |
| SHORT 1% | 5 | LINKUSDT | 21.00 | 2.408 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 1 | ARBUSDT | 44.83 | 2.876 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 2 | APTUSDT | 43.99 | 2.863 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 3 | ARBUSDT | 42.71 | 2.780 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 4 | ARBUSDT | 41.29 | 2.512 | RUNNER_4H_SWING_CLOSE |
| SHORT 2% | 5 | AVAXUSDT | 35.34 | 2.300 | RUNNER_4H_SWING_CLOSE |

## Сравнение и интерпретация

Buy-and-hold SOL за тот же период (одна монета, без funding и комиссий): **-6.225%**. Прямое сравнение с портфелем из 10 фьючерсных пар ограничено.

**Почему у LONG fill-rate выше 60%**: возврат к предыдущему 20-дневному уровню пробоя часто удовлетворяет тесту касания экстремумом свечи. Поскольку 4h OHLC не содержит фактическую последовательность сделок, книгу очередей и объём ликвидности на уровне, такой fill-rate **потенциально завышает истинный**. Число ~36% из Trading Monitor не является статистически подтверждённым реальным fill-rate: 30/83 — закрытые записи с исходом, а 47/83 — разные причины отмены и отсутствия исполнения; эти категории нельзя смешивать.

**Уязвимости прежнего бэктеста сохранены и явно раскрыты**: перевод +1R в раннер лишь на закрытии 4h и возможный +2R TP на этой же свече; kill-touch учитывается, но продолжение после kill не останавливается; свечные касания не подтверждают реальный порядок fill/stop; внутрисвечная маржа и ликвидации не проверены; funding не учтён. Это исследовательский расчёт, а не полноценный механизм исполнения в торговом терминале.

Сделки владельца PUMP (+3127) и FIL (+670) по условиям вообще **вне юниверса**, поэтому сравнение с их распределением внутри модели не допускается.

## Проверка воспроизводимости

- 10 монет, 20 исходных файлов 4h/1d, сохранённые Binance raw JSON; целостность сверена SHA256, внутренние GAP не обнаружены.
- CI `https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41366675994`, Python 3.10/3.11/3.12: **15/15 тестов на каждой версии**, все три jobs SUCCESS, Python 3.11 повторный JSON побайтно идентичен.
- Полные записи `LIMIT_PLACED`, `LIMIT_FILLED_TOUCH_ASSUMED`, `EXPIRED_UNFILLED`, `SKIPPED_BUDGET` и закрытых сделок — артефакты CI того же запуска. Отдельный машиночитаемый summary: `docs/PROJECT_RESET_20261030/09_CONVEX_RUNNER_LIMIT_V2.json`.

`CONVEX_RUNNER_001` остаётся **BLOCKED_UNTIL_BACKTEST**, `live_allowed=false`. PR не объединять без проверки владельца.
