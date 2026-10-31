# A205 — независимое опровержение оригинала AggressiveSupportResistanceScalper: pre-registration ДО анализа PnL

Дата: 2026-10-31. **Исследование только на исторических данных, нулевые реальные/PAPER-ордера, никаких изменений SMOKE и планировщиков.**

## Контроль A204 и отбор
A197–A203 зафиксированы в `A204_POSTMORTEM_SCREENING_AND_REUSABLE_TOOLING_RU.md`. Не повторять стратегию dip_catcher, которая дала PASS в 2026, но FAIL 2025 и 98% постоянной экспозиции. Не выбирать победителя среди многократных тестов по последним наилучшим процентам.

Рассмотрены три разных класса кандидатов ДО бэктеста:
- [`AggressiveSupportResistanceScalper`](https://github.com/Meszqt/freqtrade-test/blob/7062cdd465f30acb480f6ad8f678f958a8a0e554/user_data/strategies/AggressiveSupportResistanceScalper.py): **выбран для независимого скрининга** благодаря истинной предшествующей опорной зоне `low.shift(1).rolling(48)`, подтверждённому отказу от уровня, фито/body, EMA/RSI, LONG+SHORT, no DCA, 90m `custom_exit`, фактический SL 6% margin при 10x (≈0.6% цены) и TP11% margin (≈1.1% цены).
- `Winner15m` из `win-boom/BTCquant`: оригинальные EMA/MACD/ADX/ROC **состояния**, а не короткие one-shot события; `enter_long` и `enter_short` выставляются многим барам подряд. Оставлен отдельным отрицательным контролем на возможную постоянную экспозицию, НЕ выбран и НЕ оптимизируется.
- `RsiquiV5` отклонён уже из-за `np.gradient` centered future contamination в прошлых оригинальных тестах; `HighFrequencyStrategyV1/2` имеют внешние ранжированные экономические FAIL.

## Замороженный оригинал
- `Meszqt/freqtrade-test@7062cdd465f30acb480f6ad8f678f958a8a0e554`, файл `user_data/strategies/AggressiveSupportResistanceScalper.py`, Git blob `4e3084865a95a694be5178fe60d9130ecd24c002`; исполнение ТОЛЬКО класса `AggressiveSupportResistanceScalper` — не оптимизированных вариантов SR24/96.
- `can_short=True`, `timeframe=5m`, `stoploss=-0.06` **не 6% цены** — 6% от маржи при 10×, `minimal_roi={"0":0.11}`, `leverage=min(10,max_leverage)`, trailing=False, `position_adjustment_enable=False`, лимитный вход по границе S/R с `maximum_entry_distance_ratio=0.012` от предложенной цены и выходы LIMIT; на 45m с `current_profit>0.01` custom_exit `fast_profit_rotation`, на 90m `scalp_time_limit`.
- Его внешний [Freqle League](https://freqle.org/strategy/36e5874af3a1ebcf) утверждает **381 trade на 33 монетах/3 года**, PF1.86, +55.8%, DD4.51%. Это ПРОИЗВОДНАЯ многомонетного исторического leaderboard, а не независимый 4-символьный backtest. 381/(33×1095)≈0.0105 сделок в день на монету; для 4 монет ожидание лишь ~0.04/сутки, если средние равномерны. Эта крайне низкая внешняя частота уже предупреждает, что наша цель 3–5 закрытых A+ в сутки вероятно не будет достигнута. Мы это НЕ будем скрывать даже при прибыльном результате.
- Внешний отчёт также сообщает среднее удержание **46h**, MAX >200 суток вопреки `custom_exit` 90m. Возможный дефект исполнения модели/лимиток/версии в исходном рейтинге; проверяем `open_date`→`close_date` из подлинных ZIP, `exit_reason`. Если backtest нарушает авторский TTL, это FAIL уровня parity.

## Замороженный тест до PnL
- `freqtrade==2026.4`, Binance USD-M REAL 5m OHLCV 1h mark/funding. Отдельные BTC/ETH/SOL/LINK каждый со своим wallet $1000, `stake_amount=100` USDT маржи, one open position per pair, **оригинал 10×** (notional ~$1000/position), isolated; не смешивать 4 кошелька с одним реальным портфелем.
- ДВА независимых года: **2025-05-13…2025-09-30** (первый chronological validation) и **2026-05-13…2026-09-30** (второй); исходники 2025/2026 уже известны другим стратегиям EMBER, значит это не абсолютно чистый общепроектный OOS; но исходные параметры данной стратегии не меняются.
- ДВА `--fee`: BASE=0.0005/fill и STRESS=0.00125/fill, both directions, *fee applied to nominal leverage*. Включить funding; проскальзывание/реальные неисполненные лимитки/очередь не моделируются; к слепому торговому одобрению не подходят.
- 16 подлинных native ZIP (4 coins×2 fees×2 years), SHA256 Freqtrade, fixed source blob, сверка trade PnL sum, абсолютная прибыль по индивидуальному кошельку, PF/DD, winrate, median/p90/max duration, reentry gap и utilisation. Символ и год запрещено выбирать post hoc.
- ECONOMY GATE: >=2 ИЗ 4 монет показывают одновременно в **обоих годах и обоих расходных сценариях** N>=35, wallet net>0, PF>=1.2, wallet DD<15%, top3 gross wins share<60%. Кроме того, >=141 завершённых trades на 4 отдельных wallets в каждом году/fee (~1/day). Целевой TEMPO GATE: >=3/day across 4, p90 hold<=24h, минимум 70% повторных входов спустя >5m после предыдущей сделки, >=20% времени имеются свободные слоты.
- PARITY/RISK GATE: не более 10% открытых сделок держатся >2h без специально документированной причины, если автор заявляет TTL90m. Не менее 2x liquidation buffer stop (с учётом margin tiers), ликвидация не раньше SL; нет DCA; no live approvals. Вынести отдельно execution slippage gap (для оригинальных лимиток), если economic PASS.
- Даже PASS экономики — не готовность. Для EMBER MTF отдельная структурная 4h модель остаётся обязательной; этот оригинал локальные 5m уровни не имеет права называть 4h уровнем.

## Контроль выполнения
1. Записать данный документ и парсер в GitHub ДО запуска workflow.
2. Workflow в отдельной исследовательской ветке, автоматический push trigger, архивы upload.
3. Только после получения native ZIP опубликовать подписанный машинными SHA отчёт и **FAIL/PASS без ретюнинга**.
4. Если CI не работает → BLOCKED, нет искусственных данных.
