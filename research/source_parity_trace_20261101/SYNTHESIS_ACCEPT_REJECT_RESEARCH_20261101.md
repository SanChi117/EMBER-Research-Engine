# EMBER · Проверка реальной сочетаемости P07 / P10 · 2026-11-01

**Контрольная точка:** `MECHANISM-SYNTHESIS-01`. **Это анализ механизмов и протокол выбора гипотез, НЕ ещё одна самостоятельно внедряемая стратегия**, не проверка PnL. Основной `RESEARCH_MANDATE_LOCKED.md` / issue #9 не изменены; главная задача — найти несколько независимо проверяемых исходных **Binance USDT-M Futures** стратегий и только после механического аудита проверить расходы, сделки и устойчивость. Гипотезы сопровождения TP1/BE/TP2/TP3 из прошлого обсуждения остаются **необязательными**, не превращать в правило.

## 1. Суммарная картина по исходникам

| Механизм | Зачем он может пригодиться | Что доказано реальными свечами / чтением исходного кода | Чего НЕ доказано |
|---|---|---|---|
| [P07 PerpLab PullbackRetest](https://github.com/analogdada/perplab/blob/68251be7e1b4c0ade110bd4e097d524c6ce2acbc/src/perplab/strategy/library/pullback_retest.py) | **State machine** «пробой диапазона → возврат → повторный выход», предполагаемая причина дальнейшего хода — появление спроса/предложения после смены рыночной границы | **134 source signals**, BTC53/ETH39/SOL42 на 1499 H1 закрытых свечах по монете. **16 сигналов с возрастом >5 баров** из-за порядка проверок. Ранее 109 событий с пересечением уровня по wick и 44 retest close без физического касания уровня wick | Что пробой принят рынком, что уровень держится, где **защищённый swing SL**, будет ли преимущество |
| [P10 rgg81 BbSqueeze](https://github.com/rgg81/crypto-trade/blob/65cf4284e7a397673d1ac8c982f0d113027ed27b/src/crypto_trade/strategies/indicator/bb_squeeze.py) | **Volatility state transition**: разжатие BB с повышением объёма, самостоятельный кандидат момента расширения активности | **54 source signals** (BTC18/ETH21/SOL15) на H1; код не требует настоящего пробоя внешней границы BB, а при native backtest исходный close-fill вызывает риск исполнения «задним числом» | Это **не структурная Entry/SL/TP стратегия**; CLI default **15m**, его native parity на 15m не выполнен |
| [P06 FailureToReturn](https://github.com/hrodrig/freqhub-strategies/blob/210952246ae457a5f6d5e089ddea8b4960a71775/strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py) | **Impulse + level reclaim**, более строгая проверка самого события | Оригинальный класс на real TA-Lib + FT shim дал всего **1 LONG** в текущей H1 выборке, **SHORT tags не исполняемы** при can_short=false | Native Freqtrade parity, достаточная выборка, structural SL/TP |
| P01/P04/P05 TSMOM/CTA | Общая **направленная инерция**, context, не обязательный фильтр | Готовая исходная логика, пригодна для независимого аудита; не даёт однозначной локальной структурной Entry/SL/TP | Что доп. фильтр реально улучшает P07/P10, а не просто отбрасывает сетапы |

## 2. Новый независимый контроль: нельзя просто потребовать P07 И P10 вместе

Выполнен [исходник независимого счётчика](./p07_p10_overlap_gate_20261101.py), [автотест](../../tests/test_p07_p10_overlap_gate_20261101.py); реальные Binance USDT-M, 1499 **полных H1** свечей / монета, SHA256 `b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7`, код оригиналов pinned P07 blob `4b04c1834bbf0a3e69d9e67542aea204718550c8` и P10 blob `7568c60cbef2157065d2d1b8944ca5a4c965f39b`. Простая независимая реконструкция **совпала с ранее проверенным native Python source signal количеством 134/54**, в т.ч. 16 late P07, но остаётся отдельной реализацией.

**Предзаданные описательные окна**: P10 должен сработать на **той же монете, в том же направлении**, не ПОЗЖЕ сигнала P07; без будущих свечей.

| Период до P07 включительно | P07 с P10 перед ним | P07 БЕЗ такого P10 |
|---|---:|---:|
| Та же H1 свеча | **4/134** | 130 |
| Предыдущие 3 H1 свечи | **18/134** | 116 |
| Предыдущие 6 H1 | **24/134** | 110 |
| Предыдущие 12 H1 | **31/134** | 103 |
| Предыдущие 24 H1 | **36/134** | 98 |

По символам **в пределах 3h** совпало BTC 8/53, ETH 6/39, SOL 4/42. Поэтому конструкция **«P07 обязательно после P10» не может объявляться универсальным улучшением**: при 3h окне она исключает 116/134 (~86,6%) исходных событий ещё до проверки их исходов. **Это НЕ означает, что совместные события плохие или хорошие**; процент пересечения не прибыльность. Расширять окно постфактум ради количества было бы подгонкой.

## 3. Содержательная минимальная гипотеза — не «ёлка из индикаторов»

**Главная гипотеза `ACCEPTANCE_VS_REJECTION`:** торгуем не «сигнал RSI/BB», а **реакцию цены на заранее известную границу диапазона/свинга**. Возможное преимущество — разная динамика участников после **принятия** цены за границей и после **отказа принять её**. Это причинная интерпретация, **не доказанный поток вынужденных ликвидаций**, поскольку OHLCV не раскрывают реальный order flow.

Две альтернативные **семьи событий**, а не два одновременных обязательных фильтра:

- **A / Continuation / ACCEPTED BREAK**: prior confirmed range/swing boundary → close breakout beyond prior level → retest of SAME known level → **verified hold** (no unprotected wick penetration beyond invalidation) → rebreak/continuation trigger at following tradeable bar. **P07** поставляет source state machine; **P06** — независимый пример импульсного фильтра (не включать автоматически); **P10** — параллельную метку volatility expansion, необязательную и подлежащую ablation.
- **B / Rejection / FAILED BREAK**: цена **по wick** сняла видимый прежний high/low, но закрылась обратно внутри диапазона; затем либо подтвердилось отклонение/структурный сдвиг и есть причинная точка входа/стоп за экстремум, либо `NO TRADE`. В исходном P07 это **отдельная не исследованная модель**, а НЕ готовый исполнитель. Нужен **самостоятельный оригинал**/независимый источник и доказательство, что не повторно используется отвергнутая стратегия.

**Базовые общие компоненты**, но не финальная стратегия: (1) ex-ante уровень с временем подтверждения и статусом несломан/сломан, (2) однозначные события BREAK/RETEST/ACCEPT/REJECT/EXPIRE, (3) проверяемое **структурное** invalidation/SL, (4) заранее существующая реалистичная первая opposing area / destination, (5) независимый аудит исходников и причинное next-open / limit execution. Дополнительные режимы тренда/объёма/сжатия — **отдельные вопросы**, а не «надёжность 80%» из нарисованного скоринга.

**Принцип реализации:** `source → independent trace → compare base setup vs one explicitly labelled experimental adaptation → only then monetary/OOS`. До этого никаких смешанных «готовых прибыльных» бэктестов и заявок.

## 4. Что нашёл в открытых новых исходниках (не путаем код с доказанной прибылью)

| Источник | Подтверждённое устройство и inspectable blob SHA | Вердикт |
|---|---|---|
| [Kureshi25/cryptobot AdaptiveRegime.py](https://github.com/Kureshi25/cryptobot/blob/main/user_data/strategies/AdaptiveRegime.py) | Real Freqtrade strategy blob `7b0f5fbe2157d45ef52e4ee48155c06f3f057628`; 1D regime Kaufman **Efficiency Ratio**: trending Donchian + EMA200; ranging RSI+BB mean-reversion; между режимами нет входов. Точки выхода по channel/BB mean, SL по ATR, **не local structural**. Никаких независимых Binance futures PnL/OOS здесь ещё нет. | **RESEARCH_REGIME_COMPONENT / ORIGINAL SOURCE AVAILABLE**; можно изучать раздельный трендовый и возвратный подмеханизмы, **не принимать как прибыльный** |
| [Kureshi25/cryptobot TrendFutures.py](https://github.com/Kureshi25/cryptobot/blob/main/user_data/strategies/TrendFutures.py) | Real Freqtrade 1D Donchian + EMA200 LONG/SHORT; blob `2e6b83ba128373655090ca4827d8c7954ffaedfd`; channel **shift(1)** корректно исключает текущую свечу. Прежний наш A211: 1D Donchian — отрицательный/неустойчивый. | **DUPLICATED_FAMILY / HOLD**. Не повторять отрицательный цикл без НОВОЙ исходной гипотезы и внешних независимых данных |
| [jicheolha/crypto-trading-bot](https://github.com/jicheolha/crypto-trading-bot) | Реальный code `backtester.py`, blob `4b9426bddc22912dcd0fb7ed233141d5d0e9c1f9`; BB squeeze, фьючерсная экономика **Coinbase**, не Binance USDT-M; заявленная прибыль не была воспроизведена. | **VENUE_TRANSFER_NEEDED / SOURCE_COMPONENT_ONLY**. Не считать дополнительным проверенным Binance futures кандидатом |
| [Jotanune/CryptoGuardian](https://github.com/Jotanune/CryptoGuardian) | README описывает liquidity-sweep и WFO, но публичное дерево (Git tree `179dcc203a61840ee6a37e0b279a0622e0321bf7`) содержит showcase / dashboard / risk, **без исходного торгового ядра SMC**, по которому можно воспроизвести сделки. | **SOURCE_BLOCKED**: таблицам README не верить как независимой проверке |
| [sarahleesoffice/Macro_Liquidity_Sweep-_Backtester](https://github.com/sarahleesoffice/Macro_Liquidity_Sweep-_Backtester/blob/main/ict_2022_backtest.py) | Реальный Python код `ict_2022_backtest.py` blob `a6a429a4524aef8054977fd34b2a968601f24248`, конструкция sweep→MSS→FVG→SL beyond wick→TP swing. **Но исходный рынок NQ/QQQ**, а не Binance USDT-M. | **NONCRYPTO_REFERENCE_ONLY**: концепция проверки структуры, не предмет переноса как подтверждённый Futures-кандидат |
| [Freqtrade VolatilitySystem.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/futures/VolatilitySystem.py) | Публичный futures пример c ATR expansion trigger и большим stoploss (в опубликованном коде `stoploss=-1`), source tree SHA `15ce2473f3f60bd33c4a67b0b8b228e379850f19`. Нет верифицированной структурной SL/TP геометрии. | **OPTIONAL_INDEPENDENT_VOLATILITY_REFERENCE**, не отдельная проверенная прибыльная система |

Таблица — **аудит доступного исходного кода**, не утверждение о текущем GitHub HEAD после pinned blob и не обоснование совместной торговой стратегии.

## 5. Внешняя исследовательская опора — осторожное прочтение

- Chi et al., *An Empirical Investigation on Risk Factors in Cryptocurrency Futures* (Journal of Futures Markets, 2023): cross-sectional futures **basis** существеннее простого momentum; momentum-alone не имеет столь убедительной статистической силы; исследование другого периода (2017–2021), не доказывает Binance конкретный торговый вход. [DOI](https://onlinelibrary.wiley.com/doi/full/10.1002/fut.22425).
- Morin & Moore, *The Impact of Cryptocurrency Spot Price Volatility on Derivative Markets* (SSRN, 2024): на 5m встречаются существенные отклонения spot/perp и возвратные изменения, что согласуется с **возможностью** отличающихся mean-reversion условий; нет в нём доказательства доходности P07/P10. [Paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729600).

## 6. Очерёдность разумных фальсификационных проверок (не новая обязаловка)

1. **P07 Acceptance**: почему 16 сигналов после timeout, 44 ретеста без wick touch, какие группы относятся к действительному удержанию заранее известного уровня. Диагностировать различие source strict hold / adaptation без обещания улучшения.
2. **P10 Expansion** отдельно: проверить исходный **15m** original default и независимый native trace. Сравнивать режим-событие с P07 как независимые источники; не делать `P07 AND P10` обязательным.
3. **Rejection-семейство**: найти original Binance USDT-M или переносимый нативный futures исходник sweep/reclaim. NQ и README-only не подходят. Для поддерживающих контр-тестов можно сравнивать естественные диапазонные события на **уже замороженной Binance USDT-M истории** с честной пометкой `ADAPTATION_HYPOTHESIS`, но это **не заменяет оригинальную стратегию**.
4. **Критерий остановки**: если события не дают пригодного Entry/SL/TP, отсутствует независимый source parity или только случайные пересечения индикаторов — **STOP / HOLD**, а не раздувать скоринг/количество фильтров.
5. Только после стадии понимания **откуда** может появиться эффект и проверки оригиналов — экономические / risk / OOS и доработки для PAPER; этот документ **не санкционирует** новые сделки.

## 7. Decision

**Предлагаемая исследовательская архитектура:** `ONE_EX_ANTE_RANGE_LEVEL → ACCEPT/REJECT BRANCH → STRUCTURAL INVALIDATION → FIRST_GROUNDED_DESTINATION`, с **P07 и P10 независимыми исходными кандидатами** и только потенциально ситуационными labels, а не обязанными совместно срабатывать фильтрами. `TWO_BRANCH_SOURCE_PARITY_NOT_YET_COMPLETE`, `PROFITABLE_STRATEGY_NOT_YET_VERIFIED`. Это самая простая на данный момент **внятная гипотеза объединения знаний**, не существующая исходная проверенная profitable система.
