# EMBER — проверенная инвентаризация дополнительных деталей («запчасти»)

**Дата:** 01.11.2026. **Версия:** v2 — повторная сверка именно первой части задачи. **Режим:** DOCS-ONLY; ничего не внедрено, не оптимизировано и не тестировалось на рынке.

> Важное исправление первого черновика: слово «нет» относится к **полной функциональности конкретной детали**, а не к отсутствию всяких похожих элементов. SMOKE уже умеет считать касания, качество и активность OB/FVG/swing; закрытые свечи, PAPER SL-first, примитивный риск/журнал, выбор монет по предыдущим сделкам, отдельные поля для funding, OI и taker. Нельзя выдавать всё это за новые модули.

## Итог именно библиотеки запчастей

| Проверяемый статус | Количество | Как трактовать |
|---|---:|---|
| `NEW_GAP` | 10 | Отдельного рабочего модуля в изученных активных слоях не обнаружено (это не доказательство отсутствия в каждой старой ветке) |
| `PARTIAL_GAP` | 27 | Основа уже есть, отсутствует **строго указанная ниже функция** |
| `ALREADY_PRESENT` | 1 | Базовая реализация есть, **не включать в запчасти как новое** |
| **Всего проверенных пунктов** | **38** | **37** остаются в библиотеке именно как новые функции/доработки |

**Отдельно:** все 76 исходных R-ID сохранены внизу с привязкой к деталям, 18 источников X01–X18 учтены, 3 пользовательских veto сохранены. **Не запускать никакие исследования по этому документу автоматически.**

## Что мы проверили в настоящем коде

- **EMBER:** `ember/core/features.py`, `ember/core/context_builder.py`, `ember/strategy/risk_engine.py`, `ember/strategy/exit_simulator.py`, `ember/simulation/portfolio.py`, `ember/simulation/walk_forward.py`, `ember/filters/structure_gate.py`, `ember/strategy/setups.py` и документация.
- **SMOKE:** `app/lib/level/{structure,zones,analysis-v3,analysis-v5-regime,backtest,math}.ts`, `services/market-data/binance-normalizer.ts`, `core/{contracts,ledger,paper,risk,state}`, `brains/{macro,trend,range,reversal,pump,arbiter}`, `strategy_lab/{mtf_feature_builder,portfolio_simulator,risk_model,rolling_symbol_strength,universe_selector,structure_learning,trade_quality_score,parameter_grid,paper_store}.py`.
- **Внимание:** некоторые новые SMOKE contract-поля (`fundingRate`, `oiChangePct`, `takerImbalance`) уже объявлены, но поля/схемы не доказывают работающий исторический data adapter, правильный расчёт индикатора или прибыльность стратегии.

## Результат сверки 38 потенциальных деталей (путь к нашему коду служит доказательством существующей основы)

| ID | Статус | Уже реализовано | Точный недостающий элемент | Файлы нашего кода |
|---|---|---|---|---|
| Z01 | `PARTIAL_GAP` | MarketDatum хранит exchangeTs/receiveTs и freshness; Binance-normalizer уже нормализует закрытые OHLCV. | Нет единого point-in-time as-of join для funding/OI/mark/L2 и времени публикации каждой записи. | [core/contracts/market.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/market.ts) · [services/market-data/binance-normalizer.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/market-data/binance-normalizer.ts) |
| Z02 | `NEW_GAP` | AutoQuantity считает qty/номинал/margin, EMBER RiskEngine ограничивает приблизительный риск. | Нет событийной maintenance-margin/liquidation-модели с mark price, funding, isolated/cross и tier-уровнями. | [core/risk/auto-margin.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/risk/auto-margin.ts) · [ember/strategy/risk_engine.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/risk_engine.py) |
| Z03 | `NEW_GAP` | Нормализатор сохраняет агрегат takerBuyVolume, схема BrainFeatureSnapshot — takerImbalance. | Не найдены L2-архивы, order queue/microprice и модели maker partial fill. | [services/market-data/binance-normalizer.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/market-data/binance-normalizer.ts) · [core/contracts/features.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/features.ts) |
| Z04 | `PARTIAL_GAP` | В SMOKE исторический анализ вызывает общий analyzeLevelFlow; decisionId, snapshotId и бумажные receipts предусмотрены. | Нет воспроизводимого побарного diff одного original signal между чужим движком, EMBER и SMOKE. | [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [core/paper/paper-receipt.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/paper/paper-receipt.ts) · [core/contracts/trade-plan.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/trade-plan.ts) |
| Z05 | `NEW_GAP` | EMBER/SMOKE поддерживают одиночные сделки и общую экспозицию. | Не обнаружен синхронный multi-leg ledger пары/хеджа с хедж-коэффициентом, разрывом исполнения и funding каждой ноги. | [ember/simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) · [core/ledger/store.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/ledger/store.ts) |
| Z06 | `PARTIAL_GAP` | SMOKE PAPER lifecycle считает комиссии/Net PnL, есть D1-системный ledger и сигнальные планы LADDER. | Нет доказанного событийного cash-ledger частичных fills, доливок, TP1–TP3 и пересчёта маржи при каждом событии. | [core/paper/paper-lifecycle.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/paper/paper-lifecycle.ts) · [core/ledger/store.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/ledger/store.ts) · [core/contracts/trade-plan.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/trade-plan.ts) |
| Z07 | `PARTIAL_GAP` | Есть PortfolioSimulator kill-switch и мозговой arbiter выбора гипотез. | Не найдена проверенная агрегированная риск-книга нескольких независимых стратегий с корреляциями и общим allocation budget. | [ember/simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) · [brains/arbiter/index.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/brains/arbiter/index.ts) |
| Z08 | `PARTIAL_GAP` | SQLite PAPER Store хранит сделки и вычисляет kill_status; event-bus сохраняет события в процессе. | Не доказано устойчивое после рестарта сохранение RiskState и восстановление breaker/cooldown на фактических позициях. | [strategy_lab/paper_store.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/paper_store.py) · [core/state/event-bus.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/state/event-bus.ts) |
| Z09 | `PARTIAL_GAP` | SMOKE backtest и PAPER решают пересечение SL/TP в одной свече консервативно: SL раньше. | Нет детальной 1m/tick последовательности при двойном касании в оригиналах и оценки диапазона неопределённости для отсутствующих данных. | [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [core/paper/paper-lifecycle.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/paper/paper-lifecycle.ts) |
| Z10 | `PARTIAL_GAP` | SMOKE PAPER имеет состояния pending/expired и документы с entry-minute audit; TradePlan содержит expiresAt. | Нет реального архивного queue/partial fill/reject/retry исполнения на бирже (это не то же, что PAPER pending). | [core/paper/paper-pilot-state.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/paper/paper-pilot-state.ts) · [core/contracts/trade-plan.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/trade-plan.ts) |
| Z11 | `PARTIAL_GAP` | SMOKE zones.ts уже считает OB/FVG/swing, score, distinct touches, active, mitigated/broken через closed candle. | Отсутствует подтверждённый единый wave-registry с явными переходами born→active→retest→flip, временем доступности каждого состояния. | [app/lib/level/zones.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/zones.ts) · [app/lib/level/structure.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/structure.ts) |
| Z12 | `ALREADY_PRESENT` | closedCandles, closedEndIndex/bundleAt и структура с pivot.index + right-bars выполняют базовую causal MTF доступность. | Не считать базовую HTF→LTF синхронизацию новой деталью; отдельные funding/OI availability gaps уже учтены в Z01. | [app/lib/level/math.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/math.ts) · [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [app/lib/level/structure.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/structure.ts) |
| Z13 | `NEW_GAP` | Есть готовые конкретные сценарии levels/reaction и функции PA, но нет общего правила-DSL. | Не найден самостоятельный декларативный движок price-action условий с causal on_bar и одинаковой обработкой bracket. | [app/lib/level/analysis-v3.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/analysis-v3.ts) · [app/lib/level/zones.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/zones.ts) |
| Z14 | `PARTIAL_GAP` | В BrainFeatureSnapshot есть COMPRESSION/EXPANSION, в SMOKE есть route/continuation, отдельный guardian state-machine. | Не подтверждён единый stateful compression→break→failed-return→restart с типизированными причинами и прогревом. | [core/contracts/features.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/features.ts) · [app/lib/level/analysis-v5-regime.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/analysis-v5-regime.ts) · [services/exit-guardian/state-machine.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/exit-guardian/state-machine.ts) |
| Z15 | `NEW_GAP` | Есть swing-pivots/BOS/CHoCH и структуры, но не библиотека графических фигур. | Не найдены независимые причинные H&S/double top/flag/triangle с индексом подтверждения. | [app/lib/level/structure.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/structure.ts) |
| Z16 | `NEW_GAP` | FVG-зоны, активность и качество уже существуют. | Не найден отдельный динамический FVG channel, который агрегирует последовательные gaps в границы upper/mid/lower. | [app/lib/level/zones.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/zones.ts) |
| Z17 | `PARTIAL_GAP` | Уже есть sweep_reclaim, `FAST_FLUSH_DETECTED→RECLAIM/FAILURE→EXIT` guardian. | Не обнаружен общий по стратегиям детектор failed-break как отдельное правило ранней invalidation/exit для breakout/PA. | [app/lib/level/types.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/types.ts) · [services/exit-guardian/state-machine.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/exit-guardian/state-machine.ts) |
| Z18 | `PARTIAL_GAP` | Есть evaluateRegimeGate (location/reversal/continuation), V5 режимы и macro brain. | Не доказана устойчивая гистерезисная/минимально-временная модель смены regime со сменой состояния по времени. | [app/lib/level/analysis-v5-regime.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/analysis-v5-regime.ts) · [brains/macro/index.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/brains/macro/index.ts) |
| Z19 | `NEW_GAP` | EMA/ATR/RSI и трендовые фильтры есть; отдельные HMA/EWO/SuperTrend/OTT не найдены в сверенном активном ядре. | Потенциально отдельные версионированные технические features, не автоматическая замена текущих EMA. | [ember/core/features.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/features.py) · [app/lib/level/math.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/math.ts) |
| Z20 | `PARTIAL_GAP` | В схеме BrainFeatureSnapshot поле fundingRate существует. | Не найден исторический funding event-series и OU/rolling z-score/half-life features с публикационной задержкой. | [core/contracts/features.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/features.ts) · [services/market-data/binance-normalizer.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/market-data/binance-normalizer.ts) |
| Z21 | `PARTIAL_GAP` | В BrainFeatureSnapshot есть oiChangePct; reversal brain учитывает его знак в score. | Нет отдельного priceΔ×OIΔ классификатора 4 квадрантов с taker confirmation и point-in-time историями. | [core/contracts/features.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/features.ts) · [brains/reversal/index.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/brains/reversal/index.ts) |
| Z22 | `PARTIAL_GAP` | Binance normalizer сохраняет takerBuyVolume, а BrainFeatureSnapshot — takerImbalance. | Не найден причинный rolling taker-pressure 5m/15m со сдвигом времени и независимым trace сигналов. | [services/market-data/binance-normalizer.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/services/market-data/binance-normalizer.ts) · [core/contracts/features.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/features.ts) |
| Z23 | `PARTIAL_GAP` | BTC и макрорежимы используются как context gate. | Не найдено event-study измерения BTC→alt lead-lag, секунды/минуты и прогноз окна задержки без будущих свечей. | [brains/macro/index.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/brains/macro/index.ts) · [app/lib/level/analysis-v3.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/analysis-v3.ts) |
| Z24 | `PARTIAL_GAP` | Есть RollingSymbolStrength, UniverseSelector и sector tags — они ранжируют символы по историческим сделкам. | Нет отдельно зафиксированного point-in-time rank по цене/volatility/14–90d и динамического basket rebalance, как в CTA. | [strategy_lab/rolling_symbol_strength.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/rolling_symbol_strength.py) · [strategy_lab/universe_selector.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/universe_selector.py) |
| Z25 | `NEW_GAP` | Простого portfolio и BTC context недостаточно для двухногой статистической сделки. | Не найден pair spread/hedge-ratio/cointegration z-score и одновременный fill обеих ног. | [ember/simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) |
| Z26 | `PARTIAL_GAP` | RSI, EMA и pullback у нас есть. | Не подтверждены независимые absolute SMA-dislocation, slow-decay curve 48–96h и лимиты исполнения для такого удержания. | [ember/core/features.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/features.py) · [strategy_lab/mtf_feature_builder.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/mtf_feature_builder.py) |
| Z27 | `NEW_GAP` | Обычные feature builders и WFO есть, но ML-inference не представлен как действующий штатный модуль. | Не найдены модельный artifact lifecycle, feature-schema SHA, train cutoff и live/paper inference parity. | [ember/core/features.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/features.py) · [ember/simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) |
| Z28 | `PARTIAL_GAP` | SMOKE умеет структурные зоны и планы с несколькими entryPrices/LADDER. | Не обнаружен самостоятельный GEM-детектор импульсной ноги и Fib 0.79 E1/E2 с ATR-gap и доказанной семантикой входов. | [app/lib/level/zones.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/zones.ts) · [core/contracts/trade-plan.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/contracts/trade-plan.ts) |
| Z29 | `PARTIAL_GAP` | У EMBER/SMOKE есть WFO, parameter_grid и отдельные профили. | Не найдены парные A/B matched-entry отчёты по одной отключённой feature с сохранением исходного signal timeline. | [strategy_lab/parameter_grid.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/parameter_grid.py) · [ember/simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) |
| Z30 | `NEW_GAP` | PF/Sharpe/DD и WFO-пороговые оценки есть. | В просмотренном ядре нет IC, deflated Sharpe и поправок на количество протестированных комбинаций. | [ember/simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) · [strategy_lab/parameter_grid.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/parameter_grid.py) |
| Z31 | `PARTIAL_GAP` | TradeQuality и StructureLearning строят breakdown по side/session/regime, SMOKE backtest выделяет long/short. | Не найден стандартный per-signal/trade top3-concentration и leave-one-symbol-out на неизменяемом universe. | [strategy_lab/structure_learning.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/structure_learning.py) · [strategy_lab/trade_quality_score.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/trade_quality_score.py) |
| Z32 | `PARTIAL_GAP` | В EMBER есть 7 no-leakage tests, SMOKE закрывает свечи и учитывает подтверждение pivot справа. | Не найдена общая автоматическая трасса `feature_available_at` для внешних стратегий, centred gradient, отрицательных shift и любого warmup. | [tests/test_no_leakage.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/tests/test_no_leakage.py) · [app/lib/level/structure.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/structure.ts) |
| Z33 | `PARTIAL_GAP` | В истории EMBER уже есть A240 авторский shared-wallet тест и ограниченные контролируемые USD-M прогоны. | Нет универсального побарного оригинал-vs-наш engine differential harness с полной сверкой config/account/portfolio/fill. | [ember/simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) · [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) |
| Z34 | `PARTIAL_GAP` | В SMOKE и EMBER уже учитываются фиксированные комиссии/скольжение, часть quote/freshness и score объёмов. | Не найдены participation cap как доля исторического объёма, market-impact curve и L2 maker partial-fill. | [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [ember/strategy/risk_engine.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/risk_engine.py) |
| Z35 | `PARTIAL_GAP` | Session bucket уже реализован в StructureLearning, WFO окна есть. | Не найден отдельный предварительно зарегистрированный независимый session/seasonality event-study без подбора лучшего окна на том же периоде. | [strategy_lab/structure_learning.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/structure_learning.py) · [strategy_lab/walk_forward.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/walk_forward.py) |
| Z36 | `PARTIAL_GAP` | Есть cooldown в SMOKE backtest и max open positions/capital в portfolio. | Не найден агрегированный отчёт permanent exposure, bar-to-bar repeated re-entry и занятости каждой стратегии/слота. | [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [strategy_lab/portfolio_simulator.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/portfolio_simulator.py) |
| Z37 | `PARTIAL_GAP` | Есть риск-профили, динамическая ставка, margin cap, kill switch. | Нет full event-time risk staircase с DCA, liquidations и stop exposure после каждого добора — не заимствовать без моделирования риска. | [strategy_lab/portfolio_simulator.py](https://github.com/SanChi117/smoke-trading-terminal/blob/main/strategy_lab/portfolio_simulator.py) · [core/risk/auto-margin.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/core/risk/auto-margin.ts) |
| Z38 | `PARTIAL_GAP` | У проекта есть разные executors/backtesters и CI тесты. | Не найден автоматический cross-runner, сравнивающий исходный Freqtrade/Pine/custom Python с EMBER на одинаковых data/hash и fills. | [app/lib/level/backtest.ts](https://github.com/SanChi117/smoke-trading-terminal/blob/main/app/lib/level/backtest.ts) · [ember/simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) |

## Что исключено из списка **новых** деталей

- **Z12 — базовый causal HTF→LTF merge.** SMOKE уже имеет `closedCandles`, `closedEndIndex`, `bundleAt` и подтверждение pivot после правых свечей. Повторно копировать функциональность нет смысла. **Но** межисточниковый point-in-time join для OI/funding/mark остаётся отдельным недостающим пунктом Z01.
- Уже имеющиеся элементы, не заявлять как новые: BOS/CHoCH, OB, FVG, счётчик касаний зон, score и active, ATR/RSI/EMA, MTF, sweep-reclaim, обычный SL-first, базовый fixed/slippage cost, cooldown, PAPER ledger, простая классификация BTC/макро, выбор монет на основании предыдущих сделок.

## Важные отличия новых функций от уже существующих

| Новая запчасть | Не путать с |
|---|---|
| Z11 полный wave registry/flip | существующим `zoneStillActive()` и `countDistinctTouches()` |
| Z22 rolling taker pressure | существующим полем `takerBuyVolume` из Binance свечи |
| Z21 квадранты Δprice×ΔOI | существующим отдельным `oiChangePct` у Reversal brain |
| Z20 OU/funding history | существующим полем `fundingRate` в типе |
| Z24 price-relative momentum rotation | существующим trade-performance `RollingSymbolStrength` |
| Z29 matched-entry ablation | существующими `parameter_grid.py` и WFO |
| Z17 independent failed-break exit | уже работающим `sweep_reclaim` и `Exit Guardian` |
| Z06 partial cash-event ledger | уже работающим PAPER single-close journal |

## Лицензии — предел возможного переноса исходного кода

| Источник | Проверка |
|---|---|
| `fortunato/pymarket-structure` | найден `LICENSE`: MIT |
| `stockalgo/stolgo` | найден `LICENSE`: MIT |
| `OctopusTakopi/crypto-trend-following` | найден `LICENSE`: MIT |
| `freqtrade/freqtrade-strategies` | найден `LICENSE`: GPLv3 |
| `hrodrig/freqhub-strategies` | найден `LICENSE`: GPLv3 |
| `traderhydr/krpticz`, `Gotodataru/binance-futures-backtest`, `tsuithomas/crypto_research_order_book_imbalance`, `djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen`, `chrysek70/hermes-trading` | файл с именем `LICENSE` не найден в этой проверке; разрешение на копирование не подтверждено, другие формы лицензий не исключены |

Это лишь запись проверок, **не юридическое заключение**. Нельзя копировать внешний код просто потому, что он открыт для чтения. В библиотеке сохраняются описания поведения и ссылки, не сам сторонний исходный код.

---

## Подробные карточки деталей: механизм, потенциальное новое, ограничения

## Подробные 38 карточек, включая один уже существующий эталон

### Z01 · P0 — Календарная доступность данных и point-in-time join

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** MarketDatum хранит exchangeTs/receiveTs и freshness; Binance-normalizer уже нормализует закрытые OHLCV. **Отсутствующая часть:** Нет единого point-in-time as-of join для funding/OI/mark/L2 и времени публикации каждой записи.

- **Источники:** R010,R023,R024,R025,R052,R075; X08.
- **Как работает:** Цена, mark, индекс, funding, OI, taker и стакан имеют разные периоды и моменты публикации. Сигнал должен видеть только сведения, которые уже появились к моменту решения.
- **Пересечение с нашим кодом:** EMBER: OHLCV/MTF/свечи; по исследованным core-модулям полноценного события funding/OI/mark нет.
- **Что потенциально добавить:** Единый event-time слой: event_time, published_at, available_at, venue, instrument, source_SHA; as-of join, контроль пропусков и задержек.
- **Ограничение / доказательность:** Без исторических архивов Binance USD-M mark/funding/OI/taker и точных timestamp нельзя признавать сигнал воспроизводимым.
- **Статус:** `SPARE_UNVERIFIED` в первоначальном архивном описании; **текущая оценка** — строка «Итог точной сверки» выше.

### Z02 · P0 — Фьючерсная маржа, ликвидации и mark-stop

**Итог точной сверки:** `NEW_GAP`. **Есть:** AutoQuantity считает qty/номинал/margin, EMBER RiskEngine ограничивает приблизительный риск. **Отсутствующая часть:** Нет событийной maintenance-margin/liquidation-модели с mark price, funding, isolated/cross и tier-уровнями.

- **Источники:** R004,R010,R011,R030,R038,R050,R075.
- **Как работает:** Баланс, маржа isolated/cross, maintenance tiers, funding, realised/unrealised PnL, mark-trigger и ликвидация пересчитываются после каждого события/добора.
- **Пересечение с нашим кодом:** EMBER risk_engine считает номинал/маржу приблизительно; README прямо указывает отсутствие модели ликвидаций и funding.
- **Что потенциально добавить:** Изолированный margin/liquidation simulator + сценарии гэпов, cross-collateral, ступени MMR, 2×/5×/20×; остановка до оценок прибыли.
- **Ограничение / доказательность:** Критично для −100% stop у R030, 5× R004, портфеля R011; не переносить риск-модель этих стратегий до проверки.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z03 · P0 — Фактическое исполнение лимиток и L2-микроструктура

**Итог точной сверки:** `NEW_GAP`. **Есть:** Нормализатор сохраняет агрегат takerBuyVolume, схема BrainFeatureSnapshot — takerImbalance. **Отсутствующая часть:** Не найдены L2-архивы, order queue/microprice и модели maker partial fill.

- **Источники:** R066,R039,R046,R053; X01,X02.
- **Как работает:** Из bid/ask sizes получают OBI и microprice; очередность заявок, spread, queue position, maker/taker и partial fill определяют реальную цену сделки.
- **Пересечение с нашим кодом:** Есть WebSocket/объём и моделируемая комиссия; полноценная историческая книга L2 и queue replay не подтверждены.
- **Что потенциально добавить:** Отдельный модуль microprice/OBI + реалистичная модель очереди лимитных ордеров; фиксировать data provenance и capacity.
- **Ограничение / доказательность:** OHLCV не восстанавливает историческую очередь; без архивов L2 можно только оценивать диапазон неопределённости, не выдумывать fill.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z04 · P0 — Сверка одного сигнального ядра между research и PAPER

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В SMOKE исторический анализ вызывает общий analyzeLevelFlow; decisionId, snapshotId и бумажные receipts предусмотрены. **Отсутствующая часть:** Нет воспроизводимого побарного diff одного original signal между чужим движком, EMBER и SMOKE.

- **Источники:** R036,R045,R052,R057.
- **Как работает:** Сигнал считается одной детерминированной функцией на закрытых входных данных; журнал содержит source version, feature values, signal time, submit/fill time.
- **Пересечение с нашим кодом:** В EMBER и SMOKE есть отдельные backtest/PAPER контуры; точный идентичный сигнал до каждой свечи не подтверждён.
- **Что потенциально добавить:** Signal replay contract: один и тот же модуль, снимок входа, хеш решения и diff на уровне каждого бара между режимами.
- **Ограничение / доказательность:** R036 делает pure-function engine, R045 ведёт артефакты и state; нельзя переносить их результаты Spot/ML напрямую.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z05 · P0 — Портфель двух ног и funding по каждой ноге

**Итог точной сверки:** `NEW_GAP`. **Есть:** EMBER/SMOKE поддерживают одиночные сделки и общую экспозицию. **Отсутствующая часть:** Не обнаружен синхронный multi-leg ledger пары/хеджа с хедж-коэффициентом, разрывом исполнения и funding каждой ноги.

- **Источники:** R046,R049,R067; X08.
- **Как работает:** Pair spread/cointegration или carry требует двух синхронных legs: цены, hedge ratio, funding по каждой, fees, недоисполнение одной ноги.
- **Пересечение с нашим кодом:** EMBER portfolio отслеживает сделки, но атомарную/частично заполненную пару в просмотренных модулях не обнаружено.
- **Что потенциально добавить:** Multi-leg portfolio ledger, partial-hedge exposure, hedge rebalance, transfer/venue risk и фиксирование legs.
- **Ограничение / доказательность:** Не считать арбитраж без риска: basis, borrow, leg slippage, ликвидация и рыночная нейтральность требуют отдельных проверок.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z06 · P0 — Частичные выходы, доборы и денежный журнал

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SMOKE PAPER lifecycle считает комиссии/Net PnL, есть D1-системный ledger и сигнальные планы LADDER. **Отсутствующая часть:** Нет доказанного событийного cash-ledger частичных fills, доливок, TP1–TP3 и пересчёта маржи при каждом событии.

- **Источники:** R010,R037,R038,R057,R060.
- **Как работает:** TP1/TP2/TP3, частичные закрытия, перенос стопа, пирамидинг/усреднение, финансирование и комиссии по каждой ноге должны менять оставшийся риск и капитал.
- **Пересечение с нашим кодом:** SMOKE имеет планы ENTRY/SL/TP и PAPER outcome; полный cash-event ledger для частичных fill/scale-in не подтверждён.
- **Что потенциально добавить:** Событийный ledger: fill_id, parent_trade, qty, fee, funding, margin, average_entry, remaining_stop_risk; invariants суммы.
- **Ограничение / доказательность:** R038 содержит funding на доливе; R057 state-machine TP; нельзя вписать фиксированное RR вместо авторской модели.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z07 · P0 — Общий риск нескольких разных движков

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Есть PortfolioSimulator kill-switch и мозговой arbiter выбора гипотез. **Отсутствующая часть:** Не найдена проверенная агрегированная риск-книга нескольких независимых стратегий с корреляциями и общим allocation budget.

- **Источники:** R011,R040,R060,R074; X18.
- **Как работает:** Независимые стратегии создают коррелированные позиции; общий RiskGuard ограничивает суммарный DD, gross/notional, overlap и stop exposure.
- **Пересечение с нашим кодом:** EMBER имеет портфельный kill switch; риск по нескольким отдельным стратегиям и корреляциям не подтверждён.
- **Что потенциально добавить:** Portfolio-level multi-strategy budget, конфликт сигналов и correlation netting; раздельный PnL/воздействие.
- **Ограничение / доказательность:** R060 ZENITH/GEM общий RiskGuard; закрытые модели R074 не переносить.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z08 · P0 — Персистентное состояние защит и восстановление после рестарта

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SQLite PAPER Store хранит сделки и вычисляет kill_status; event-bus сохраняет события в процессе. **Отсутствующая часть:** Не доказано устойчивое после рестарта сохранение RiskState и восстановление breaker/cooldown на фактических позициях.

- **Источники:** R008,R019,R050,R053.
- **Как работает:** Daily/weekly loss breaker и cooldown хранятся между сессиями; рестарт не должен сбрасывать запрещение входа; состояние сверяют с журналом/биржей.
- **Пересечение с нашим кодом:** В EMBER kill switches есть, но сохранение/восстановление после restart в изученных core-модулях не подтверждено.
- **Что потенциально добавить:** Persistent RiskState + restart/reconcile test, idempotent transition и запрет silent reset.
- **Ограничение / доказательность:** TSMOM меняет экономику при штатном breaker: без сверки нельзя объявлять исходный плюс валидным.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z09 · P0 — Тайминг очередности касаний и неопределённость intrabar

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SMOKE backtest и PAPER решают пересечение SL/TP в одной свече консервативно: SL раньше. **Отсутствующая часть:** Нет детальной 1m/tick последовательности при двойном касании в оригиналах и оценки диапазона неопределённости для отсутствующих данных.

- **Источники:** R016,R017,R018,R020,R021,R070.
- **Как работает:** В одной OHLC-свече TP и SL могут быть достигнуты в разном порядке; надо использовать 1m/tick, если есть, иначе диапазон лучшего/худшего исхода.
- **Пересечение с нашим кодом:** SMOKE разрешает спорные свечи SL-first; EMBER имеет баровую модель, но авторские fill-семантики могут отличаться.
- **Что потенциально добавить:** Необратимый dual-touch diagnostic; диапазон неопределённости, отдельные цены open/gap, TTL лимиток.
- **Ограничение / доказательность:** BIGBEAR/BIGBULL исходно использовали случайный выбор 50/50 при двойном касании: такой тест не подтверждает реалистичную прибыль.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z10 · P0 — Срок жизни ордера, missed fills и stale-data контроль

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SMOKE PAPER имеет состояния pending/expired и документы с entry-minute audit; TradePlan содержит expiresAt. **Отсутствующая часть:** Нет реального архивного queue/partial fill/reject/retry исполнения на бирже (это не то же, что PAPER pending).

- **Источники:** R018,R022,R053,R059,R061.
- **Как работает:** Сигнал, размещение, TTL, отмена, частичное исполнение, повторная заявка и stale candle — отдельные состояния.
- **Пересечение с нашим кодом:** SMOKE имеет pending/expired, но queue/missed_fill и время отправки на реальную площадку не доказаны.
- **Что потенциально добавить:** Order state-machine с timestamp→execution, missed fills, TTL, reject/retry и fee/latency sensitivity.
- **Ограничение / доказательность:** Не подменять limit entry гарантированным исполнением по свечному high/low.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z11 · P1 — Жизненный цикл структурных зон и качество волн

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SMOKE zones.ts уже считает OB/FVG/swing, score, distinct touches, active, mitigated/broken через closed candle. **Отсутствующая часть:** Отсутствует подтверждённый единый wave-registry с явными переходами born→active→retest→flip, временем доступности каждого состояния.

- **Источники:** R033,R034,R035.
- **Как работает:** Swings образуют волны; зона имеет born/active/touched/broken/retest/flip, wick bounds, score качества и конечную доступность в времени.
- **Пересечение с нашим кодом:** SMOKE имеет зоны/реакции; EMBER FVG/POI частично приближены, не доказана идентичность сложного zone-lifecycle.
- **Что потенциально добавить:** Сравнительный модуль market_structure: causal wave registry, per-zone provenance, quality и lifecycle.
- **Ограничение / доказательность:** Внешняя библиотека есть (MIT); оригинального класса MsSupportResistanceV1 нет. Нельзя приписывать ему прибыль 404 сделок после импорта только библиотеки.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z12 · P1 — Причинный перенос HTF на LTF с временем доступности

**Итог точной сверки:** `ALREADY_PRESENT`. **Есть:** closedCandles, closedEndIndex/bundleAt и структура с pivot.index + right-bars выполняют базовую causal MTF доступность. **Отсутствующая часть:** Не считать базовую HTF→LTF синхронизацию новой деталью; отдельные funding/OI availability gaps уже учтены в Z01.

- **Источники:** R002,R033,R034,R052,R056.
- **Как работает:** 4H индикатор, сформированный при закрытии 4H, доступен 1H/15m только после закрытия/публикации; shift/merge и warmup обязательны.
- **Пересечение с нашим кодом:** В EMBER и SMOKE MTF есть, но детальная parity-инвариантность для всех новостей/структур не доказана.
- **Что потенциально добавить:** Единый as-of resampler со строгим closed-bar timestamp, тестами HTF shift и first-available LTF.
- **Ограничение / доказательность:** Референс: fortunato/mtf.py с HTF shift(1); не делать сдвиг дважды и не отменять необходимый.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z13 · P1 — Декларативные правила Price Action

**Итог точной сверки:** `NEW_GAP`. **Есть:** Есть готовые конкретные сценарии levels/reaction и функции PA, но нет общего правила-DSL. **Отсутствующая часть:** Не найден самостоятельный декларативный движок price-action условий с causal on_bar и одинаковой обработкой bracket.

- **Источники:** R058,R068,R070.
- **Как работает:** Выражение уровня, failed breakout, retest, consolidation и последовательного триггера как проверяемых правил в on_bar-контексте.
- **Пересечение с нашим кодом:** BOS/sweep/retest имеются, но отдельный проверяемый DSL для сравнения реализаций не подтверждён.
- **Что потенциально добавить:** Набор независимых распознавателей с event_time и единой семантикой «образован/подтверждён/исполнен».
- **Ограничение / доказательность:** stolgo даёт библиотеку/примеры, а не доказанный edge; формат bracket нужно тестировать.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z14 · P1 — Состояния compression→breakout→failed return→restart

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В BrainFeatureSnapshot есть COMPRESSION/EXPANSION, в SMOKE есть route/continuation, отдельный guardian state-machine. **Отсутствующая часть:** Не подтверждён единый stateful compression→break→failed-return→restart с типизированными причинами и прогревом.

- **Источники:** R002,R029,R058.
- **Как работает:** Сжатие диапазона по ATR/ширине, выход, неудачный возврат, повторный импульс, reclaim, cooldown. Каждая фаза на известной свече.
- **Пересечение с нашим кодом:** SMOKE умеет продолжение/retest; отдельный накопительный автомат сжатия и рестарта не подтверждён.
- **Что потенциально добавить:** Finite-state detector + журнал переходов и требований volume/HTF.
- **Ограничение / доказательность:** R029 исходный код long-only (несмотря на противоречивый README); не переносить предполагаемые shorts.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z15 · P1 — Независимые детекторы геометрических фигур

**Итог точной сверки:** `NEW_GAP`. **Есть:** Есть swing-pivots/BOS/CHoCH и структуры, но не библиотека графических фигур. **Отсутствующая часть:** Не найдены независимые причинные H&S/double top/flag/triangle с индексом подтверждения.

- **Источники:** R014,R015,R044,R047,R070.
- **Как работает:** Четырёхчасовые фигуры: флаг, треугольник, двойная вершина/дно, голова-плечи; 5m wick/candle sequences; сигнал после фактического подтверждения пивота.
- **Пересечение с нашим кодом:** Есть swings и структуры BOS; полный набор детекторов фигур не подтверждён.
- **Что потенциально добавить:** Отдельные причинные функции с паттерн-id, временем подтверждения, статистикой по каждому.
- **Ограничение / доказательность:** Сохранить как диагностические признаки; авторские результаты основаны на других venue/universe и могли иметь survivorship bias.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z16 · P1 — Непрерывный FVG-channel как альтернатива одиночным зонам

**Итог точной сверки:** `NEW_GAP`. **Есть:** FVG-зоны, активность и качество уже существуют. **Отсутствующая часть:** Не найден отдельный динамический FVG channel, который агрегирует последовательные gaps в границы upper/mid/lower.

- **Источники:** R028.
- **Как работает:** Bull/bear FVG агрегируются в сглаженные верх/низ/mid канала; вход по пересечению границ, а не факту одной незакрытой зоны.
- **Пересечение с нашим кодом:** FVG и POI есть, но агрегированный динамический FVG channel не подтверждён.
- **Что потенциально добавить:** Вычислитель channel upper/lower/mid, упругость/возраст зоны, signal provenance.
- **Ограничение / доказательность:** Контрольный USD-M стресс R028 отрицательный 2024–2026; модуль изучать как feature, не готовую стратегию.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z17 · P1 — Распознавание ложного пробоя и ранний выход

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Уже есть sweep_reclaim, `FAST_FLUSH_DETECTED→RECLAIM/FAILURE→EXIT` guardian. **Отсутствующая часть:** Не обнаружен общий по стратегиям детектор failed-break как отдельное правило ранней invalidation/exit для breakout/PA.

- **Источники:** R020,R044,R058,R061,R062.
- **Как работает:** Свеча пробивает уровень, не удерживает его, возвращается или подтверждается последующей свечой; separately failure-exit и invalidation.
- **Пересечение с нашим кодом:** SMOKE имеет sweep-reclaim, но нет подтверждения полного семейства failed-break/early-exit.
- **Что потенциально добавить:** Сравнить независимые версии failed_break с trigger-on-close/next-open и early invalidation.
- **Ограничение / доказательность:** R020 исходный same-close тест некорректен, нельзя переиспользовать результаты.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z18 · P1 — Переключатель regime и устойчивость режима

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Есть evaluateRegimeGate (location/reversal/continuation), V5 режимы и macro brain. **Отсутствующая часть:** Не доказана устойчивая гистерезисная/минимально-временная модель смены regime со сменой состояния по времени.

- **Источники:** R003,R036,R043,R051,R062.
- **Как работает:** ADX/EMA/volatility, наблюдение persistence 30m/1h, выбор trend/breakout/range-reversion с явным neutral state.
- **Пересечение с нашим кодом:** Режимы есть; нет доказательства точного persistence/route per strategy.
- **Что потенциально добавить:** Протокол состояния режима с минимальной длительностью, гистерезисом, исключением nan/warmup.
- **Ограничение / доказательность:** Не переносить авторские «прибыльные regime switches» без A/B и OOS.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z19 · P1 — SuperTrend, OTT и HMA-коридор как альтернативные признаки

**Итог точной сверки:** `NEW_GAP`. **Есть:** EMA/ATR/RSI и трендовые фильтры есть; отдельные HMA/EWO/SuperTrend/OTT не найдены в сверенном активном ядре. **Отсутствующая часть:** Потенциально отдельные версионированные технические features, не автоматическая замена текущих EMA.

- **Источники:** R006,R007,R031,R032,R036,R071.
- **Как работает:** ATR/SuperTrend direction flip, OTT адаптивная линия, Hull MA corridor, EWO и многоскоростные RSI; отдельные признаки для независимого сравнения.
- **Пересечение с нашим кодом:** EMA/ATR/RSI уже есть; эти формулы/варианты не подтверждены отдельными feature modules.
- **Что потенциально добавить:** Оригинальные функции признаков с версионированными параметрами; не заменять ими существующие EMA по умолчанию.
- **Ограничение / доказательность:** R032 оригинал runtime blocked; R031 стоп −26.5%; R007 98% exposure; это не кандидаты для прямого переноса risk.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z20 · P1 — Funding extremum, z-score и OU half-life

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В схеме BrainFeatureSnapshot поле fundingRate существует. **Отсутствующая часть:** Не найден исторический funding event-series и OU/rolling z-score/half-life features с публикационной задержкой.

- **Источники:** R023,R049,R065; X08.
- **Как работает:** Funding rate как событие 8h, z-score исторической ставки, оценка OU mean reversion/half-life; сигнал отдельно от денежного funding PnL.
- **Пересечение с нашим кодом:** В основном EMBER funding не моделируется; быстрые макросрезы не равны историческому событийному слою.
- **Что потенциально добавить:** Фичи funding_level, lagged_z, OU half-life и cash-flow; valid-only if point-in-time.
- **Ограничение / доказательность:** R023 публичный CSV не содержит рекламируемого XRP; R065 OOS отрицателен; Z-score — не доказательство edge.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z21 · P1 — Четыре режима price×Open Interest

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В BrainFeatureSnapshot есть oiChangePct; reversal brain учитывает его знак в score. **Отсутствующая часть:** Нет отдельного priceΔ×OIΔ классификатора 4 квадрантов с taker confirmation и point-in-time историями.

- **Источники:** R024.
- **Как работает:** Рост/падение цены × рост/падение OI: вход новых позиций либо закрытие старых; taker ratio уточняет подтверждение.
- **Пересечение с нашим кодом:** Есть price direction и объём; полноценный point-in-time OI classification не выявлен.
- **Что потенциально добавить:** Четырёхквадрантный классификатор с lag, taker confirm и regime label.
- **Ограничение / доказательность:** Авторский DD до −97.5% на SUI; использовать как исследовательский признак, не автономный сигнал.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z22 · P1 — Агрессивный поток покупок/продаж (taker buy ratio)

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Binance normalizer сохраняет takerBuyVolume, а BrainFeatureSnapshot — takerImbalance. **Отсутствующая часть:** Не найден причинный rolling taker-pressure 5m/15m со сдвигом времени и независимым trace сигналов.

- **Источники:** R023,R024,R025.
- **Как работает:** Rolling taker_buy_volume / total_volume отличает агрессора от обычного свечного объёма; сигнал при устойчивости нескольких баров.
- **Пересечение с нашим кодом:** Обычный volume_ratio есть; taker-side сделки и лаг публикации не подтверждены.
- **Что потенциально добавить:** Фича taker_pressure, rolling persistence, trade timestamp; compare above candle-only baseline.
- **Ограничение / доказательность:** У R025 большинство авторских рынков имеют отрицательный PF; отдельно от прибыли стратегии.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z23 · P1 — BTC→alt lead–lag событийная задержка

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** BTC и макрорежимы используются как context gate. **Отсутствующая часть:** Не найдено event-study измерения BTC→alt lead-lag, секунды/минуты и прогноз окна задержки без будущих свечей.

- **Источники:** R067.
- **Как работает:** При резком движении BTC в разные режимы проверяется delayed reaction по конкретным альтам на секундном/минутном горизонте.
- **Пересечение с нашим кодом:** BTC macro gate уже есть; синхронизированный event-trigger latency estimator не подтверждён.
- **Что потенциально добавить:** Event-study с задержкой, лаг-распределением, историческими одновременными feed snapshots.
- **Ограничение / доказательность:** Kraken Futures оригинал и авторская гипотеза; перенос latency на Binance не гарантирован.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z24 · P1 — Cross-sectional momentum и динамический ranking

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Есть RollingSymbolStrength, UniverseSelector и sector tags — они ранжируют символы по историческим сделкам. **Отсутствующая часть:** Нет отдельно зафиксированного point-in-time rank по цене/volatility/14–90d и динамического basket rebalance, как в CTA.

- **Источники:** R011,R040,R053.
- **Как работает:** Монеты ранжируют по доходности за 14/21/90d, ATR/волатильности, volume/tradability; портфель периодически ротируется.
- **Пересечение с нашим кодом:** Scanner и фиксированный universe есть, однако полноценного point-in-time rank/basket/turnover учета не выявлено.
- **Что потенциально добавить:** Исторически воспроизводимый universe, rank snapshots, rebalance/rejected/turnover/capacity ledger.
- **Ограничение / доказательность:** Нельзя выбирать top winners по полному периоду; R040 spot и концентрация ZEC, R053 timestamp flaw.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z25 · P1 — Relative-value / spread z-score двух активов

**Итог точной сверки:** `NEW_GAP`. **Есть:** Простого portfolio и BTC context недостаточно для двухногой статистической сделки. **Отсутствующая часть:** Не найден pair spread/hedge-ratio/cointegration z-score и одновременный fill обеих ног.

- **Источники:** R046,R076.
- **Как работает:** Для двух контрактов рассчитывается spread, hedge ratio, rolling z-score, вход в отклонение и закрытие при нормализации.
- **Пересечение с нашим кодом:** Парной статистической торговой модели как самостоятельного модуля не подтверждено.
- **Что потенциально добавить:** Pair signal и portfolio legs отдельно; cointegration gate, rebalance, IC/execution costs.
- **Ограничение / доказательность:** Не подменять Kraken Spot-stat-arb R076 несуществующей авторами futures-реализацией.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z26 · P1 — Относительное отклонение от SMA и медленный decay

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** RSI, EMA и pullback у нас есть. **Отсутствующая часть:** Не подтверждены независимые absolute SMA-dislocation, slow-decay curve 48–96h и лимиты исполнения для такого удержания.

- **Источники:** R041,R039.
- **Как работает:** RSI<30 + сильное отклонение от длительной SMA, удержание 48–96h, равномерные небольшие позиции; отдельно от cross-sectional rank.
- **Пересечение с нашим кодом:** RSI и pullback есть, но dislocation/decay function + liquidity caps не подтверждены.
- **Что потенциально добавить:** Детектор dislocation и decay curve; capacity stress, долгий time-stop, stop risk.
- **Ограничение / доказательность:** Оригинальный OversoldReversion Spot и stop −99%: нельзя переносить его risk/экономику.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z27 · P1 — Качественные признаки ML и контракт модели

**Итог точной сверки:** `NEW_GAP`. **Есть:** Обычные feature builders и WFO есть, но ML-inference не представлен как действующий штатный модуль. **Отсутствующая часть:** Не найдены модельный artifact lifecycle, feature-schema SHA, train cutoff и live/paper inference parity.

- **Источники:** R045,R064.
- **Как работает:** Feature registry и версии ML weights, history-only train/validation, inference thresholds, model drift; offline и online должны давать одинаковые сигналы.
- **Пересечение с нашим кодом:** EMBER есть feature builder и WFO, но версии внешних ML-моделей/артефактов в core не подтверждены.
- **Что потенциально добавить:** ModelCard+feature SHA + training cutoff + causal inference adapter; только research.
- **Ограничение / доказательность:** R045 model training/model artifacts не восстановлены; R064 dry-run −$93.98/139 trades. Не использовать прогноз как прибыльный.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z28 · P1 — Deep Fibonacci retracement и раздельные входы

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** SMOKE умеет структурные зоны и планы с несколькими entryPrices/LADDER. **Отсутствующая часть:** Не обнаружен самостоятельный GEM-детектор импульсной ноги и Fib 0.79 E1/E2 с ATR-gap и доказанной семантикой входов.

- **Источники:** R060.
- **Как работает:** После импульса определяются leg endpoints, 79% retracement, ATR-стоп за экстремумом, два уровня entry, SMC confluence.
- **Пересечение с нашим кодом:** У EMBER/SMOKE structural zone есть; специализированного GEM dual-entry 79% нет.
- **Что потенциально добавить:** Изолированный fib-leg detector + E1/E2 geometry + independent state trace.
- **Ограничение / доказательность:** Источник BloFin; SMC часть дублирует существующие механизмы, риск и плечо автора не заимствовать.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z29 · P2 — A/B ablation элементов без подмены входов

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** У EMBER/SMOKE есть WFO, parameter_grid и отдельные профили. **Отсутствующая часть:** Не найдены парные A/B matched-entry отчёты по одной отключённой feature с сохранением исходного signal timeline.

- **Источники:** R034,R035,R036,R043; X09.
- **Как работает:** Один сигнал и один портфель, включение/выключение единственного фильтра без изменения данных и других параметров.
- **Пересечение с нашим кодом:** WFO/диагностика есть; воспроизводимого single-component matched-trade attribution для всех механизмов не доказано.
- **Что потенциально добавить:** Framework paired-run с дельтой trades/fees/PnL/DD, исходным signal timeline и строгим OOS.
- **Ограничение / доказательность:** MsFilter и NoMs — одна семья, не два независимых прибыльных кандидата.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z30 · P2 — Оценка IC, deflated Sharpe и множественных попыток

**Итог точной сверки:** `NEW_GAP`. **Есть:** PF/Sharpe/DD и WFO-пороговые оценки есть. **Отсутствующая часть:** В просмотренном ядре нет IC, deflated Sharpe и поправок на количество протестированных комбинаций.

- **Источники:** R039,R045,R064,R076; X07.
- **Как работает:** Информационный коэффициент, null/baselines, permutation или bootstrap со структурой времени, deflated Sharpe и поправка на число испытанных вариантов.
- **Пересечение с нашим кодом:** EMBER считает PF/DD/WFO, но IC/multiple-hypothesis correction не выявлены.
- **Что потенциально добавить:** Статистический отчёт: periods, tried variants, confidence intervals, family count, OOS untouched.
- **Ограничение / доказательность:** R076 Spot среднее преимущество после расходов отрицательное; применима методика, не заявленный рынок.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z31 · P2 — Атрибуция результата по активам, режимам и сигналам

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** TradeQuality и StructureLearning строят breakdown по side/session/regime, SMOKE backtest выделяет long/short. **Отсутствующая часть:** Не найден стандартный per-signal/trade top3-concentration и leave-one-symbol-out на неизменяемом universe.

- **Источники:** R022,R039,R040,R047,R048.
- **Как работает:** Каждому сигналу/паттерну назначить ID; отдельно PnL по символам, долю топ-3 сделок, концентрацию, leave-one-asset-out, trade tags.
- **Пересечение с нашим кодом:** Отчёты по сделкам/quality gate есть, но устойчивый leave-one-out/концентрация не подтверждены.
- **Что потенциально добавить:** Attribution dashboard: by module/signal/symbol/regime, 3-trade concentration и per-family portfolio effects.
- **Ограничение / доказательность:** Нельзя принимать R034 с 96.2% прибыли от 3 сделок за устойчивый механизм.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z32 · P2 — Диагностика lookahead/warmup/двойного shift

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В EMBER есть 7 no-leakage tests, SMOKE закрывает свечи и учитывает подтверждение pivot справа. **Отсутствующая часть:** Не найдена общая автоматическая трасса `feature_available_at` для внешних стратегий, centred gradient, отрицательных shift и любого warmup.

- **Источники:** R002,R027,R052,R054,R055,R056,R061.
- **Как работает:** Centered gradient, отрицательный shift, pivot с правыми барами, EMA19200 при startup500, same-close fill — все требуют момента доступности.
- **Пересечение с нашим кодом:** EMBER имеет 7 leakage tests, но проверка произвольного внешнего pipeline требует отдельного контрактного аудита.
- **Что потенциально добавить:** Data availability tracer по каждому индикатору и automatic reject на NaN/insufficient warmup.
- **Ограничение / доказательность:** Не «исправлять» и одновременно приписывать результат оригиналу: исправленный вариант тестировать отдельным ID.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z33 · P2 — Сверка исходного портфеля и независимого контрольного теста

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В истории EMBER уже есть A240 авторский shared-wallet тест и ограниченные контролируемые USD-M прогоны. **Отсутствующая часть:** Нет универсального побарного оригинал-vs-наш engine differential harness с полной сверкой config/account/portfolio/fill.

- **Источники:** R001,R009,R011,R026,R036,R075.
- **Как работает:** Авторский общий счёт, пары, плечо, max positions, repeat entries, wallet/stake и timeframe должны быть восстановлены отдельно от 3-парного стандартизированного экрана.
- **Пересечение с нашим кодом:** Бэктест есть, но старые A233/A240 ошибочно сравнивали раздельные и общий кошелёк.
- **Что потенциально добавить:** Frozen author parity ledger, canonical hashes, per-trade diffs, separate controlled 3-pair benchmark.
- **Ограничение / доказательность:** Никакого verdict у ETH-only R009 за 10-coin OKX; R075 mirrored shorts не равны авторскому short edge.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z34 · P2 — Лимит ликвидности и проскальзывание на входе/выходе

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** В SMOKE и EMBER уже учитываются фиксированные комиссии/скольжение, часть quote/freshness и score объёмов. **Отсутствующая часть:** Не найдены participation cap как доля исторического объёма, market-impact curve и L2 maker partial-fill.

- **Источники:** R039,R040,R041,R047,R066; X02.
- **Как работает:** Лимит объёма исполнения как доля quote volume свечи, spread sensitivity, очередь для maker и forced exit; отдельные оценки цены разных размеров.
- **Пересечение с нашим кодом:** Fee/slippage модель есть, но полные participation caps и market impact не подтверждены.
- **Что потенциально добавить:** Fill envelope при capacity scenarios и стресс на ZEC/малых альтах; показать то, чего свечи не позволяют доказать.
- **Ограничение / доказательность:** Не переносить результат, если большая часть прибыли только в малоликвидном активе.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z35 · P2 — Сезонность/сессии и режимная ошибка селекции

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Session bucket уже реализован в StructureLearning, WFO окна есть. **Отсутствующая часть:** Не найден отдельный предварительно зарегистрированный независимый session/seasonality event-study без подбора лучшего окна на том же периоде.

- **Источники:** R016,R037,R059.
- **Как работает:** Анализ времени суток, сезона и weekly/daily resets, без отбора лучшего окна на всей истории.
- **Пересечение с нашим кодом:** Периодические WFO есть; фиксированная методика session ablation не выделена.
- **Что потенциально добавить:** Проверка заранее заданных окон на независимых режимах и stable sessions.
- **Ограничение / доказательность:** BIGBEAR авторский session-filter мог подбираться на той же истории — нужна поправка на поиск.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z36 · P2 — Анализ повторных входов и постоянной экспозиции

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Есть cooldown в SMOKE backtest и max open positions/capital в portfolio. **Отсутствующая часть:** Не найден агрегированный отчёт permanent exposure, bar-to-bar repeated re-entry и занятости каждой стратегии/слота.

- **Источники:** R007,R029,R053.
- **Как работает:** Счётчик re-entry, free capital, time-in-market, sequential open на следующем баре, hidden overlap.
- **Пересечение с нашим кодом:** В SMOKE есть cooldown, EMBER ограничивает max positions; отдельного exposure audit по каждому оригиналу не подтверждено.
- **Что потенциально добавить:** Exposure timeline + repeat-entry attribution, alerts when slots permanently occupied.
- **Ограничение / доказательность:** R007 98.24% времени 4/4 слотов занято: частота 4.76/day не доказывает независимость 4.76 сетапов.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z37 · P2 — Ступенчатый риск и DCA-risk budget как объект исследования

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** Есть риск-профили, динамическая ставка, margin cap, kill switch. **Отсутствующая часть:** Нет full event-time risk staircase с DCA, liquidations и stop exposure после каждого добора — не заимствовать без моделирования риска.

- **Источники:** R004,R030,R038,R064,R074.
- **Как работает:** Risk staircase по состоянию капитала, per-trade volatility scaling, total stop exposure с доборами, DD-scaler.
- **Пересечение с нашим кодом:** Risk_engine имеет общий размер риска, но лестница/квадратичная DD модель в core не подтверждена.
- **Что потенциально добавить:** Отдельная симуляция риска без изменения торговых сигналов; единый maximum loss и margin.
- **Ограничение / доказательность:** При source stop −100% или неизвестной марже не использовать увеличение размера в PAPER.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.

### Z38 · P2 — Отдельная инфраструктура для аудита альтернативных исполнителей

**Итог точной сверки:** `PARTIAL_GAP`. **Есть:** У проекта есть разные executors/backtesters и CI тесты. **Отсутствующая часть:** Не найден автоматический cross-runner, сравнивающий исходный Freqtrade/Pine/custom Python с EMBER на одинаковых data/hash и fills.

- **Источники:** R018,R026,R032,R057,R073; X06,X09,X12,X18.
- **Как работает:** Сравнить Freqtrade/Pine/пользовательский Python по одним входным данным, отделить runtime error, несовместимость, неисполненные заявки и отрицательный PnL.
- **Пересечение с нашим кодом:** Собственные тесты и CI есть, но сравнительная дифференциальная модель неодинаковых исполнителей не собрана.
- **Что потенциально добавить:** Replay-adapter boundary; измерять source/runtime/market/fill discrepancy по каждому test id.
- **Ограничение / доказательность:** Закрытые исходники R073/R074 и неисправный R032 не считать экономическим FAIL.
- **Статус:** первоначально `SPARE_UNVERIFIED`; текущая оценка приведена в карточке и общей таблице.


---

## Полнота охвата R001–R076

Отсутствие отдельного уникального элемента в источнике — не экономический FAIL стратегии. Некоторые карточки ведут к нескольким компонентам. Перечень ниже не исключает кандидата из исходного реестра.

| Кандидат | Источник | Связанные «запчасти» или причина отсутствия новой | 
|---|---|---|
| R030 VolatilitySystem | `freqtrade/freqtrade-strategies` | Z02, Z37 |
| R004 Risk_Stair_S5 | `linhuang1212-coder/crypto-quant-trading` | Z02, Z37 |
| R011 Octopus multi-perp CTA | `OctopusTakopi/crypto-trend-following` | Z02, Z07, Z24, Z33 |
| R029 FailureToReturnStrategy | `hrodrig/freqhub-strategies` | Z14, Z36 |
| R033 MsSupportResistanceV1 | `fortunato/pymarket-structure` | Z11, Z12 |
| R009 SingleB_FixedRR | `liu57liu456/backtest-autopsy` | Z33 |
| R008 TSMOM | `yongzhe2160cs/trading-engine` | Z08 |
| R002 DualTrendCompressionRestartShortV1 | `wangc-joker/ft_userdata` | Z12, Z14, Z32 |
| R022 Acekiller MTF scanner | `Acekiller88/crypto-signal-scanner` | Z10, Z31 |
| R023 XRP funding mean reversion | `Gotodataru/binance-futures-backtest` | Z01, Z20, Z22 |
| R034 MsFilterV6 | `fortunato/pymarket-structure` | Z11, Z12, Z29 |
| R035 MsFilterV6NoMs | `fortunato/pymarket-structure` | Z11, Z29 |
| R016 BIGBEAR | `genia503/mean-reversion-backtester` | Z09, Z35 |
| R017 BIGBULL | `genia503/mean-reversion-backtester` | Z09 |
| R039 nateemma gbb/reversion | `nateemma/strategies` | Z03, Z26, Z30, Z31, Z34 |
| R045 LightGBM Jansen | `djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen` | Z04, Z27, Z30 |
| R042 RSI/ADX scalper | `jiangkaili/binance-trader-bot` | Новая самостоятельная функция пока не доказана; RSI/ADX уже есть; самодельный fee gate не переносить без исправления |
| R046 Pair Trading NEDL | `djienne/pair_trading_NEDL` | Z03, Z05, Z25 |
| R075 V5 Crypto Scalper — perp Momentum theoretical | `knacker65/v5-crypto-scalper` | Z01, Z02, Z33 |
| R057 gmchun breakout | `gmchun83/binancefuturebot` | Z04, Z06, Z38 |
| R014 momentum_wick | `TheoBrigitte/freqtrade` | Z15 |
| R015 momentum_rsi | `TheoBrigitte/freqtrade` | Z15 |
| R019 TrendRider | `darkvolg/Trading` | Z08 |
| R031 FSupertrendStrategy | `freqtrade/freqtrade-strategies` | Z19 |
| R032 FOttStrategy | `freqtrade/freqtrade-strategies` | Z19, Z38 |
| R043 Bollinger Reverter / Donchian | `Superior-Trade/superior-skills` | Z18, Z29 |
| R044 ETH Momentum 2h / DumpReversal | `grinay/geektrade-strategies` | Z15, Z17 |
| R051 AdaptiveRegime / AdaptiveRegimeLong | `Kureshi25/cryptobot` | Z18 |
| R058 stolgo PA variants | `stockalgo/stolgo` | Z13, Z14, Z17 |
| R060 Zenith / GEM | `traderhydr/krpticz` | Z06, Z07, Z28 |
| R066 Orderbook imbalance | `tsuithomas/crypto_research_order_book_imbalance` | Z03, Z34 |
| R067 Lead-lag trader | `mamipour/lead-lag-trader` | Z05, Z23 |
| R068 FMZ SR breakout | `fmzquant/strategies` | Z13 |
| R048 NostalgiaForInfinity X8 | `iterativv/NostalgiaForInfinity` | Z31 |
| R020 Revelio sweep→BOS V1 | `hroussel18/Revelio_Improved_Strategy` | Z09, Z17 |
| R010 SOL Trend Pullback V9 | `kboranyldz/sol-trading-research` | Z01, Z02, Z06 |
| R024 OI momentum/divergence | `Gotodataru/binance-futures-backtest` | Z01, Z21, Z22 |
| R025 Taker momentum | `Gotodataru/binance-futures-backtest` | Z01, Z22 |
| R012 FAdxSmaStrategy | `freqtrade/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; ADX/SMA пересечения уже есть; возможен лишь сравнимый эталонный тест |
| R013 FReinforcedStrategy | `freqtrade/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; основной механизм перекрывается имеющимися, источник/реализацию сверять отдельно |
| R026 Winner15m | `win-boom/BTCquant` | Z33, Z38 |
| R001 Double MA | `MirrorNew/2026DoubleMaFuturesStrategy` | Z33 |
| R003 BearRegimeShortV1 | `IvPalmer/Master-Trader` | Z18 |
| R005 TrendFollowing | `krantikaridev/freqtrade` | Новая самостоятельная функция пока не доказана; обычный тренд/EMA и protections уже представлены, новых компонентов без полного аудита не доказано |
| R006 NASOSv7LongShort | `remiotore/ccxt-freqtrade` | Z19 |
| R028 FVGChannel | `jaredrsommer/freqtradestrategies` | Z16 |
| R027 MTF_Hybrid | `win-boom/BTCquant` | Z32 |
| R007 dip_catcher | `viktors1982/trading` | Z19, Z36 |
| R018 AggressiveSupportResistanceScalper | `Meszqt/freqtrade-test` | Z09, Z10, Z38 |
| R021 Pranay FVG/OB | `pranay123-stack/Algorithmic-Trading-Projects` | Z09 |
| R036 HERMES SuperTrend | `chrysek70/hermes-trading` | Z04, Z18, Z19, Z29, Z33 |
| R037 APEX no-pyramid | `EstebanSP23/crypto_systematic_research` | Z06, Z35 |
| R038 Quattro Donchian | `EstebanSP23/crypto_systematic_research` | Z02, Z06, Z37 |
| R040 MomentumRegimeBasket15mFast | `nateemma/strategies` | Z07, Z24, Z31, Z34 |
| R041 OversoldReversion | `nateemma/strategies` | Z26, Z34 |
| R047 Chart-pattern backtester | `juriok/chart-pattern-backtester` | Z15, Z31, Z34 |
| R049 Funding Carry OU | `aayanvatsa04/btc-perpetual-funding-arbitrage` | Z05, Z20 |
| R050 TrendFutures | `Kureshi25/cryptobot` | Z02, Z08 |
| R052 Den­niskid research / production | `denniskid2520/btcusdt-research-archive` | Z01, Z04, Z12, Z32 |
| R053 Dynamic gainers | `kiattisakph/crypto-scalp-bot` | Z03, Z08, Z10, Z24, Z36 |
| R055 DivergenceStrategy | `jamniol/freqtrade-setup` | Z32 |
| R056 MandelbrotFibonacciStrategy | `hrodrig/freqhub-strategies` | Z12, Z32 |
| R059 SC4RECOIN breakout | `SC4RECOIN/simple-crypto-breakout-strategy` | Z10, Z35 |
| R061 Milton BTC breakout | `MiltonTulli/trading-bot` | Z10, Z17, Z32 |
| R062 BinHV45 v3 / v4 | `zevrichards/freqtrade-strategies` | Z17, Z18 |
| R071 DS_BNC_EV1E_5m | `Danson77/Freqtrade_AIO_UI` | Z19 |
| R054 RsiquiV5 | `TheoBrigitte/freqtrade` | Z32 |
| R063 GeneticEngineV1 | `ceyhanmolla` | Новая самостоятельная функция пока не доказана; исходный код и SHA не восстановлены — нечего импортировать |
| R064 Ultimate Alpha v16 | `OfficialGIGA/freqtrade-ml-strategy` | Z27, Z30, Z37 |
| R065 Funding zscore | `Adeline117/Strategy-project` | Z20 |
| R069 FMZ retest 482873 | `https://www.fmz.com/strategy/482873` | Новая самостоятельная функция пока не доказана; venue/timeframe mismatch, до исправления нет технически подтверждённого компонента |
| R070 2Candle | `jaredrsommer/freqtradestrategies` | Z09, Z13, Z15 |
| R072 NFI5MOHO_WIP | `davidzr/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; старая API/семейство NFI; независимый модуль не выделен |
| R073 AKzar walk-forward | `AKzar1el/walk-forward-crypto` | Z38 |
| R074 DevAntsa models | `DevAntsa/DevAntsa-Algo-Public` | Z07, Z37 |
| R076 Crypto Stat Arb — spot mean reversion gross edge | `billybraith17/crypto-stat-arb` | Z25, Z30 |

## Дополнительные 18 источников — что сохранять

| ID | Источник | Роль |
|---|---|---|
| X01 | xujaan/futurabot | OBI/CVD/VPIN и поток, проверить конкретные реализации (Z03,Z21,Z22) |
| X02 | DylanSiegel/GO-Microstructures | Hawkes/aggTrades/микроструктура и event-time (Z01,Z03,Z34) |
| X03 | HodlHook/momentum-breakout-postmortem | Отрицательный OOS как контроль методики, не компонент edge |
| X04 | MG-Trading-Terminal/trading-strategy | Позиционирование/OI, нет полного исполнителя |
| X05 | Mykola-Quant/retail-crypto-alpha | Отрицательный futures OOS, архив evidence |
| X06 | PVinh-Quant/Kairos-v2 | Research инфраструктура (Z38) |
| X07 | SebastianBoehler/MarketTensor | ML baseline и слабое преимущество (Z30) |
| X08 | Superjojo74/nautilus-perp-funding | Funding settlement layer, НЕ сигнал (Z01,Z05,Z20) |
| X09 | analogdada/perplab | Тестовый движок/parity/ablation (Z29,Z38) |
| X10 | behlulgoker/price-action-engine | Spot API; только абстрактные PA-правила, без копирования venue |
| X11 | bockuden/crypto-cointegration-research | отрицательная после расходов экономика pair/basis; evidence (Z25) |
| X12 | chiragbitoni/binance-paper-trading-lab | PAPER инфраструктура, не фьючерсный edge (Z38) |
| X13 | francisx1999/crypto-trading-bot-postmortem | отрицательный Kraken/Coinbase OOS, не Binance verdict |
| X14 | joseph280/crypto-backtest-lab | синтетический sanity, не рыночный результат |
| X15 | spagnola-analytics/intraday-strategies | другой рынок, не импортировать сигналы |
| X16 | ycchew/CQ_breakout_strategy | equity/Yahoo, не Binance USD-M |
| X17 | younghwan91/quantbox-engine | недоступный оригинал, SOURCE_BLOCK |
| X18 | zabor-crypto/zaBor | инфраструктура риск-контроля (Z07,Z08) |

## Прямое вето пользователя

`AbdullaE100/perp-quant-lab`, `OctopusTakopi/funding-rate-alpha`, `agarwalchirag535-lab/smallcap-pump-reversal` — `USER_VETO / DO_NOT_REQUEUE`. Важно: Octopus CTA R011 — **другой** репозиторий, не под запретом.

## Проверенные исходные файлы (примеры, SHA относятся к просмотренным файлам, не доказательству работы всего проекта)

| Зачем | Репозиторий/файл | Git blob SHA |
|---|---|---|
| Z11/Z12 | [fortunato/pymarket-structure/src/market_structure/freqtrade.py](https://github.com/fortunato/pymarket-structure/blob/main/src/market_structure/freqtrade.py) | `556f95bdff71aa78c99ab35da5962684600e6984` |
| Z12 | [fortunato/pymarket-structure/src/market_structure/mtf.py](https://github.com/fortunato/pymarket-structure/blob/main/src/market_structure/mtf.py) | `b628a8edf5530bafaa582d81c1b7a2f64bece175` |
| Z04/Z19 | [chrysek70/hermes-trading/hermes_trading/signals.py](https://github.com/chrysek70/hermes-trading/blob/main/hermes_trading/signals.py) | `ac6794eda99cc83e50a097b19e7bb30f9e9bdc89` |
| Z13 | [stockalgo/stolgo/examples/pa/failed_break.py](https://github.com/stockalgo/stolgo/blob/main/examples/pa/failed_break.py) | `2754b3a11465029be55783bb4510ab32b12401db` |
| Z21 | [Gotodataru/binance-futures-backtest/strategy_3_oi_divergence/signals.py](https://github.com/Gotodataru/binance-futures-backtest/blob/main/strategy_3_oi_divergence/signals.py) | `be177d2b24a740bc3ac46115326780c48582ec3e` |
| Z20 | [Gotodataru/binance-futures-backtest/strategy_1_funding_mr/signals.py](https://github.com/Gotodataru/binance-futures-backtest/blob/main/strategy_1_funding_mr/signals.py) | `7528f737eddd459b8505972c01fef60d263715e1` |
| Z20 | [aayanvatsa04/btc-perpetual-funding-arbitrage/funding_arb/models/ou_model.py](https://github.com/aayanvatsa04/btc-perpetual-funding-arbitrage/blob/main/funding_arb/models/ou_model.py) | `d4aaeb1f11d20c9a0e7214e501d022cafa851362` |
| Z06/Z34 | [EstebanSP23/crypto_systematic_research/2_strategies/01_quattro_donchian/backtest_quattro_v2_costs.py](https://github.com/EstebanSP23/crypto_systematic_research/blob/main/2_strategies/01_quattro_donchian/backtest_quattro_v2_costs.py) | `638a29dfac2430809b50154c7b046d75f402d12a` |
| Z27 | [djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen/freqtrade_live/user_data/strategies/LightGBMStrategy.py](https://github.com/djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen/blob/main/freqtrade_live/user_data/strategies/LightGBMStrategy.py) | `8c4c66f14f0001f9ad959d149b4e7571b869a02e` |
| Z28 | [traderhydr/krpticz/gem_strategy.py](https://github.com/traderhydr/krpticz/blob/main/gem_strategy.py) | `12d5b0f9309aaf9f3697236610b219c2ef969642` |
| Z07/Z28 | [traderhydr/krpticz/strategy.py](https://github.com/traderhydr/krpticz/blob/main/strategy.py) | `84aa0da94f9d79acb53a0ad574b5102a0ff3ca24` |
| Z09 | [jaredrsommer/freqtradestrategies/2Candle.py](https://github.com/jaredrsommer/freqtradestrategies/blob/main/2Candle.py) | `10f0259053eb5fbd5dd4167006fd22a68c8db223` |
| Z17 | [zevrichards/freqtrade-strategies/BinHV45_Regime_5m_v4.py](https://github.com/zevrichards/freqtrade-strategies/blob/main/BinHV45_Regime_5m_v4.py) | `f133f37902fc19343ec3cff5d9108d825413b002` |
| Z32 | [hrodrig/freqhub-strategies/strategies/FreqHub.Strategy.MandelbrotFibonacci/MandelbrotFibonacciStrategy.py](https://github.com/hrodrig/freqhub-strategies/blob/main/strategies/FreqHub.Strategy.MandelbrotFibonacci/MandelbrotFibonacciStrategy.py) | `ea54ee26dac523fa6ce0e173b75453a6ad5087fc` |
| Z27 | [OfficialGIGA/freqtrade-ml-strategy/README.md](https://github.com/OfficialGIGA/freqtrade-ml-strategy/blob/main/README.md) | `79471eb459b83a5b4811acf990e722617887a497` |

## С чем сверялась текущая реализация EMBER/SMOKE

- [EMBER core/features.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/features.py) — `a7323ff1ce25e3c6def59a8b8d5bf7150681f5cb`.
- [EMBER core/context_builder.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/context_builder.py) — `e075d95b54c505d6dcf30def5967899a2cd3e0f8`.
- [EMBER strategy/risk_engine.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/risk_engine.py) — `b4972edff2807e391ecaf5c62705dbe2c72015cb`.
- [EMBER strategy/exit_simulator.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/exit_simulator.py) — `23c450858b9c938b9b41bd56b58434f381045490`.
- [EMBER simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) — `a0f689a14301c8cb4b7381801303191845cd9f1e`.
- [EMBER simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) — `7c3c346e366e8ca4f0367f2ec7ffe9bf9b6c619f`.
- [SMOKE README](https://github.com/SanChi117/smoke-trading-terminal/blob/main/README.md) — `reviewed 2026-11-01`.

## Правило возможного переноса, только после отдельного разрешения

1. Проверить, действительно ли функция отсутствует, указав сравниваемые функции/версии/поведение (не только совпадение терминов).
2. Проверить лицензию внешнего источника; GPLv3, MIT и отсутствие лицензии не эквивалентны. Не копировать код без подходящих прав.
3. Отделить исходный алгоритм от его авторского бэктестера, торгового счёта и предположений об исполнении; не наследовать небезопасные SL/плечи.
4. Составить contract-in/out, causal timestamp, unit/property tests и независимые данные. Никакой silent repair под видом оригинала.
5. Добавлять в отдельный выключенный исследовательский модуль; сравнивать baseline с/без компонента только на заранее закреплённой выборке и нетронутом holdout.
6. **Никаких действий сейчас:** этот файл не запускает исследования, не меняет стратегию, код, ветки A-серии, PAPER-планировщики, Binance или live.

## Не путать статусы

- `SPARE_UNVERIFIED`: потенциально новая функция, без импортной/экономической проверки.
- `ALREADY_PRESENT`: после точной code-parity проверки выяснилось, что функция уже реализована.
- `SOURCE_BLOCKED`: не найден оригинал, лицензия либо данные — НЕ отрицательная экономика.
- `NO_ECONOMIC_CLAIM`: ни один модуль здесь не считается источником доказанной прибыли.
