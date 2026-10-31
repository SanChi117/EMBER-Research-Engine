# A199 — реестр готовых оригинальных стратегий, инженерный допуск до экономики

Дата фиксации 31.10.2026. *Рынок BTC/ETH/SOL/LINK Binance USD-M, две платы, модельный $100 stake / $1000 отдельно, PAPER ONLY.* ВЫБОР ПО СВОЙСТВАМ КОДА, не по результатам будущего 2026 native test.

| Исходный открытый механизм | Исходный TF | Совместимость с нашими 4 futures | Допуск в A199 | Почему |
|---|---|---|---|---|
| `freqtrade/freqtrade-strategies/user_data/strategies/futures/FReinforcedStrategy.py` exact source blob `11bfdde9...` | **5m**, источник resampled 1h SMA50 | can_short=True, native Freqtrade 2026.4, стоп 5% | **ДА** | EMA8/21 cross + 1h trend, ADX exit, изначальный Futures, ожидаемая частота больше часовых систем; сигнал и exit в авторском Freqtrade |
| `freqtrade/freqtrade-strategies/user_data/strategies/futures/FAdxSmaStrategy.py` exact source blob `3bb13caf...` | **1h** с настоящей детализацией исполнения 5m | can_short=True, native Freqtrade | **ДА / КОНТРОЛЬ** | Нестратегически отличающийся ADX + SMA12/48 cross, низкая частота может отклонить гипотезу |
| `FSampleStrategy.py` (official futures example) | 1h | can_short=True | РЕЗЕРВ | Образец и обучающий код, без независимой истории доходности |
| `FSupertrendStrategy.py` | 1h | в исходнике нет `can_short=True`, stop −26.5%, Supertrend indicator source сам отмечает отсутствие академической валидации | НЕТ | Не подходит для короткого риска; не разрешено подменять исходные правила |
| `FOttStrategy.py` | 1h | сам файл импортирует `from numpy.lib import math` (требует совместимости), исходный стоп 26.5% | НЕТ | Исполнение под наш консервативный размер позиции не валидировано |
| `freqtrade/freqtrade-strategies/berlinguyinca/Scalp.py` | **1m** spot long-only | Автор исходника рекомендует **60 одновременно открытых позиций** | НЕТ | Не по масштабу малого депозита 4–5 пар; не переносить в Futures путем добавления шортов |
| `iterativv/NostalgiaForInfinity` (NFI X8) | **5m** multi-timeframe | Авторское руководство рекомендует **40–80 pairs**, 6–12 concurrent trades; преимущественно spot long | ПОЗЖЕ, ОТДЕЛЬНЫЙ ТЕСТ | Многопарная инфраструктура и большая экспозиция; не доказана полезность на 4 монетах, не должна считаться готовой малодепозитной Futures |
| `nateemma/strategies/Basket/MomentumRegimeBasket15mFast.py` | 15m **spot long-only** | Авторский 90d/14d cross-sectional momentum basket c top3 и 75 пар, возраст удержания дни/недели, maxDD по периодам >40% | НЕТ | Отличается от целевой краткой Futures стратегии, концентрация результатов на редких хвостовых событиях |
| `nateemma/strategies/Reversion/OversoldReversion.py` | 1h spot long-only | stop−99%, time-based exit, 1250h startup | НЕТ | Для малого риска нет исходного биржевого стопа, не готов Futures короткий ход |

**Принцип:** опубликованные official `freqtrade/freqtrade-strategies` — авторы прямо предупреждают «examples/educational; not guaranteed profitable». Никогда не отмечать прошедшими как `NET>0`, пока нет своих нативных исходных ZIP.

**Сфера последующей работы:** если A199 два исходника не пройдут gate, не подменять проблему оптимизацией: расширить поиск до новых авторских Futures 5/15m систем с опубликованным backtest source и анализом fee+slippage, затем независимо перепроверить. Частота **4 отдельных pair wallets** не есть реальная частота общего портфеля: учитывать корреляцию и пересечения сигналов.

**Никаких ордеров и включения авто-торговли.**
