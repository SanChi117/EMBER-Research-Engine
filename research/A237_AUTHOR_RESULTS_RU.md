# A237 — независимая экономическая проверка исходного общего счёта TrendFollowing

**31 октября 2026 · завершено 6/6, блокировок 0 · Binance USDT-M Futures.**

A235 исправил таймфрейм 4h, но предыдущий контроль не воспроизводил исходный капитал и активы. A237 восстановил авторские BTC/ETH/SOL/BNB, единый $1000 wallet, `stake_amount=unlimited`, `max_open_trades=3`, `tradable_balance_ratio=0.95`, авторские защиты и исходный стоп. Код самой стратегии неизменён, Git blob `ee2293e19f3cdecb082525f6d55a166249f74eb2`, авторский config blob `965193dbe93e65389c0ce8b5669229667e9fd846`. Размер ставки учитывается внутри моделирования Freqtrade; ликвидации и orderbook не проверены независимо.

## Результаты отдельного исходного счёта, net от $1000

| Период | BASE 0.05%/side | STRESS 0.11%/side | STRESS maxDD | STRESS trades |
|---|---:|---:|---:|---:|
| 2024 | -32.40% | **-49.99%** | −51.58% | 380 |
| 2025 | -31.07% | **-43.37%** | −45.13% | 409 |
| 2026 январь–май | -4.30% | **-9.84%** | −23.39% | 156 |


**Вывод:** модельный PnL отрицателен во всех трёх периодах уже при обычной комиссии и ухудшается под стресс-издержками. В 2024 stress DD достигает 51.58%. Отмечаем `NEGATIVE_AUTHOR_ACCOUNT_3_PERIODS`; **не превращаем его в общий доказанный FAIL всех возможных авторских и будущих вариантов**. Это гораздо более строгий отрицательный контроль конкретного исходного авторского профиля, чем A230/A235. Не требует спасения подбором параметров.

## Reproduction

- [Native Freqtrade workflow completed 6/6](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41242861062), commit `d2dbf06fcbd037d44209d6041032f6793ef29465`, job `124660161408`, Python 3.11/Freqtrade 2026.9.
- `A237_AUTHOR_RESULTS.json`: machine-readable exact returns and drawdowns.
- GitHub Actions artifact `13058187639`, archive SHA256 `7954cd6ffb092bf779894e38d56f4a312935fdef49429f5929961b730a22509e`, 661184 bytes; includes source manifests and full native logs; 30d retention.
- Original Binance USD-M MAINNET official monthly 5m/mark/funding SHA-verified for 4 assets (372 market source ZIPs); contract precision via TESTNET metadata owing to HTTP451.
- BNB official funding timestamp sometimes +1ms around 8h interval, so data preflight permits ≤1 second jitter **without imputing or deleting any funding record**.
- Main known limitations: modeled OHLC fills, no genuine historical order book/queue, no independent liquidation/margin audit; non-untouched previously reviewed years. Distinguish this from verified forward PAPER. No live trades or existing PAPER job edits.

Next: Risk S5 original four-pair account independently preregistered in A238; Double MA original common BTC/ETH wallet remains R001 separate.
