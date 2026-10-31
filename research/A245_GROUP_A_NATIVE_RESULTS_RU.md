> **⚠️ АРХИВНЫЙ ОТЧЁТ ТОЛЬКО ГРУППЫ A.** Упоминание ниже «group B ещё выполняется» устарело. [Текущий исправленный статус](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/RESEARCH_STATUS_CANONICAL.md): A245 = **30 завершённых расчетов, 6 BLOCKED**, несмотря на 2/2 CI SUCCESS. Ни одна стратегия не VERIFIED.

---

# A245 group A — 18 завершённых нативных проверок трёх ДРУГИХ оригиналов

Дата 31 октября 2026. [GitHub Actions run 41245981488](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41245981488), job 124669395539 SUCCESS, **18 из 18 complete, blocked 0**. Настоящие Binance mainnet USD-M 5m и настоящие mark/funding из архива, SHA-квитанции, оригинальные стратегии Git SHA, Freqtrade 2026.9. Одновременно **контрольный общий** BTC/ETH/SOL кошелёк $1000, ставка $100, max3, а не author config. 2024/2025/январь-май2026. Каждый год — отдельный reset. Стресс-комиссия 0,11% на сторону, базовая 0,05% на сторону.

| Стратегия | 2024 BASE / STRESS | 2025 BASE / STRESS | Jan-May2026 BASE / STRESS |
|---|---|---|---|
| R027 MTF_Hybrid | -13.79% / **-34.47%** (1736/1653 trades) | +2.17% / **-10.63%** (1625/1536) | -5.75% / **-10.10%** (636/599) |
| R029 FailureToReturnStrategy | +0.55% / **+0.39%** (23/24) | +0.50% / **+0.41%** (12/12) | +0.46% / **+0.41%** (6/6) |
| R028 FVGChannel | -13.88% / **-23.70%** (993/984) | -8.49% / **-19.43%** (897/890) | -12.67% / **-18.24%** (367/359) |

**Вывод:** MTF_Hybrid и FVGChannel отрицательны по обеим комиссиям почти во все окна и при stress 3/3. Это НЕ universal original author account FAIL. FailureToReturn слегка положительна все три окна, но **6-24 сделки/окно** и +0.39—0.41% STRESS прибыли малозначимы. Предыдущий "нулевой результат ETH" не был основанием автоматического отказа. Её статус: **POSITIVE_CONTROLLED_SCREEN / NO_STATISTICAL_POWER / CONFIG_PARITY_PENDING**, не VERIFIED.

Source caveats: FVGChannel исторический long-only исходник не доказан как author futures-native (здесь controlled USD-M transfer); FTR сохранён original can_short=False, session filter and daily guard; MTF EMA19200 / startup500 neutral fallback не менялся; исторические периоды уже просмотрены, не untouched OOS; Freqtrade OHLC limits/SL не доказывают orderbook fill, slippage или корректность official maintenance margin/liquidation.

Архив **artifact 13058698873**, SHA256 **7c6717d0207085083f89af0104674eb602e9dcab6c4aceafe6a3c9cea0b32eae**, size 6,850,575 bytes. Все 18 stdout metrics сохранены в [машинном JSON](a245_other_originals/A245_GROUP_A_VERIFIED_NATIVE_METRICS.json). [Пререгистрация](a245_other_originals/PREREG_RU.md). Group B ещё не завершён на момент выпуска этого промежуточного отчёта.

Без реальной торговли и изменения PAPER.
