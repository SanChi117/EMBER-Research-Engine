# A246 — переоценка ещё СЕМИ ранее перспективных оригиналов, отдельно от Double MA и других повторов

**2026-10-31.** Проверены `main/RESEARCH_MANDATE_LOCKED.md`, issue #9 и A234 реестр. Это аудит **исходных кодов, исходных опубликованных результатов и старого исполнения**, не новый независимый экономический бэктест; никто не получает `VERIFIED_FUTURES_CANDIDATE`. Цель — **продолжить остальные** потенциальные стратегии (R007, R009, R010, R011, R023, R024, R025), не зацикливаться снова на R001/R003/R004/R005/R026. Предшествующий A245 — отдельные нативные эксперименты ещё 6 ранее нерассмотренных исходников; их экономику нельзя предрешать.

## R007 — оригинальная dip_catcher: 2026 плюс есть, 2025 минус, реальный 5m re-entry почти 100%

Frozen `viktors1982/trading@e572140b1b8cb550cb244c67d363087b81bd4ab8` source `freqtrade/strategies/dip_catcher.py` git blob `76ab2b3f91dc7beaa0be8021a245caa2b3f4186f` **заново сверены с оригиналом в A246**: source timeframe 5m, LONG/SHORT, native source 8%-price stop.

Ранее A202 [успешный native/2026](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41156913032) STRESS имел положительные BTC/ETH/SOL/LINK на трёх из четырёх по внутренним порогам; A203 [на другом независимом 2025 периоде](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41157269206) native 8 ZIP / real mainnet USD-M показывает STRESS:
- BTC **−4.7203%**, ETH **−2.4100%**, SOL **−0.3281%**, LINK **−3.7893%**. 0/4 положительных, без удаления сделок. BASE 2025 BTC -4.18%, ETH +0.55%, SOL +3.28%, LINK -0.40%.
- Native trade audit исходного 2025: **98.24% времени занято сразу 4/4 независимых слота**; **667/667** последовательных повторных входов не позднее 5 минут; показатель закрытий ~4.76/день — практически постоянное пребывание в рынке, не самостоятельные сигналы. 2026 исходник similarly 98.6% времени все 4 заняты.
- A202 separate original MAE sensitivity: исходные выигрышные сделки часто терпят 1% adverse move, поэтому нельзя отредактировать SL до 1% и сохранить ту же историческую net curve.

**Итог A246:** `R007=NEGATIVE_2025_FUTURES_NATIVE_STRESS / POSITIVE_PREVIOUS_2026_SCOPE / NOT_VERIFIED`. Старые плюсы 2026 не стерты; старые минусы 2025 тоже. Новая гипотеза для повтора должна менять **данные независимого периода или авторскую full-account реконструкцию**, не ставку/стоп на известных 2025/26. Не нужно снова гонять тот же source-parameter/4 single pair 2025–26.

Источники: `research/native_candidate_screen_20261031/A203_INDEPENDENT_2025_ORIGINAL_DIPCATCHER_FAIL_RESULTS_RU.md` в ветке `research/a203-dipcatcher-2025-independent-holdout-20261031` и `A202_PERMANENT_EXPOSURE_AND_REENTRY_NATIVE_TRADES_AUDIT_RU.md`.

## R009 — SingleB_FixedRR: исходный 10-coin OKX портфель не эквивалентен ETH-only Binance тесту

Frozen `liu57liu456/backtest-autopsy@39e640bf304dfe1edceec74668d8beded39482d5`, source `strategy/SingleB_FixedRR.py` git blob **`9544d6ea47c9905fed86e62c85cf6aca48c0c8c5`**, повторно открыт по source SHA. Original class `SingleB_FixedRR`, 5m, LONG/SHORT, `stoploss=-0.015`, ROI target +1.5%, MOM14 (история A191).

Оригинальный `config.json` git blob **`2de24398a4d187f5fb241b7da921fe7748492fe7`** заново найден: **OKX** 10 символов BTC/ETH/SOL/DOGE/ARB/OP/SUI/LINK/XRP/XLM; wallet **5000 USDT**, stake **500**, max3, Futures isolated, entry ask/exit bid, market universe 10. ЭТО НЕ исходный Binance-native author universe.

A191 реальный Binance USDT-M **только ETH**, native Freqtrade2026.4 [run41142627798](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41142627798): 2026-08-01..09-30 net BASE **+0.4927%**, STRESS **−0.4176%**; PF BASE1.0524, STRESS0.9556; 126/115 trades. Без source-author OKX portfolio parity **нельзя объявлять экономически проваленным весь оригинал**. Но для Binance ETH выбранный cross-market опыт отрицателен при STRESS.

**Итог:** `R009=FUTURES_VENUE_AND_PORTFOLIO_TRANSFER_PENDING`, original author 10 contracts OKX; исследовать отдельно Binance USD-M доступный **пофиксированный 10-coin universe**, без cherry-picking ETH или ручного отказа только за отсутствующий исходный Binance портфель. Не приписывать авторские 14k сделок и $8814 независимому результату Binance.

## R010 — SOL Pullback V9: только 12 входов, результаты proxy отрицательные; 15s/mark не проверены

Frozen source `kboranyldz/sol-trading-research@df3dcb722f1814f9eccf5ebd72facced13063a3e`, source `src/sol_pullback_core_v9.py` git blob **`b18ac10938e6aa91dfa42293a5da6fb6d545039d`**, заново сверен оригинальный большой исходник. Это **живой Binance Futures бот**, не исходный Freqtrade backtester. В коде: 1h закрытый сигнал, 4h SOL+BTC режим, 15-сек polling, исходный TP1/TP2, 1–3x динамика и mark stop; missing point-in-time OI/taker.

A198 independent **author original signal + OTHER execution 5m proxy**, [run41151388321](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41151388321), 2026-05-13..09-30: 16 source raw entry signals, **12** filled trades; author-size ~6%-risk BASE **−14.8038%**, STRESS **−19.4321%**; *external*, неоригинальный 1%-risk cap BASE −2.38%, STRESS −3.70%. Эти результаты являются **результатами proxy**, не native author live path. Нельзя называть фактическим A198 доказанным полным убытком original 15s/mark implementation.

**Итог:** `R010=NEGATIVE_OFFLINE_EXECUTION_PROXY / AUTHOR_15S_MARK_OI_PARITY_NOT_VERIFIED`. Не оптимизировать 12 сделок, не продвигать исходник.

## R011 — Octopus multi-perp CTA: положительный оригинальный perp-портфель, но 788 рынков и liquidation-gap

Оригинал `OctopusTakopi/crypto-trend-following` immutable исследовательский снимок **`804eb428705c913988371c28a57ca051bb3a7f9c`** (репозиторий **НЕ** является user-veto `OctopusTakopi/funding-rate-alpha`). Повторно открыты:
- `scripts/backtest.py` Git blob **`4234829abf6e49e9c1b498b419b3c41ccbd2e3a1`**.
- `results/config.json` blob **`98f773d51f9a7f6432ee45d82b3beeadce21459f`**: original BTC+alt dynamic universe, start2020-01-01 end2026-07-22, account **$100,000**, annual vol target20%, max gross leverage2x, true history funding option, **10bp cost**/turnover, buffer0.1, dynamic sector balancing and correlation.
- `results/report.md` blob **`4a0449c94b1f8fe65a0fc20ea95bd404f339363b`**: author reported **788** total contracts, average **145** concurrent positions, average gross 41.8%, 2020–Jul2026 total return **+242.1%**, CAGR **20.6%**, NET Sharpe **1.041**, max model DD **−30.1%**, holdout Sharpe **1.539**. 92.5% funding coverage in symbol-time table; repository notes short/missing funding for uncovered exposure can be zero.
- Important source admission README: *no historical margin/liquidation or orderbook/queue/impact capacity model*, 2x gross cap only, zero funding when archive unavailable; delisted exchange exit approximation. **Эти пробелы особенно важны при среднем N=145**, и параметры не подтверждены на малом капитале.

**Итог:** `R011=SOURCE_BACKED_POSITIVE_AUTHOR_RESEARCH / INDEPENDENT_BINANCE_USDM_PORTFOLIO_AND_MARGIN_UNVERIFIED`, а не FAIL потому что «похож на TSMOM» или «слишком большой $100k». Запрещено искать лучшие 3 монеты внутри уже просмотренных 788 и называть это независимой original CTA. Для будущего теста — восстановление полной universe/data и верификация risk/liquidation; никакой инвестиционной рекомендации из автора.

## R023 — funding mean reversion: хорошая реклама XRP, но приложенный исходный CSV относится к отрицательному BTC

`Gotodataru/binance-futures-backtest@5ed0d6e39d8a3e951bea40c66e2638c213012e1b`, source:
- `strategy_1_funding_mr/backtest.py` blob `2b3d7e4e7b5ddaf78df4af7706fa30b72ea934a3`, `strategy_1_funding_mr/signals.py` blob `7528f737eddd459b8505972c01fef60d263715e1`. Original 15m funding-MR with 6m train/2m test WFO, 81 combinations of EMA/funding/holding params.
- `shared/data_loader.py` blob `9178ce4ca23bc94d7ea9ff01bacaec7e7ad96e54` reads LOCAL hardcoded `D:\\algotrade2\\BIGdatabaseBinance`, expected 1m klines, 8h funding + 5m OI/taker signals; **actual source data absent from public repo**. Without recreating official FUTURES market metrics timestamps exactly, no claim of reproduction.
- Original README advertises XRPUSDT OOS **+0.19% / Sharpe1.58 / 44 trades**. Independently inspected tracked `strategy_1_funding_mr/results/metrics_per_symbol.csv` blob `8e89dbb6f713ed23923e8546b719459b99440358` **contains only BTCUSDT**, not XRP: author **BTC record** `total_return_pct=-0.2269, PF=0.6183, 139 trades` (interpret scaling with source metrics contract before displaying as percent of capital). The public CSV does **not** verify the README's XRP result. No historical independent Binance OOS replay here.
- Funding original signal uses `funding_rate.ffill().shift(1)`; do not replace with current 8h future settlement values.

**Итог:** `R023=AUTHOR_XRP_POSITIVE_UNCORROBORATED_CSV / MARKET_DATA_SOURCE_BLOCKED / ORIGINAL_LOGIC_AVAILABLE`, **не** приписывать BTC отрицательный результат XRP.

## R024 — OI divergence: source risk far worse than headline +ETH, +SUI

Same upstream source pinned. `strategy_3_oi_divergence/signals.py` blob **`be177d2b24a740bc3ac46115326780c48582ec3e`** 15m lagged price/OI and taker-L/S ratio, continuation/MR. Original author historical `strategy_3_oi_divergence/results/metrics_per_symbol.csv` blob **`64b64d68cfef16a80d46a990c318956fa768d159`**:
- ETH `total_return_pct=0.0741` in author's metric representation, PF **1.023**, author reported max DD `-0.4954` (−49.54%), trades540.
- SUI `total_return_pct=1.6208`, PF **1.1082**, maxDD `-0.975` (−97.5%), trades1334.
- SOL `-0.5455` return metric, PF0.9432, DD `-0.8737`, trades1032; BTC `-0.6623`, PF0.7111, DD `-0.6631`.
- These are authored source CSV values, **NOT EMBER independently simulated returns**; must map units and verify positivity of actual cash ledger. OI and metrics historical private hardcoded dataset missing, so replay BLOCKED_DATA, not universal ECONOMIC_FAIL.

**Итог:** `R024=AUTHOR_SOME_POSITIVE_METRICS_WITH_EXTREME_DD / BINANCE_OI_POINT_IN_TIME_DATA_BLOCK`. Do not select SUI because its author return is best: reported drawdown is catastrophic.

## R025 — Taker momentum: source shows broad cross-symbol negative economics, no reason to repeat identical year

Author `strategy_2_taker_momentum/results/metrics_per_symbol.csv`, frozen Git blob **`6ded98a074c64504c501e93332022d5eeab0abe1`**:
- BTC metric `-0.4515`, PF0.3322, trades318.
- ETH `-0.3466`, PF0.5159, trades349.
- SOL `-0.4506`, PF0.75, trades498.
- SUI `-0.1953`, PF0.8285, trades374.
- TRUMP marginal `+0.0062` in source representation, PF1.0309, trades81 — **не доказанное after-cost устойчивое преимущество**, особенно рядом с общими убытками.
- Source retains BTC/ETH/SOL/DOGE etc negative broad results, no author portfolio margin replay proved. Different from R023 funding and R024 OI; do not mix distinct signals.

**Итог:** `R025=NEGATIVE_AUTHOR_CROSSMARKET_PRELIMINARY / NOT_INDEPENDENT_EMBER_ORIGINAL_PORTFOLIO`. Repeat only with new documented execution discrepancy or genuinely new point-in-time data.

---

## Какие выводы ИМЕННО изменены в A246

1. A202 dip_catcher **не стерта положительная 2026**, но 2025 stress 0/4 и почти постоянная экспозиция ограничивают притязания.
2. SingleB original **10-market OKX**, ETH-only Binance −0.42% stress не даёт права браковать весь оригинал без transfer model.
3. SOL V9 original signal действительно проверен, **original execution 15s/mark НЕ проверен** — нельзя считать 12 proxy-сделок исходным авторским исполнителем.
4. Octopus CTA **нельзя списывать только из-за семейства или $100k**, у автора полноценное публичное исследование, но 145 concurrent и без liquidation invalid for small paper.
5. Funding-MR README XRP +0.19% **не подтверждается приложенным source CSV**, потому что там только BTC; не придумывать ETH/XRP CSV.
6. OI divergence & taker momentum отделены от funding MR как *разные источники сигналов*, и их собственные авторские CSV не заменяются выдуманными EMBER прогонками.

**Дальнейшая очередь в A234+A236 по-прежнему открыта**, A245 отдельно проверяет шесть **других** исходников 36 native runs на 3 pair controlled screen с честной пометкой author parity PENDING. Никто не VERIFIED; никакие live/PAPER расписания/счета не тронуты.
