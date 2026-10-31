# A239 — контрольный срез полной переоценки перспективных оригиналов (31 октября 2026)

**Статус: НЕ ЗАКРЫТО.** Пользователь требует пересмотреть все потенциально перспективные стратегии прежних циклов, не ограничиваясь одной. Locked scope `RESEARCH_MANDATE_LOCKED.md`: Binance USDT-M Futures, original pinned SHA, causal native historical returns + real funding/mark, independent execution/margin, no new invented strategy, no live or active PAPER changes.

## Вселенная проверки

- A234 [машинный реестр 74 записей кандидатов и вариантов](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a234-all-promising-candidates-review/research/all_candidates_a234/registry.json) — 74 `REVIEW_OPEN`, не 74 завершённых экономических проверки.
- A236 [разобраны 21 пропущенных ссылок](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a236-unclassified-source-triage-20261031/research/all_candidates_a234/A236_TRIAGE_21_SOURCES_RU.md); +2 отдельных TRANSFER гипотезы R075/R076, в сумме **76 записей/вариантов**. Остальные источники разделены на отрицательные внешние свидетельства, инфраструктуру, venue mismatches и неопределённые / SOURCE BLOCK. Исторический охват остальных веток проекта не доказан полным.
- Запреты пользователя A220 на 3 конкретных репозитория и veto A214–A216 сохраняются, не открывать запрещённые исследования.
- Double MA **не CONFIRMED**: A233 4 отдельных счёта не равны одному исходному BTC/ETH общему счёту, top3 concentration. R001 ожидает нативный общепортфельный тест.

## Найденные ошибки прежних экономических выводов

A230 runner имел `"timeframe":"1h"` для каждой стратегии (не соответствовал TrendFollowing=4h, Risk S5=15m, NASOS=5m). Портфельный конфиг (stake, equity allocation, pair universe, max_open_trades) также часто не соответствовал оригиналу. Новые проверки не делают старые результаты «ложью», но ограничивают их область валидности тем прежним runner.

### A235 — 18/18: source-native TF, 3 pair контролируемый baseline

- [Отчёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a235-native-timeframe-parity-20261031/research/A235_RESULTS_RU.md); [GitHub Actions](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41241733734); full native trade artifact SHA `2d1098c7ee6676d8bdbf8bd209478ed976a98336b5a6149ad724767a539af1e2`.
- Stress 0.11% per side: TrendFollowing 2024 −17.57%, 2025 −4.98%, 2026 Jan–May −3.24%; Risk S5 +4.56%, +5.48%, −6.40%; NASOS −0.81%, −0.21%, 0% with 0 trades in 2026. Still 3 pair fixed $100 stake, no source author shared account proof.

### A237 — 6/6: оригинальный TrendFollowing shared account, 4 pairs

- Pinned original `krantikaridev/freqtrade` source class 4h and author config SHA; original BTC/ETH/SOL/BNB common wallet 1000, unlimited stake, 3 positions.
- [Отчёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a237-trendfollowing-author-account-20261031/research/A237_AUTHOR_RESULTS_RU.md); [CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41242861062); [machine PnL](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a237-trendfollowing-author-account-20261031/research/A237_AUTHOR_RESULTS.json).
- Stress 0.11%/side: **2024 −49.99%, 2025 −43.37%, Jan–May 2026 −9.84%**. `NEGATIVE_AUTHOR_ACCOUNT_3_PERIODS`, no manual tuning to rescue. Genuine Binance mainnet 4 pairs + funding/mark with official ZIP SHA and testnet contract metadata. Risk profile model severely negative; not generalized to all future markets.

### A238 — 6/6: оригинальный Risk_Stair_S5 shared account, 4 pairs

- [Экспериментальный author config и manifest audit](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a236-unclassified-source-triage-20261031/research/all_candidates_a234/A236_RISK_STAIR_S5_EXPERIMENT_CONFIG_AUDIT_RU.md) restored source `risk_experiment_manifest.json`, `run_risk_experiments.ps1` and `config_backtest.json`. Exact deployed strategy folder still has discrepancy in archival script `experiments` vs pinned class `risk_exp`, so author historical full deployment not independently proven.
- [Полный отчёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a238-risk-stair-author-account-20261031/research/A238_RISK_AUTHOR_RESULTS_RU.md); [GitHub Actions](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41243084798); [machine PnL](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a238-risk-stair-author-account-20261031/research/A238_RISK_AUTHOR_RESULTS.json).
- Source class 15m, 4h informative, **5× leverage**, BTC/ETH/SOL/ADA, shared wallet $1000, `stake_amount=unlimited`, ratio .40, max positions 4.
- Stress 0.11%/side: **2024 +22.29%, 2025 +11.80%, Jan–May 2026 −2.74%**; DD stress 10.19% / 16.53% / 9.88%; 167 / 150 / 61 trades respectively. `PROMISING_BUT_UNVERIFIED`: no verified maintenance-margin/liquidation model, no genuine order-book slippage/gap fills, no untouched OOS. One recent window negative.

## Next research queue (not an executed claim)

1. **R001 Double MA** author BTC+ETH one shared account and source state, distinct from 4 separate sleeves A233; use pinned exact original portfolio, with no retrospective tuning.
2. **R003? BearRegimeShortV1** (exact registry ID verify before commit): source-backed author config has **20 markets**, wallet $200, max2 stake100, different from A228 $1000/3 pairs; evaluate source chronology 1h BTC informative 20d momentum and author ex-post negative year evidence before spending on huge archive download.
3. Winner15m, MTF_Hybrid, FTR, FVG, VolatilitySystem and all A234 entries should receive source/config/causal/economic status, not premature negative labels. For Risk S5, next critical gate is 5× margin/liq + execution + genuinely untouched forward OOS before any automated PAPER candidate promotion.
4. Preserve all negative receipts. Updating an experiment's methodology must use separate pre-registered branch and diff, never fake 0% on a failed command. Multiple variants in a registry record must be individually tracked before declaring full coverage.

## Conclusion

**30 new completed native trials A235(18)+A237(6)+A238(6), 0 independently VERIFIED strategies.** The broad 76-item queue is **NOT done**. The immediate evidence favors further research on original Risk S5, while original TrendFollowing author portfolio showed significant losses. No live orders and no change to scheduled PAPER routines. This checkpoint only catalogs completed work, no future results claimed.
