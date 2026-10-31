# Готовность 37 дополнительных компонентов

Дата: 2026-11-01. v0.3.0: `READY_FOR_OFFLINE_USE` (вызов через `invoke`/`run_on_candles`, тесты на 37 ID), **не** доказательство `PRODUCTION_READY` или исходного паритета. Все 37 имеют импортируемые реализацию и базовые unit-тесты на соответствующее тематическое ядро, **но ни одна не получила статуса `PRODUCTION_READY`**. Зрелость исходных авторских стратегий не оценивалась.

Определения: `UNIT_CORE` — функция может быть вызвана на заранее подготовленных данных; `DATA_GATE` — даже осмысленный аналитический результат требует непредоставленных исторических источников, timestamp/ликвидности/маржи; `PARTIAL` — реализован только честно указанный поднабор исходного требования. Несколько меток могут действовать одновременно.

| ID | Доступный код | Статус для последующего подключения | Незавершённое |
|---|---|---|---|
| Z01 | asof_evidence / join_at_decision | DATA_GATE | Binance mark, funding, OI источники, publish-time |
| Z02 | maintenance_required / margin_state | DATA_GATE, PARTIAL | фактические MM tiers, cross-margin, ликвидационный ордер |
| Z03 | orderbook_imbalance / microprice / maker_fill_certainty | DATA_GATE | L2 replay, историческая очередь и частичные fills |
| Z04 | diff_traces | UNIT_CORE | оригинальный исполняемый источник и signal feed |
| Z05 | multileg_pnl | UNIT_CORE, PARTIAL | synchronised legs, частичные fill и hedge rebalance |
| Z06 | replay_cash_events | UNIT_CORE | интеграция с биржевым журналом, funding и маржой |
| Z07 | portfolio_risk_gate | UNIT_CORE, PARTIAL | стратегия-зависимая корреляция и intrabar exposure |
| Z08 | RiskState / save_risk_state / load_risk_state | UNIT_CORE, PARTIAL | согласование с реальными позициями и распределённая БД |
| Z09 | classify_bracket_bar | UNIT_CORE | 1m/tick replay для уточнения AMBIGUOUS |
| Z10 | transition_order | UNIT_CORE, PARTIAL | exchange reconciliation/partial order queue |
| Z11 | advance_zone | UNIT_CORE, PARTIAL | полная авторская wave registry и подтверждение flip |
| Z13 | evaluate_rules | UNIT_CORE, PARTIAL | полный DSL и bracket state |
| Z14 | advance_compression | UNIT_CORE, PARTIAL | источник признака compression, ATR gating |
| Z15 | confirmed_pivots / double_top | UNIT_CORE, PARTIAL | 7+ других фигур и дополнительные условия |
| Z16 | fvg_channel | UNIT_CORE, PARTIAL | авторская схема сглаживания/взвешивания |
| Z17 | failed_breakout | UNIT_CORE, PARTIAL | полные перезапуски/ранний выход в стратегиях |
| Z18 | advance_regime | UNIT_CORE | provenance trend_strength и OOS |
| Z19 | hull_ma / supertrend | UNIT_CORE, PARTIAL | OTT и авторские EWO-параметры |
| Z20 | z_score / fit_ou / ou_z_score | DATA_GATE | funding settlement архив и причинный лаг |
| Z21 | oi_quadrant | DATA_GATE, PARTIAL | OI/taker источники и causality; интерпретация не доказывает сделку |
| Z22 | taker_pressure | DATA_GATE | taker объем по закрытым свечам |
| Z23 | lag_correlations | DATA_GATE, PARTIAL | синхронизированные минутные/тик BTC/alt |
| Z24 | momentum_ranks | DATA_GATE, PARTIAL | фиксированный universe по времени и basket execution |
| Z25 | pair_spread | DATA_GATE, PARTIAL | cointegration test, two-leg fills, costs |
| Z26 | mean_dislocation | UNIT_CORE, PARTIAL | RSI filter, holding decay, liquidity caps |
| Z27 | ModelContract / verify_model_contract | UNIT_CORE, PARTIAL | ML training and inference intentionally NOT implemented |
| Z28 | fibonacci_retracement | UNIT_CORE, PARTIAL | E1/E2 order sizing, spread/slippage, stop policy |
| Z29 | paired_ablation | UNIT_CORE | independent OOS and matched trace runner |
| Z30 | information_coefficient / bonferroni_pvalue | UNIT_CORE, PARTIAL | DSR and cross-sample block bootstrap |
| Z31 | pnl_attribution | UNIT_CORE | regime and symbol source annotation |
| Z32 | leakage_violations | UNIT_CORE, PARTIAL | static scanner arbitrary external Python/Pine |
| Z33 | diff_traces | UNIT_CORE, PARTIAL | exact source portfolio & config parity |
| Z34 | capacity_limit_quantity | DATA_GATE, PARTIAL | actual queue/market impact |
| Z35 | session_pnl | UNIT_CORE | preregistered study and independent OOS |
| Z36 | exposure_report | UNIT_CORE, PARTIAL | streaming concurrency & reentry metrics |
| Z37 | staircase_risk | UNIT_CORE, PARTIAL | multiple entries / maintenance margin feedback |
| Z38 | diff_traces | UNIT_CORE, PARTIAL | original Freqtrade/Pine runner adapter |

`Z12`: уже реализован в SMOKE; дублирование исключено. Ни одна из строк не является разрешением запускать торговлю или бэктесты.


## Обновление v0.3 — реальное исполнение функций

Технически исполнимые реализации **всех 37 ID** дополнены 34 связанными операциями; тестируются через `invoke`, общий Binance USD-M loader, `run_binance_usdm`, импорт CSV сигналов и SQLite event ledger. Наличие тестируемой функции не означает автоматическую торговую интеграцию, оригинальную лицензию или доказанную доходность.

| ID | Добавленная работающая операция | Ограничение |
|---|---|---|
| Z01 | `Z01.signal_frame`, BinanceUSDMPublic funding/OI/mark | Историческая публикационная задержка гипотетична, фиксировать receipt |
| Z02 | `Z02.liquidation_boundary` | Только при фактических maintenance tiers; не Binance liquidator |
| Z03 | `Z03.depth`, `Z03.quote_fill` | Гарантию исторического fill по REST не получить |
| Z04 | `Z04.parity`, `Z38.parity_exports` | Нужен результат оригинального исполнителя |
| Z05 | `Z05.cash_ledger` | Реальные две ноги требуют внешних receipts |
| Z06 | `SQLiteResearchLedger` | Offline evidence; нет реальных ордеров |
| Z07 | `Z07.correlated_gate` | Консервативный суммарный риск, без риск-неттинга |
| Z08 | `SQLiteResearchLedger.set_risk_if_version` | Достоверная синхронизация с биржей отдельно |
| Z09 | `Z09.bracket_uncertainty` | Dual touch = AMBIGUOUS без последовательности тиков |
| Z10 | `Z10.replay`, `resolve_order_replay` | Только предоставленные подтверждённые fills |
| Z11 | `Z11.history` | Не доказывает SMC авторский wave registry |
| Z12 | Ранее имеется в SMOKE | Не дублируется |
| Z13 | `evaluate_rules` | Типизированный декларативный subset; не произвольный Pine |
| Z14 | `Z14.compression` | Сигнал не является готовой торговой системой |
| Z15 | `Z15.patterns` | Детекторы паттернов — независимая реализация, а не оригинал |
| Z16 | `fvg_channel` | Не оригинальная сглаживающая формула внешнего автора |
| Z17 | `Z17.failure_exit` | Не прикручен к действующему PAPER order state |
| Z18 | `advance_regime` | Нужен actual/causal strength |
| Z19 | `Z19.ott`/`Z19.var`, HMA/SuperTrend | Не источник чужой прибыли |
| Z20 | `Z20.funding`, OU/z-score | Нужен фондовый settlement history |
| Z21 | `Z21.oi` с causal alignment | Binance OI период истории ограничен |
| Z22 | `Z22.taker_series`, `klines_with_taker` | Taker-buy доступен как поле Futures Kline |
| Z23 | `lag_correlations` | Нужны синхронные BTC-alt ряды |
| Z24 | `Z24.basket` | Нужны замороженные по времени вселенная/история |
| Z25 | `Z25.pair_diagnostics` | AR(1) экран не доказывает коинтеграцию |
| Z26 | `Z26.dislocation` | Ни прибыльность, ни exit price не подтверждены |
| Z27 | `Z27.predict_linear` | Только безопасная JSON-логистическая модель, не закрытый LightGBM |
| Z28 | `Z28.dual_entry` | Риск обоих ордеров ограничен без брокерского исполнения |
| Z29 | `paired_ablation` | Нужен фиксированный OOS и одинаковая база |
| Z30 | `Z30.bootstrap`, Bonferroni, IC | Нет правдивой DSR без истории числа попыток |
| Z31 | `Z31.regimes`, `Z31.trade_exports` | Нужен правильный денежный PnL и метки regime |
| Z32 | `Z32.scan_source`, `leakage_violations` | Статический скан эвристический; не полное доказательство |
| Z33 | `Z04.parity`, `Z38.parity_exports` | Продукты сигналов должны быть известны |
| Z34 | `Z34.impact_envelope` | Стоимость по сценарию, а не гарантированный фактический fill |
| Z35 | `Z35.preregistered` | Окна определяет вызывающий до проверки |
| Z36 | `exposure_report` | Нужны реальные интервалы открытия/закрытия |
| Z37 | `Z37.with_addons` | Для liquidation-grade нужен mark и реальные tiers |
| Z38 | `Z38.parity_exports`, `Z38.normalize_original` | Не запускает сам Freqtrade/Pine, читает их собственные записи |

### Итог готовности

**Рабочими стали вычисления и программные интерфейсы**, доступные немедленно по импорту. **Биржевые процессы и точная исходная механика каждой стратегии** не могут считаться готовыми без недоступных на входе данных, параметров и реального исходного исполнителя. Эти требования нельзя исправить объявлением статуса READY.
