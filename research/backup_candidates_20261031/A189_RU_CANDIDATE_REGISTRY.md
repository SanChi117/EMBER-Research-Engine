# A189 — резерв кандидатов для EMBER, поиск 31.10.2026

**Режим:** внешняя разведка и статический отсев без подбора параметров / без реальных ордеров. Это НЕ новый подтверждённо прибыльный портфель. Все опубликованные авторские результаты отдельно обозначены; собственное воспроизведение ограничено сверкой опубликованных trade receipts `fortunato/pymarket-structure` арифметически.

## Требования
Ищем альтернативу текущей Double MA: принципиально отличающиеся механики, открытый исходный код, доступ к исходным правилам и истории сделок, честные затраты, статистика по независимому периоду, возможность запуска Freqtrade native / другого проверяемого engine и PAPER. Приоритет SHORT+LONG 5m–4h на BTC/ETH/SOL/LINK/SUI; допустимы spot-only отдельные модули, но их нельзя выдавать за готовую futures long/short.

## Сводная таблица
| Класс | Имя | Механика, рынок | Имеющиеся подтверждения | Ограничение | Решение |
|---|---|---|---|---|---|
| A | MsSupportResistanceV1 | S/R зоны, подтверждение стороны волны, 4h BTC/ETH/SOL/XRP/LTC long/short | Публичные **404** trades и OHLCV; автор +70.32% PF1.38 DD18.10%; по 15 JSON собственный независимый арифметический счёт 404, sum PnL +703.15 USDT, PF1.376, win172, loss232 | **Не найден полный Freqtrade исходник класса стратегии** в дереве `fortunato/pymarket-structure`. Есть рабочая библиотека `attach_market_structure`; результаты исторические, предположительно in-sample curve-fit; fills/lookahead/fees недостаточно проверены | **PRIORITY_1 / RECONSTRUCTION_BLOCKED** |
| B | SingleB_FixedRR | MOM(14), 5m long/short OKX perpetual, SL−1.5%, TP+1.5% | Открытый исходник `strategy/SingleB_FixedRR.py`, автор заявляет 14 008 trades, 55.6% win, +8 814 USD (2024-01→2026-07, 10 монет) | **Нет независимого trade-by-trade native архива в обследованном репозитории**; fee/slippage, funding и 5m intrabar требуют OOS. Автор пишет о 53 dry-run сделках и −91 USD у другого варианта `SingleB`, не путать с FixedRR | **PRIORITY_2 / NATIVE_OOS_NEEDED** |
| C | BinHV45_Regime_5m v3 / v4 | Перепроданность/капитуляция и возвращение к средней, 5m + 30m/1h фильтры; spot long-only | Открытый исходник v3 и v4, автор v3 314 trades, +22.53%, win74.5%, DD4.13% (2025-12→2026-06), 40 coins | Авторский PAPER в июне—августе 2026 деградировал по фазам 77%→59%→44% win; убытки после пересмотра динамического списка пар. Другой состав портфеля, spot, v4 не эквивалентен v3 | **RESERVE_ONLY_WITH_STATIC_PAIRS_AND_NEW_OOS; НЕ экономический PASS** |
| D | Funding Rate Carry OU (aayanvatsa04) | spot long + perp short на BTC, фондирование, low-frequency delta-neutral | Исходник модели, обеих ног исполнения и 128 тестов автором; автор 10 сделок, +9.38 USDT при номинале 1000 USDT, 2024-06→2026-06 | Мизерное число событий, требуются две ноги и расчёт маржи/ликвидации/полного капитала; **не заменяет 3–5 сетапов в день** | **DIVERSIFIER_ONLY; feasibility/test** |
| E | MsFilterV6 | TSI crossover + market structure 4h long/short | Автор +39.85%, PF1.50, 164 сделки | Проверка 15 публичных receipt JSON: крупнейшие 3 сделки **383.41 из 398.52 USD прибыли (96.2%)**; без этих трёх остаётся +15.11; BTC и LTC отрицательны. Кода класса стратегии нет | **LOW_PRIORITY / NOT_RESERVE_FOR_NOW** |
| F | TrendFutures (Kureshi25) | Daily Donchian breakout long/short futures | Автор OOS по четырём walk-forward окнам среднее +4.2%, 2/4 прибыльные | Сам же автор показывает **−66.5%** на полном сценарии при 1×, 156 trades; дневная редкая частота | **REJECT_AS_PROFIT_BACKUP** |
| G | Ultimate Alpha v16 (OfficialGIGA) | ML model, 4h, 17 coins | Автор 139 dry-run сделок | На PAPER минус **94 USD**, 32.4% winners, модельно сложен, отсутствует очевидное независимое преимущество | **REJECT** |
| H | GeneticEngineV1 (ceyhanmolla) | Генетические индикаторы, 5m spot | Автор +42.56% 183 trades 98.9% wins | PF `90+` автор обозначает **оценочным**, не прямым расчётом trade receipts; 3-месячное IS, возможный overfit | **REJECT_UNTIL_INDEPENDENT_SOURCE_TRADES** |
| I | Cross-sectional momentum/mean reversion (billybraith17) | Relative long/short spot Kraken | Полный research-код, walk-forward, корректировки multiple-testing | Автор не нашёл прибыльности **после спредов/комиссий** на spot; полезно как методология, не стратегия | **RESEARCH_MATERIAL_ONLY** |

## Пересчёт опубликованных trade receipts Market Structure (НЕ native replay)
Репозиторий `https://github.com/fortunato/pymarket-structure`, публичные 15 файлов `refs/freqtrade/backtest_results/{strategy}-{coin}USDT-4h-trades.json`. Простая арифметическая сверка `profit_abs`, не проверка корректности генерации входов.

| Стратегия | N | PnL USDT | PF | Win % | топ-3 победителей / общая прибыль | Прибыль без топ-3 |
|---|---:|---:|---:|---:|---:|---:|
| MsSupportResistanceV1 | 404 | +703.15 | 1.376 | 42.57 | 35.3% | +454.97 USD |
| MsFilterV6 | 164 | +398.52 | 1.504 | 35.98 | 96.2% | +15.11 USD |
| MsFilterV6NoMs (контроль) | 208 | +225.94 | 1.214 | 31.73 | 169.7% | −157.46 USD |

MsSupportResistanceV1 по символам: BTC N74 +86.82 USD, ETH N84 +128.89, SOL N76 +176.45, XRP N98 +218.55, LTC N72 +92.44; это *выборка автора*, не independent OOS. Сумма всех пяти = +703.15 USD. Оригинальный автор сообщил 1000 USD старт, stake300, 3 параллельных позиции, 360 дней, PF1.38, MaxDD18.1%.

Проверка *факт существования полного кода* для классов `MsSupportResistanceV1` и `MsFilterV6`: дерево Github main содержит библиотеку `src/market_structure/freqtrade.py`, тесты структур, публичные свечи/trade JSON и markdown, **но исходники конкретных Freqtrade классов не найдены**. Искать и сверять программный код до присвоения статуса воспроизводимой готовой стратегии.

## Ссылки на код и исходники
- https://github.com/fortunato/pymarket-structure/blob/main/refs/freqtrade/README.md
- https://github.com/fortunato/pymarket-structure/blob/main/src/market_structure/freqtrade.py
- https://github.com/liu57liu456/backtest-autopsy/blob/master/strategy/SingleB_FixedRR.py
- https://github.com/liu57liu456/backtest-autopsy/blob/master/README.md
- https://github.com/zevrichards/freqtrade-strategies/blob/main/BinHV45_Regime_5m.py
- https://github.com/zevrichards/freqtrade-strategies/blob/main/BinHV45_Regime_5m_v4.py
- https://github.com/zevrichards/freqtrade-strategies/blob/main/INTELLIGENCE_REPORT.md
- https://github.com/aayanvatsa04/btc-perpetual-funding-arbitrage
- https://github.com/Kureshi25/cryptobot
- https://github.com/OfficialGIGA/freqtrade-ml-strategy/blob/main/RESULTS.md
- https://github.com/billybraith17/crypto-stat-arb

## Следующие тестовые циклы (без подгонки)
1. A190: проверить доступность **полного класса** MsSupportResistanceV1; без оригинального кода лишь классифицировать структуру/сигнал и проверить, не является ли опубликованная история воспроизводимой. Никаких заявлений о готовой стратегии до оригинального engine replay. Сравнить источники и геометрию SL/TP, 4h lifecycle, commission/funding, no-lookahead.
2. A191: `SingleB_FixedRR`: immutable исходник, freqtrade native 2026.4 (версию совместимости проверить), исторические 5m 5–10 ликвидных пар, OOS после июля 2026 и независимый более ранний bear window, 5m vs 1m detail, fees 10/25/40bps round trip + funding, low leverage, pairs fixed, fail if missing. Не оптимизировать на OOS. Сравнить с random direction and dumb momentum.
3. A192: `BinHV45_Regime_5m` v3 and v4 на **одинаковых** 5-10 статических ликвидных парах в Binance spot vs futures (1× long-only), с высокими costs и fallback close delay. Авторские +22.53% на 40 coin *не переносить* на иной портфель. Требуется честная проверка на июль–октябрь 2026, когда в PAPER у автора деградировала статистика.
4. A193: Carry только как дополнительный некоррелированный low-turnover модуль, тест по двум биржам, model borrow/liquidation, реальные funding settlements, bid-ask, полный капитал/маржу, reject if fee budget nonpositive. Второе исследование `DavidAyusoPita/funding-carry-analysis` показывает при частой перебалансировке **−9...−15% годовых** после costs и всего +2.7...+5.4% годовых от долгого удержания — риск не оправдан при ограниченном капитале без особого fee tier.

**Критерий выбора:** только immutable native OOS, no lookahead/recursive bias, разумное N и собственно объяснимый net edge после costs/realistic fills. Никакой LIVE и изменений текущего PAPER. Данные A189 — лишь shortlist research.
