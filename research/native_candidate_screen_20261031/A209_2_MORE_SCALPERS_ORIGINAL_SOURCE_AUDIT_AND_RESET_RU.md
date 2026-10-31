# A209 — source-only отбор ещё двух быстрых скальперов без повторения ненадёжных тестов

Дата: 2026-10-31. RESEARCH ONLY. Это исходный аудит, **не финансовый бэктест**, доходность и PF ниже не утверждаются. Отделять source facts от рекламных claim.

## Кандидаты (один публичный автор, разные оригинальные классы)
Repo `remiotore/ccxt-freqtrade@44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03`.

**1) AdvancedScalpingStrategy 5m**
- Исходник `strategies/AdvancedScalpingStrategy.py` Git blob `a3a5563aa626e51d940f87a8f8524bc316e40716`.
- Документированы `timeframe="5m"`, `can_short=True`, stoploss `-0.015` (рисковая доля с плечом), ROI2% в минуту0→1.5%@5min→1%@10min→0.5%@20min→0%@30min, `leverage=min(max_leverage,5.0)`.
- **Проверка реального кода: только `enter_long` в `populate_entry_trend:255–295` и только `exit_long` в `populate_exit_trend:297–322`; нигде в исходном файле не устанавливается `enter_short=1`. Значит `can_short=True` сам по себе НЕ создаёт SHORT-сделок. На фьючерсах можно тестировать *только long-only original*, а это не цель A+ bilateral 3–5/day.
- Комментарий `multi_timeframe_momentum` вводит в заблуждение: фактически RSI3/5/21 посчитаны на **одном 5m**, нет informative 4h/15m. `dynamic_support_resistance` uses `high.rolling(20).max()` and `low.rolling(20).min()` including same current candle, not causal *prior confirmed* zone; weighted indicator not honest 4H structure.
- Авторский `custom_stoploss` существует, но `use_custom_stoploss=True` не активирован, это лишь обёртка; не принимать маркетинговые «dynamic ATR stop» claims. 
- Отсеян как готовый LONG/SHORT event scalper. Адаптация `enter_short` — **новая стратегия**, она запрещена к интерпретации как оригинальный бэктест.

**2) AlphaMomentumStrategy v3.1 1m**
- `strategies/AlphaMomentumStrategy.py`, Git blob `2ec5431f7958f4b0801881d31603bc381485ca48`.
- Исходник действительно устанавливает `enter_long` AND `enter_short`, но `timeframe='1m'`, `stoploss=-0.006` как доля leverage-risk, trailing 0.2% margin activation0.4%. Base leverage4x regime-adjusted.
- 14 обязательных AND-фильтров по каждой стороне: momentum+acceleration, volume>2.8×SMA, ATR% `>0.014` **1.4% движения ATR в одной минуте** default, confluence, RSI/Stoch, часовая фильтрация. На BTC/ETH 1m это чрезвычайно высокое требование, поэтому прежде чем дорогой 1m native backtest нужен независимый scan количества сырых сигналов и реалистичного ATR. **Пока не утверждаем zero trades без настоящего скана.**
- Авторский комментарий о «6 месяцев LIVE +198%, Sharpe4.7, Win81.2%, DD3.8%» — только текст в .py, **не подтверждён настоящим подписанным live journal** в анализируемом файле, не основание включать.
- Вероятное расхождение: `custom_stoploss` не действует если нет class `use_custom_stoploss=True`; code uses custom_stoploss but в оригинале не обнаружен этот activation flag. Stoploss -0.006 remains. Риск неверной рекламы.
- TIMEFRAME1m требует 1m tick detail и издержки. **Status: PREFLIGHT_LOW_PRIORITY**, нет подтверждения edge. Не включать в A207/A208 бессодержательные маркетинговые доходности.

## Параллельные методические результаты (фактически проверено)
- A207 source `Gotodataru/binance-futures-backtest` настоящие taker-buy pressure 5m, 2024/2025/2026 May-Sep, 120 Binance source ZIP и 24 trade receipt SHA: **economic FAIL 0/4 все три года, N24/53/101**. Среди 178 сделок 166 вышли по time exit 80m, десять по SL, две по TP2%; даже до сильного стресс-тарифа сигнала направления почти нет. См. `A207_ORIGINAL_TAKER_VOLUME_3YEAR_FROZEN_REAL_BINANCE_FAIL_RU.md`.
- A208 source `kiattisakph/crypto-scalp-bot` 3m+15m динамический топ-гейнер, авторский тестер **lookahead future 3m/15m close at open_time**, `pnl_pct` undefined in `_close_position`, no fee/slippage/funding in `_calc_pnl`, значит исходник не годится для честной оценки, см. `A208_DYNAMIC_GAINERS_3M_15M_ORIGINAL_BACKTEST_SOURCE_REJECT_RU.md`.
- A206 независимая raw-signal vs fill проверка A205 была опубликована как workflow, но CI JSON до сих пор не подтверждён. **Не считать A206 законченным**; A205=FAIL не пересматривать.

## Заключение
Среди просмотренных не найден **подтверждённый на оригинальном коде** готовый 5m/15m bilateral short-stop profitable event scalper. Полезные идеи: реальные taker-flow pressure с volume context, event-only rejection from past close-confirmed zone, строгий point-in-time top-gainers subset. Никакого допуска к исполнению, пока не выполнены separate fresh OOS and realistic fee / volatility / order-fill / leverage checks. Реальные и виртуальные ордера пользователя не менялись.
