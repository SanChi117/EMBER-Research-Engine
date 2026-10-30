# PROJECT RESET — обзор альтернатив, исходных данных и выбор проверяемых гипотез

Дата: 2026-10-30. Источники проверены по издательским/официальным страницам, технические API по документации Binance/Bybit. **Это исследовательский shortlist, не торговые сигналы, не подтверждённая доходность, не научный систематический review всех публикаций.**

## 1. Исходные выводы, которые нельзя забывать

- Не переносить доказательную силу из **OHLCV паттернов** (zone/CHoCH/BOS/FVG) на будущий поток OI/funding/liquidations. Это отдельные данные, гипотезы и тесты. C117 отверг прибыльность **конкретного старого** правила даже в сравнении с random clock; не доказал ложность всех контекстных ценовых признаков.
- Funding/basis и microstructure — не magic signals. Теоретическая арбитражная конструкция может проигрывать после costs, basis risk, funding schedule, inventory margin, position limits, futures liquidation, borrow costs, exchange outages.
- Источник с честной исторической отметкой `available_at` до входа и целевым first-passage без будущих пивотов — обязательнее красоты графика.
- Простые benchmark стратегий = no-trade, coin/side-matched random clock, unconditional direction, time-series trend/momentum, cost-only, historical funding carry after costs. Стратегия не может «победить» просто потому, что контроль без комиссий или имеет в два раза больше ордеров. Сравнивать одинаково рискованный капитал и per-time notional exposures.
- Обязательный поправочный фактор за много испытанных гипотез: count previous failed trials and report all, freeze hypotheses before unobserved OOS, holdout per venue/market regime, avoid posthoc symbol filtering. Academic reference: Bailey et al. (2014, 2017), `https://scholarworks.wmich.edu/math_pubs/40/`, `https://scholarworks.wmich.edu/math_pubs/42/`.

## 2. Внешние материалы: что они действительно поддерживают

**Опора 1 — perpetual futures: spread/basis/funding вместо фигур**
- `Cao, Zhai, Luo (Journal of Futures Markets, accepted 2024)`: 134 predictors, 48 statistically significant sorting returns; basis & price-volume common factors. University of Edinburgh `https://www.research.ed.ac.uk/en/publications/anatomy-of-cryptocurrency-perpetual-futures-returns/`. Следующая обновлённая работа авторов 2026 рассматривает 170 предикторов, 63 значимых по их модели, `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6795783`. **Значимость в статье ≠ воспроизводимая net прибыль наших пар и комиссий**.
- `He, Manela, Ross, von Wachter, Fundamentals of Perpetual Futures (rev. 2025)`: theoretical pricing/spot-vs-perp spread, bounds with costs and implied arbitrage `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4301150`.
- `Neubert et al., 2026 systematic review`: synthesizes 22 studies, highlights mature pricing/funding theory and severe leverage/liquidation/basis risks `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6639558`.
- `The Two-Tiered Structure of Cryptocurrency Funding Rate Markets (2026)`: 35.7m minutes, 26 venues; reported spreads after costs often evaporate (only 40% of top opportunities profitable once costs/spread reversal accounted by their design) `https://www.mdpi.com/2227-7390/14/2/346`.

**Опора 2 — market microstructure / flow**
- `Cont, Kukanov, Stoikov (2014, Journal of Financial Econometrics)`: order-flow imbalance and best bid/ask depth linked to short-term price impact in **US equities**, *not proof of profitable crypto implementation*. `https://academic.oup.com/jfec/article-abstract/12/1/47/816163`.
- `Price discovery in bitcoin spot and futures markets (Journal of International Money and Finance, Dec. 2025)`: lead-lag and informed trading affected by async/sparse transactions, implies timestamp and cross-venue alignment crucial `https://www.sciencedirect.com/science/article/pii/S0261560625001500`.
- `A Shared Template Without Shared Feedback: Funding Rates in Cryptocurrency Perpetual Futures (2026)` models caps, deadband, funding-delay, capital constraints: do not assume funding observed now is the realized transfer later `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6185958`.

**Опора 3 — credible backtesting**
- `Automated Strategy Discovery in Crypto Perpetuals via Dynamic Factor Ensembles and Auditable Evaluation (2026)` stresses next-bar T+1, fees/slippage/funding, WFO/cost-stress and auditable artifacts; working paper not proof of transferable gains `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6071928`.
- BTC spot/futures microstructure study and Binance docs give technology constraints. None justifies A+ rating before testing.

## 3. Реальные источники и ограничения (не выдумывать OI историю!)

| Поле | Источник | Что документально доступно | Нюанс |
|---|---|---|---|
| Original spot/perp OHLCV (closed 1m, price, traded qty) | `https://github.com/binance/binance-public-data`, `https://data.binance.vision/` | daily/monthly original ZIP + `.CHECKSUM` (счётчик C116/C117 подтверждает USD-M native1m history) | archives могут исправляться; метки времени spot после 2025 в микросекундах, USD-M в мс; не путать market types. Native3m/5m independent original mismatch исторически зафиксирован в EMBER C114/C115. |
| Historical perp aggTrades (taker buy/sell signed proxy) | Binance Vision futures aggTrades daily/monthly по публичной документации, `https://github.com/binance/binance-public-data` | raw aggTrades возможно извлечь как event flow и построить trade delta, если отдельный source QA PASS | Aggregation ≠ level2 order book; нельзя называть 1m taker-buy-volume полным CVD или «реальными ликвидациями». |
| Funding realized history | Binance `GET /fapi/v1/fundingRate` `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History`; Bybit `/v5/market/funding/history` `https://bybit-exchange.github.io/docs/v5/market/history-fund-rate` | history with settlement timestamps, paginated | Separate **projected/current** funding and **settled** funding; do not leak future realized rate into earlier entry. Actual funding charged at settlement. |
| Open Interest historical Binance | `GET /futures/data/openInterestHist` official `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics` | endpoint **only latest ~1 month** (docs explicit) | 2025 OI backtest through this endpoint **impossible**; don't fabricate. |
| Open Interest historical Bybit | `/v5/market/open-interest` `https://bybit-exchange.github.io/docs/v5/market/open-interest` | interval 5min→1d, cursor, docs mention ability to query back to *symbol launch*, possible delays | Need **independent actual earliest/symbol/day retrieval test** before claiming 2025 coverage; different venues' OI definition/units differ. |
| Liquidation snapshot | Binance websocket `{symbol}@forceOrder`, `!forceOrder@arr` `https://developers.binance.info/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Mini-Tickers-Stream` | realtime events | **Only latest liquidation event within each 1000ms snapshot**, not complete liquidated volume, not historical archive. Proprietary vendors need coverage/QA/price, not trust marketing. |
| Source book depth and aggressor side | Binance live WS bookTicker/depth, Bybit book, exchange trade/event history | live collection feasible *if region/runtime allows* | historical L2 cancellation/queue cannot be faithfully reconstructed from OHLCV ZIP; not claim live maker fills from 1m candles. |
| Market volatility / BTC gate / macro | exchange UTC D1 and external event calendars | contextual features may be created | Macro/upcoming economic calendar can support execution risk label, not replace price/OI or become discretionary A+ score. |
| Coinglass aggregated liquidation/OI | vendor API (terms/coverage may be paid) | potentially cross-venue supplements | not automatically verified, **must** document timestamp, snapshot completeness, retro corrections and pricing. |

**DATA SOURCE FATAL RULE:** No OI at target historic date → no retroactive OI alpha calculation for that period. No real liquidation stream → no «невидимая ликвидация» label from candle high/low. No synchronized spot/perp quotes → no basis strategy economics.

## 4. Shortlist при учёте времени пользователя, автономии и стоимости данных

Оценки являются **экспертным качественным приоритетом**, НЕ бэктестом и НЕ вероятностью прибыльной сделки.

| Кандидат | Источник предполагаемого edge | Автономность | Данные / цена входа в исследование | Риск / ограничения | Приоритет |
|---|---|---|---|---|---|
| **H1: basis/funding dislocation — spot/perp относительная стоимость, delta-neutral** | Перекос perp premium/basis и стоимость переноса как cash flow | Высокая: расчёт по событиям funding, не нужен 24/7 ручной скальп | Исторические original spot/perp + settled funding публичны; cross-venue quote/slippage проверить отдельно | Две ноги, basis/funding sign reversal, margin, latency/hedging; прибыль после fees может быть слабой, не годится для «3-5 сетапов в день» без оговорок | **1: первое дешёвое, понятное и тестируемое** |
| **H2: deleveraging/forced-flow event — OI shock + агрессивные сделки + ликвидационные события** | Вынужденное сокращение плеча и market-order imbalance может создавать краткосрочное продолжение или exhaustion | Высокая после надёжного data collector; решения по событию, без ручного экрана | OI старше 30d Binance недоступен по REST, Bybit historical требует проверку, ликвидации streaming snapshots не полный архив | Критический historical SOURCE_BLOCKED до доказанных источников; риск сбоев и накладывания сильных событий. Нельзя смешать «выброс OI» с directional trade без честного backtest | **2: основной кандидат для событийной направленной торговли после data QA** |
| **H3: sustained signed trade flow + depth imbalance** | Trade-side pressure vs passive quote replenishment, short-horizon price impact | Автоматически, но требует непрерывного low-latency тика/глубины | futures aggTrades archive доступен, глубина L2 historical не гарантия | Более высокие fees и latency, связь short impact с tradable net return не установлена | **3: перспективно, дорого по точности** |
| **H4: cross-sectional relative strength / medium-horizon trend** | slow momentum / crypto sector relative leadership, более редкий turnover | Высокая, легко baseline | Достаточно original1m→D1, universe as-of; легко воспроизвести | Чисто price-based снова может оказаться отрицательным; нужен benchmark не «перекраска зоны» | **4: обязательная дешёвая нулевая/положительная база, не основная alpha по умолчанию** |
| **H5: volatility compression → range breakout continuation** | Change in distribution/volatility rather than chart FVG geometry | Автономно | Original market history sufficient | Прибыльность не доказана, похожие price pattern семьи уже провалились; bad fee asymmetry | **5: факультативный baseline** |
| **H6: news/event impulse** | Rapid repricing post unexpected release | Требует robust event timestamps and fast execution | Историческая публикация новости available_at часто неполная | Latency/slippage dangerous, сложнее объективный event surprise, пользователь не у терминала | **6: macro risk calendar first, not entry** |
| **H7: latency maker market-making / rebates** | bid-ask spread captured on orderflow | Автоматически, но требует colocated depth/queue economics | historical L2 and exchange execution details | Большой operational complexity, adverse selection, не подходит простому старту | **7: не брать** |

**Решение по приоритетам:** сначала **data contract & source feasibility**; затем **H1** как первая маленькая самодостаточная falsifiable стратегия, с чистым delta-neutral cashflow; **H2** как параллельная подготовка исследовательских данных. Не объединять H1+H2 до доказательства хотя бы одной независимой гипотезы.

## 5. Контракт на первый новый эксперимент H1 (только после P0–P3 QA)

**Null:** после затрат и риска neutral spot/perp carry **не** имеет положительной out-of-sample net доходности и не лучше matched neutral/no-trade benchmark на одинаковом капитале и времени. Не доказывать zero risk.

**Input:** BTCUSDT, ETHUSDT, SOLUSDT, заранее объявленные Binance spot/perp со timestamp и raw SHA, historical settled funding + mark/index; возможно Bybit только отдельной независимой venue проверки. Применение 4H зон для стопа/тейка **нет**. Нет плеча 25× как критерия.

**Entry:** по заранее определённому знаку basis vs expected/past-known funding, price after next available quote, только если projected realized funding net of fees/slippage at conservative bounds положителен; никакого использования будущей фактически выплаченной funding при принятии решения. Контроль: no-trade + cost matched naive spot-perp hedge around funding windows (самое важное — entry/exit fee).

**Exit:** по ранее объявленному funding/спред горизонту (например 1 settlement cycle / 3 cycles, но конкретную версию горизонт/триггер/комиссии закрепить *до* чтения тестового периода). Hedge error, notional utilization, spot borrowing need full accounting. НЕТ «фиксированного RR в качестве TP».

**Первый gate:** полноценные actual quotes + funding source receipts и stock of independent historical bars; косты 14/25/40bps **на каждую фактически исполняемую ногу** (roundtrip fee policy должна быть корректно посчитана, не разделить стоимость на два); посчитать trade frequency, avg basis P&L, funding revenue, capital efficiency, tail spread shocks, max adverse basis gap. Если не можно реконструировать real actionable spot/perp two-leg quotes — SOURCE_BLOCKED, а не «прибыль» по midpoint.

**Проверка статистики:** предрегистрация, отдельные discovery/calibration/holdout windows; не использовать прежние CHoCH тестовые окна как «новую слепую историю», если признаки могли быть исследованы в тех же данных; ранняя/поздняя фаза, BTC crash, fees/shock scenario, random funding-time control, venue-specific test, holdout by symbol/weeks; по Binance/Bybit датам до запуска сформировать отдельный paper. 0 profitable -> архивировать H1.

## 6. Контракт на H2, *не* на реальную торговлю

Прежде чем писать исполнительную логику:
1. Fetch small samples OI Bybit earliest date vs symbol inception, exact chronology and pagination; verify funding/spot/perp original/cross-venue source. Для Binance OI only most recent 30d; feasible live collection with versioning, if legal/availability in runtime.
2. Determine whether historical liquidation *complete events* exist from reputable source; if only `forceOrder` snapshots, clearly report coverage censored, not measured forced-sale notional.
3. Specify observational test: if OI`Δ` shock+high aggressive sell followed by price drop, does next 15m/1h have **net tradable** trend or rebound, *independent of already executed price move*? Two direction hypotheses MUST be **separate, preregistered**, not choose continuation vs reversal retrospectively.
4. Control: same symbol/week/volatility/time-of-day matched non-shock observations, clock-random entries, price-only benchmark; inputs only available-at prior to fill. Include no signals as zero and partial data unavailable as ERROR.
5. Independent untouched holdout and PAPER only, 100+ sample if realistic; no target adaptation after source peek.

## 7. Почему «3–5 сделок/день по 1–2% ×25–30» не является исходным требованием к alpha

Это желательная частота и величина движения, но её достижение не гарантируется рынком. Плечо **умножает PnL и риск ликвидации**, не добавляет закономерности; 25bps стоимости roundtrip при 25× — уже около **6.25% маржи** до funding/разворота/slippage. Нельзя считать отдельные прибыльные Telegram screenshots репрезентативной историей. Документ `Исследование механики сигналов CryptoX ProTrading` на Google Drive демонстрировал нерепрезентативность избранных 20 screenshot и выход частями; не переносить result без полного журнала.

## 8. STOP/SUCCESS критерий первичного исследования

- **STOP SOURCE:** несуществующая история OI/forced events, preview funding with lookahead, различие timestamp-unit, mixed provider, 451/gaps, unsupported leg quote simulation.
- **STOP ECONOMIC:** mean net expectation <=0 after conservative costs across 2 untouched regimes, PF<=1.2 where appropriate, confidence uncertainty includes 0, DD/capital risk beyond precommit, performance only from one cherry-picked symbol/month, even if observed positive on synthetic.
- **ENGINEERING SUCCESS:** exact error, full source and feature lineage, no hindsight leakage, reproducible negative controls, immutable scored outcomes; не равен live.
- **ECONOMIC candidate:** only if across valid OOS tests both sign and magnitude survive multiple-testing stress, reasonable number of **independent** event clusters, cost stress and changes in fee/timestamp provider, and monotone prospective live PAPER (not guaranteed).
- **RISK:** реальные ордера не разрешены, no capital target promised, no chasing losses and no risk amplification to save a failing strategy.
