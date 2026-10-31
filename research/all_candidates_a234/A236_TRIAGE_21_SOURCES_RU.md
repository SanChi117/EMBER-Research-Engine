# A236 — обработка всех 21 неразобранных ссылок A234 (audit of available evidence, NOT economic replays)

Дата 31.10.2026. База: `A234_COVERAGE.json`, 21 запись `UNCLASSIFIED_SOURCE_REVIEW_REQUIRED`. Для трех ранее голых ссылок получен актуальный исходный репозиторий и закреплённый commit; остальным дана **предварительная** классификация по историческим свидетельствам A234. Никакой результат не переименован в прибыльный; перенос SPOT → Binance USDT-M сам по себе не воспроизводит исходный тест.

## Источники, требующие дальнейшего внимания

| Источник | Отношение к Binance USDT-M и статус |
|---|---|
| `knacker65/v5-crypto-scalper` | **R075 / OPEN TRANSFER**. В README автора описан `Momentum only, both directions` +$415 за 3 года при 3× (заявление, НЕ независимый EMBER результат). Пин `eafcdbbdcc60d8b1ac3b7377c5220e886a1fc3d6`, `backtest_perps.py` blob `ddc817afd9a0ba0baa2967868bdd98d0bad2e58c`, README blob `7f7c2d2dff653ce443203a0af315ac2996858ee4`. Автор сам пишет `PURELY RESEARCH`, зеркалирует short из long, **игнорирует funding**, загружает локальные `backtest_data/*.pkl`; независимое происхождение свечей именно USD-M не установлено, нет маржинальной/ликвидационной проверки. Нельзя считать готовым futures winner. Следующее действие: проверить источники .pkl, fills и ledger прежде повторения на genuine futures. |
| `billybraith17/crypto-stat-arb` | **R076 / OPEN TRANSFER**. Пин `19f51e8c1b091245579cd06172c3d0bd3d083c85`, README blob `d891587a07e08fcdf74055b0b750106ba4e5e64f`. Автор исследовал **Kraken SPOT 1h mean reversion**; небольшой gross сигнал ниже рыночных издержек, futures предлагает лишь как следующую работу. Требуется выяснить, есть ли оригинальная исполнимая futures-версия; пока не разрешена экономическая классификация Binance USD-M. |
| `xujaan/futurabot` | SOURCE_REVIEW, не новый прибыльный оригинал: сложная конфигурация SMC/OBI/CVD/VPIN, нет самостоятельного доказательного OOS-журнала в ранее прочитанном отчёте. Если появится source+futures receipts, включить отдельную запись, не «улучшать» исходник. |
| `denniskid2520/btcusdt-perp-live` | Уже покрыт записью **R052**, связан с другим `research-archive`. Подтверждённый в старом отчёте lookahead касается конкретного архивного слоя; production требует отдельной проверки, а не автоматического FAIL. |

## Остальные 17 ссылок: источник и основание для следующего действия

| Источник | Проверка по предыдущим закреплённым свидетельствам |
|---|---|
| `DylanSiegel/GO-Microstructures` | Futures aggTrades и исследовательская Hawkes-модель, но нет исполнимого net portfolio/queue; `TOOL_SOURCE_ONLY`. |
| `HodlHook/momentum-breakout-postmortem` | Авторские варианты Qullamaggie с опубликованным отрицательным OOS; `NEGATIVE_EVIDENCE_KEEP`, не повторять подгонку без новой гипотезы. |
| `MG-Trading-Terminal/trading-strategy` | Документация позиционирования без восстановленного полного исполнителя; `SOURCE_BLOCK`. |
| `Mykola-Quant/retail-crypto-alpha` | Отрицательные заявленные автором futures OOS идеи; `EXTERNAL_NEGATIVE`, не наш бэктест. |
| `PVinh-Quant/Kairos-v2` | Исследовательская инфраструктура, не изолированная стратегия с edge; `TOOL_ONLY`. |
| `SebastianBoehler/MarketTensor` | ML baseline и слабая опубликованная разница (0.0828 vs 0.0822 Sharpe); `INSUFFICIENT_EDGE_EVIDENCE`. |
| `Superjojo74/nautilus-perp-funding` | Библиотека funding settlement, `TOOL_ONLY`. |
| `analogdada/perplab` | Futures testing engine, автор не утверждает embedded profitable edge; `TOOL_ONLY`. |
| `behlulgoker/price-action-engine` | Код зависит от Binance **SPOT** `api/v3/klines`; `VENUE_TRANSFER_BLOCK`. |
| `bockuden/crypto-cointegration-research` | Отрицательное опубликованное after-cost spot/perp basis, близко к A212/A213; `EXTERNAL_NEGATIVE`. |
| `chiragbitoni/binance-paper-trading-lab` | PAPER-инфраструктура; исходная стратегия Spot, отдельная futures sim не подтверждена; `TOOL_ONLY`. |
| `francisx1999/crypto-trading-bot-postmortem` | **Вновь закреплён код:** commit `53babe6c478934c91491366078c8600c5616e07d`, README blob `b105390954222062e5b14d785abdeb4916339436`, оригинальный `BotTraderStrategyV5.py` blob `d4b90da0d0796188d00f1835b20c72610cf49f86`; автор сообщает 7/7 отрицательных тестов на **Kraken/Coinbase**, НЕ Binance USD-M. `EXTERNAL_NEGATIVE_DIFFERENT_MARKET`; сохранять как методическое свидетельство, не универсальный FAIL фьючерсов. |
| `joseph280/crypto-backtest-lab` | Демонстрационная синтетическая прибыль; `TOOL_ONLY`. |
| `spagnola-analytics/intraday-strategies` | Оригинал CME MES/equity futures, не криптовалютный USD-M; `VENUE_MISMATCH`. |
| `ycchew/CQ_breakout_strategy` | Yahoo/equity-календарь и подбор параметров, нет причинного futures OOS; `VENUE_MISMATCH`. |
| `younghwan91/quantbox-engine` | Репозиторий не восстановлен по старой ссылке, `SOURCE_BLOCK`; не выдавать за отрицательную экономику. |
| `zabor-crypto/zaBor` | Инфраструктура/риск, не самостоятельная прибыльная стратегия; `TOOL_ONLY`. |

## Контроль полноты

**21/21** старых неразобранных ссылок получили адресное предварительное решение: 2 добавлены в машинное расширение очереди, 1 дубль R052, остальные 18 остаются либо источниками методики/инструментами, либо отрицательными внешними свидетельствами, либо SOURCE/TRANSFER-blocked. Это **классификация оснований**, не 21 заново выполненный бэктест и не гарантированная полнота всех исторических платформ.

Активный реестр: A234 = 74; дополнение A236 = 2 (R075, R076); **76 записей кандидатов/вариантов в совокупности**, не 76 доказанных экономических исследований. Исходный A234 не перезаписан задним числом. Для источников с SOURCE_BLOCK оставить возможность возврата после обнаружения точного исходника. A235 параллельно исправляет неверный timeframe трёх оригиналов на подлинных данных.

**Статус подтверждённых `VERIFIED_FUTURES_CANDIDATE`: 0.** Нет торговых ордеров или изменения PAPER-планировщиков; мандат LOCKED не менялся.
