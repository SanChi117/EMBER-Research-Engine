# A235 — результаты 18 исправленных нативных тестов Freqtrade

Дата: 31 октября 2026. Экономический артефакт, **НЕ решение о реальной торговле**. Первичная пререгистрация: [A235](research/a235_timeframe_parity/PREREG.md). Блокировка направления: `RESEARCH_MANDATE_LOCKED.md` (`main`).

## Причина повторного теста (подтверждено исходным кодом)

В A228/A229/A230 общий runner задавал `"timeframe":"1h"` в конфигурации и не передавал `--timeframe` отдельно. Это неверно для трёх исходников: **TrendFollowing 4h, Risk_Stair_S5 15m, NASOS 5m**. Отдельно проверены оригинальные SHA; A235 сделал source-AST assertion и передавал нужный `--timeframe`, не меняя авторские формулы. Защиты `--enable-protections` и 5m-detail там, где допустимы. 5m NASOS детализировать 5m нельзя.

В GitHub [Actions run #41241733734](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41241733734) **18/18 complete, 0 blocked**, Python 3.11, Freqtrade 2026.9. Класс исходного файла не модифицирован. 279 официальных ZIP genuine mainnet USD-M (но contract metadata от testnet из-за HTTP 451): BTC/ETH/SOL, настоящие 5m, 8h mark и funding, 2023-11..2026-05. Комиссии моделируются отдельно: base 0,05% и stress 0,11% на сторону. Это не настоящая модель orderbook/spread/slippage или liquidation.

## Доходность и просадка чистого капитала

В каждой строке отдельный год/окно с **новым счётом $1 000**, фиксированный stake $100, максимальные 3 одновременно открытые позиции, 3 пары. Значения после комиссий по моделированию Freqtrade, включая funding в пределах реализованной встроенной модели. Не складывать без моделирования последовательного портфеля.

| Оригинал | Период | BASE 0,05%/стор. | STRESS 0,11%/стор. | DD STRESS | Сделок STRESS |
|---|---|---:|---:|---:|---:|
| TrendFollowing (`4h`) | 2024 | -11.12% | **-17.57%** | −18.37% | 340 |
| TrendFollowing (`4h`) | 2025 | +7.08% | **-4.98%** | −8.63% | 436 |
| TrendFollowing (`4h`) | 2026 январь–май | -0.57% | **-3.24%** | −9.19% | 160 |
| Risk_Stair_S5 (`15m`) | 2024 | +16.95% | **+4.56%** | −10.11% | 132 |
| Risk_Stair_S5 (`15m`) | 2025 | +19.72% | **+5.48%** | −11.98% | 118 |
| Risk_Stair_S5 (`15m`) | 2026 январь–май | -1.98% | **-6.40%** | −11.88% | 52 |
| NASOSv7LongShort (`5m`) | 2024 | -0.82% | **-0.81%** | −1.52% | 5 |
| NASOSv7LongShort (`5m`) | 2025 | -0.20% | **-0.21%** | −1.47% | 8 |
| NASOSv7LongShort (`5m`) | 2026 январь–май | +0.00% | **+0.00%** | −0.00% | 0 |


## Как исправление меняет предыдущие оценки

- **TrendFollowing:** прежний A230 стресс-2025 −28,41%; теперь при нативном 4h **−4,98%** (2025 BASE +7,08%). Тест был существенно искажён; **это не верификация прибыльности**. 2024 STRESS −17,57%; январь–май 2026 −3,24%.
- **Risk_Stair_S5:** A230 стресс-2025 +12,36%; теперь на исходном 15m **+5,48%**. Отдельные 2024 и 2025 остаются положительными, но 2026 STRESS −6,40%. 5× leverage плюс исходный 15m/4h сигнал требуют проверки margin/liquidation/funding execution. Вердикт: `REVIEW_OPEN`, а не confirmed or final FAIL.
- **NASOSv7LongShort:** нативный 5m дал всего 5 сделок за 2024, 8 за 2025, 0 за Jan–May 2026; практически нет информации для статистического edge. `INSUFFICIENT`, не универсальный FAIL.

## Обнаруженная отдельная проблема паритета портфеля

Проверен ещё один оригинальный артефакт: `krantikaridev/freqtrade` commit `11d7d66c60cf49a148cb61619b8061dc40d2510c`, `config/config.dryrun.json`, blob `965193dbe93e65389c0ce8b5669229667e9fd846`. В нём стратегия TrendFollowing, TF=4h, whitelist **BTC/ETH/SOL/BNB**, 3 max trades, `stake_amount: unlimited`, wallet $1000. A235 использует **BTC/ETH/SOL, stake=$100**, поэтому даже с правильным TF это **контролируемый тест**, а не воспроизведение исходного общего счёта.

В `linhuang1212-coder/crypto-quant-trading` commit `63c012a0329a280f99fe57896456d4b9363c9c71` есть репозиторный `user_data/config_backtest.json` (blob `ee0f8c8a4c1ad827a38109c7872c1f09ac7383f3`) с BTC/ETH/SOL/**ADA**, 4 max trades, unlimited stake; соответствие **именно** Risk_Stair_S5 требует авторского подтверждения, не подменять этим конфигом оригинал автоматически. Для NASOS восстановить точный портфель и включённые/отключённые callbacks.

## Evidence

- Machine-readable [A235_NATIVE_TF_RESULTS.json](research/A235_NATIVE_TF_RESULTS.json) — все 18 результатов и метаданные CI.
- [CI log and jobs](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41241733734): source AST parity, 279 source ZIP receipts, 18 отдельных Freqtrade-complete.
- GitHub Actions artifact **ID 13057093648**, ZIP 12 308 413 байт, **SHA-256** `2d1098c7ee6676d8bdbf8bd209478ed976a98336b5a6149ad724767a539af1e2`: полные native ZIP trade journals и input-source receipts. Artifact retention 30 дней, текущие payload-данные чисел извлечены из job log, а не рекламных описаний.
- Старые A228/A229/A230 receipts не удалены. Реальные Binance ордера, автономный PAPER, Google Drive, мандат и исходники не изменены.

## Следующий экономический контроль

На основании frozen *до нового теста* author config отдельно проверить TrendFollowing на четырёх авторских парах, stake=unlimited и едином капитале; Risk S5 выяснить конкретный авторский experimental config и leverage/margin; NASOS авторский portfolio. **Double MA один общий BTC/ETH счёт остаётся отдельным R001.** Из A234+A236 в переоценке в общей сложности 76 записей/вариантов, а не 76 готовых стратегий. `VERIFIED_FUTURES_CANDIDATE = 0` — до исходного портфельного паритета и честного OOS.

