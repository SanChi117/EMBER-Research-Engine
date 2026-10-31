> **⚠️ АРХИВНОЕ СВИДЕТЕЛЬСТВО, НЕ ТЕКУЩИЙ СТАТУС.** AUTHOR_ACCOUNT_BACKTEST_UNVERIFIED_EXECUTION — стресс 2024/2025 положителен, Jan–May2026 отрицателен. При исходном 5× liquidation/mark/order-fill не подтверждены. Не допускать к PAPER без нового протокола. [Текущая единая сводка](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/RESEARCH_STATUS_CANONICAL.md). Ни одна стратегия не `VERIFIED_FUTURES_CANDIDATE`.

---

# A238 — Risk_Stair_S5 с исходным общим счётом, нативный Binance USDT-M

**31.10.2026. Шесть из шести Freqtrade native тестов завершились; все трейдовые архивы доступны. Не доказанный производственный trading edge.**

## Протокол и паритет

- Strategy оригинал `linhuang1212-coder/crypto-quant-trading` commit `63c012a0329a280f99fe57896456d4b9363c9c71`, Git blob `9b6ba1f5466727da1e9446f4e283b1c555fca59b`. Timeframe `15m`, 4h informative, 5x leverage, stoploss_on_exchange=True, trailing and stage exits retained. 
- Experiment manifest blob `b07d45fe9485a0e71af6ff26f8cfd66af793f587` names Risk_Stair_S5 with stage `20b/-0.06,40b/-0.04,lev=5.0`; experiment runner blob `6e35055ecf8aa7e7ee247ddf5ac5f9b9a0d10c93` references `user_data/config_backtest.json` blob `ee0f8c8a4c1ad827a38109c7872c1f09ac7383f3`. All three author source SHA re-verified during CI.
- Exact controlled model account from author config: **BTC/ETH/SOL/ADA, wallet $1000, stake=unlimited, max_open_trades=4, ratio=0.40**. Distinct from A235's artificial 3 pairs and fixed $100 stake. 5m detail on 15m and official candles; Freqtrade `2026.9`, strategy protections enabled.
- Binance MAINNET genuine USDT-M official monthly 5m klines, 8h mark and actual funding, 4 assets, 2023-11...2026-05; 372 archived price/mark/funding sources with SHA. Because Binance mainnet REST HTTP451, precision/contract metadata sourced from Binance Futures TESTNET, not execution parity. No spot fallback.
- 2024, 2025 and Jan-May 2026 tested independently, reset wallet in each year/window. Fees standard 0.05% each side / stressed 0.11% each side. Fee stress ≠ real orderbook/spread/slippage and overnight gaps. No parameter hyperopt or selecting pairs after results.

## Результаты одного авторского портфеля, net PnL от $1000

| Период | BASE 0.05% | STRESS 0.11% | Max DD stress | STRESS сделок |
|---|---:|---:|---:|---:|
| 2024 | +39.96% | **+22.29%** | −10.19% | 167 |
| 2025 | +27.72% | **+11.80%** | −16.53% | 150 |
| 2026 январь–май | +0.52% | **-2.74%** | −9.88% | 61 |


**Вывод:** восстановление авторской геометрии капитала и набора монет действительно меняет предыдущий вывод. A235 Risk S5 на 3 парах фиксированных $100 давал stress +4.56% / +5.48% / −6.40%; A238 даёт **+22.29% / +11.80% / −2.74%**. Кандидат достоин дальнейшей верификации, не признания VERIFIED. Из трех окон одно остается отрицательным после повышенных расходов. 5× плечо может создать ликвидационный риск выше оценённого OHLC drawdown.

## Важные незакрытые риски

1. Исходный скрипт экспериментов `run_risk_experiments.ps1` ожидает стратегию в `user_data/strategies/experiments`, сохранённый pinned класс расположен в `risk_exp`. Мы проверили класс и параметры, но **не доказали тождество исходного исторического runtime-деплоя**.
2. 5× isolated margin maintenance tiers, liquidation events, funding debit timing and stop gaps не проверены независимо. Nativе Freqtrade OHLC не равен биржевому execution replay.
3. Нет нетронутого OOS/forward PAPER: 2024/2025/первые пять месяцев 2026 уже многократно просматривались. Нельзя выбирать лучший вариант на известных данных и выдавать за prospective edge.

## Цифровые доказательства

- [Пререгистрация A238](a238_author_risk/PREREG.md).
- [GitHub Actions run #41243084798](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41243084798) — all 6 complete, zero blocked, pinned source SHA + 4 pair genuine market sources.
- [A238_RISK_AUTHOR_RESULTS.json](A238_RISK_AUTHOR_RESULTS.json) — machine-readable six PnL, DD, trade counts.
- GitHub Actions artifact ID **13057784292**, ZIP digest SHA256 `239d0c11a107bbd415082699b759820c4968575c0565b9de2757fcf7dcff6102` (3,477,039 bytes), full native trade ZIP and price receipts; 30 day artifact retention. Workflow commit `d099ccbc2ca9ba80e0ca61a94e85f4725f99c0bb`.
- `A235` old run logs preserved. No live trades, no existing PAPER planner modifications, original class untouched.

## Статус

`PROMISING_BUT_UNVERIFIED`. Следующий gate — causal timeline, actual futures maintenance margin/liquidations, fee+slippage independent stress with mark-price and genuine orderbook if accessible, plus prospective frozen out-of-sample window and PAPER. Остальные 76 кандидатных записей A234+A236 **не считать завершёнными**.
