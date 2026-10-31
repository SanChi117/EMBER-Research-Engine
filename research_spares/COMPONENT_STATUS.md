# Готовность 37 дополнительных компонентов

Дата: 2026-11-01. Все 37 имеют импортируемые реализацию и базовые unit-тесты на соответствующее тематическое ядро, **но ни одна не получила статуса `PRODUCTION_READY`**. Зрелость исходных авторских стратегий не оценивалась.

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
