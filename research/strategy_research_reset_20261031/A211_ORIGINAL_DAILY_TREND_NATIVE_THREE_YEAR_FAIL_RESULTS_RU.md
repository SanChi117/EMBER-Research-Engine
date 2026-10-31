# A211 — завершённый экономический отчёт: ORIGINAL дневной TrendFutures НЕ устойчив

Дата 2026-10-31. Подтверждён GitHub Actions [run 41205821202](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41205821202): SUCCESS 24 подлинных Freqtrade ZIP; `A211_24_NATIVE_REAL_BINANCE_RESULTS_VERIFIED.json` автокоммитирован самим CI после перепроверки каждого trade log, 1× leverage и контроля истории/сумм.

## Реальный исходник и нетронутые параметры

`Kureshi25/cryptobot@c8ffbaabee9f63630e179c698c53df4916b93f8e:user_data/strategies/TrendFutures.py` Git blob `2e6b83ba128373655090ca4827d8c7954ffaedfd`, 1d, `can_short`, Donchian20/10, ATR mult3.0, 1×. **Важная оговорка:** в авторском репозитории найден отдельный подогнанный JSON `TrendFutures.json` 18/16/9.5. Мы его НЕ загружали, поскольку prereg до PnL фиксировал класс Python с исходными defaults 20/10/3.0. Путь изолирован, байты .py совпадают; авторский репозиторий не изменён. Предварительный отказ CI и исправление задокументированы в `A211_AUTHOR_OPTIMIZED_JSON_PARAM_ISOLATION_PREFLIGHT_RU.md`.

**Реальные источники:** 540 месячных Binance Vision ZIP `2023-01-01–2026-10-01`, authentic 1d USD-M klines, 1h genuine mark price, real 1h settled funding; все SHA в оригинальном machine receipt, missing monthly mark repairs only via genuine daily SHA. 2023 = warmup for EMA200/startup220. Three disjoint evaluation windows: 2024,2025,2026 Jan-Sep; 4 pairs BTC/ETH/SOL/LINK; 2 fees (0.0005,0.00125) per side, stake100 USDT, wallet1000 USDT on 4 strictly separate partitions, one 1× isolated position per pair. **No extra slippage**, so real market orders can be worse. Freqtrade engine 2026.4.

## Результат per 4000 USDT on 4 independent model wallets

| Period | BASE N | BASE wallet return | BASE PF across 4 ledgers | STRESS wallet return | matched $100/coin price-only hold |
|---|---:|---:|---:|---:|---:|
| 2024 | 48 | **−1.920621%** | 0.710886 | **−2.082894%** | +7.158605% |
| 2025 | 40 | **−2.523581%** | 0.604854 | **−2.673160%** | −2.270796% |
| 2026 Jan–Sep | 27 | **+1.043687%** | 1.536729 | **+0.950860%** | −0.054354% |

Контрольный buy&hold: purchase $100 worth of each symbol with $900 cash per segregated wallet, close at end, roundtrip fee 0.05%/0.125% on two executions. **Only futures PRICE hold proxy**: no spot premium, funding or gap/slippage; not genuine executable funded spot benchmark. Поэтому сравнение ориентировочное.

Total BASE per-year USDT: 2024 −$76.824852, 2025 −$100.943228, 2026 +$41.747478. **Sum three independent yearly resets = −$136.020602**, *not* actual compounded single-account backtest across 3y. STRESS −$152.207762 across three yearly reset experiments.

ETH 2026 +4.105045% / PF11.95 with **only 5 trades**; это недостаточная статистика, нельзя объявить отдельную доходную ETH-стратегию. 2024 ETH +0.3919%/PF1.085, 2025 ETH +0.4161%/PF1.065 — PF<1.2. 2024 and 2025 worst LINK account -4.57%/-6.83%, 2025 maximum **reported realized** account DD9.84%, но настоящий portfolio marked-to-market DD не вычислен: не подменять один другим.

## Вывод / запреты
**Research economic gate FAIL, no forward approval.** 2026 положителен в одном режиме, 2024/2025 отрицательны. Даже до extra live spread/slippage нет устойчивого положительного преимущества. Не оптимизировать 20/10/3→18/16/9.5 задним числом на тех же окнах и не рекламировать «1d лучше, потому что редкие сделки».

Весь код для получения источников (`a211_prepare_true_daily_futures.py`), нативного исполнения (`a199_native_original_futures_offline.py`), 24-архивной проверки с бенчмарками (`a211_verify_24_native_daily_trade_zips.py`) и сами отчёты сохранены. История 2024–26 уже просмотрена в EMBER — это не pristine external OOS. Даже при положительном тесте допуск к торговле потребовал бы отдельный forward PAPER.

Следующий независимый кандидат (не новый набор параметров trend-following) — **A212 реальный двухногий cash-and-carry**, prereg в отдельной ветке до PnL. Existing SMOKE/PAPER schedulers и реальные позиции не менялись.
