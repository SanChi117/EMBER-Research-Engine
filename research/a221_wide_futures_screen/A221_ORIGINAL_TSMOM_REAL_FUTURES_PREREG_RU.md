# A221 — пререгистрация независимого повторного теста ORIGINAL TSMOM (только USD-M Futures)

Дата 2026-10-31. Мандат `main/RESEARCH_MANDATE_LOCKED.md` строго обязательный. A220 user veto проверен; 3 отклонённых источника НЕ тестируем.

## Источник и семейство

Оригинал [yongzhe2160cs/trading-engine](https://github.com/yongzhe2160cs/trading-engine/tree/efa37deac60fb9d91abcb181440c94f2f0eac4b8) commit `efa37deac60fb9d91abcb181440c94f2f0eac4b8`, `strategy/tsmom.py` Git blob `af7d999ff114a872df6bfe65fb5376577451021b`, `config/settings.py` blob `579df537946b20ce2c8ca55d4a8ab47629b769ba`. Time-Series Momentum (Moskowitz et al.), **не** cross-sectional ranking C1 пользовательского A220. Каждая из BTC, ETH, SOL берёт свой знак изменения цены за 720 1h баров (30d), нормирует позицию по 336h realized vol, cap 1×, пересматривает раз в 24h. Без гипероптимизации и создания своих сигналов.

Авторский отчёт: 2021–2026 net Sharpe≈1.15, maxDD≈−19%, 12m holdout +6.1% и Sharpe≈0.44 vs buy-and-hold −35%. Это НЕ независимое доказательство. Источник разрабатывался под Bybit live, но research прямо использует реальные Binance Vision USD-M OHLCV, в собственном ledger взимает *фиксированный* funding=1bp/8h, не реальный funding каждого settlement. Не путать Bybit live со способом backtest.

## Репликационная задача, frozen до получения PnL

- Монеты: BTCUSDT, ETHUSDT, SOLUSDT USD-M Futures; **счёт единый**, по 1/3 капитала на каждую, общая equity compound.
- Данные: genuine Binance Vision monthly USD-M **1h OHLCV** 2023-11-01 по 2026-09-30, дополнительно **fundingRate settlement** 2024-01 по 2026-09; SHA ZIP и CSV должны совпасть с ранее проверенным A217 source manifest. Запрещены синтетические ряды, fills и нормализация пустых пропусков. UTC uninterrupted 1h, exclude incomplete end.
- Тестовые окна: 2024, 2025, 2026 Jan–Sep; **каждый год независимая оценка** при наличии общей предыстории для 30d lookback, одинаковые frozen параметров, separate restarts with positions flat at Jan1, terminal exit turnover at end. По сравнению с автором это историческая *репликация*, **не истинный untouched OOS**, потому что автор уже видел эти даты.
- Оригинальный Python `tsmom_signals` скачивается byte-for-byte по commit и Git blob SHA — не переписывать.
- Реалистичный independent execution audit: сигнал известен **после закрытия часа**; поставленный на следующем 1h UTC open = next-open, а не known-close same-price. PnL open-to-open на следующем часу. Не утверждать реальные market fills. Проверять continuity, flat warmup, no future-price.
- РАСХОДЫ: BASE commission 5.5bp + execution slippage 5bp per unit weight turnover (original total 10.5bp one-way); STRESS 15bp fee+slippage7.5bp = 22.5bp per unit turnover; both positive. Genuine per-settlement `funding_rate` with correct sign and held position; 8h/actual settlement timestamps. Last-hour end equity excludes unobserved interval and forces terminal closing fee at last available open. No hidden free carry.
- Capital: $3000 single portfolio 1x gross cap (3 sleeves 1/3 each), long/short allowed, no DCA or leverage upsizing. Daily mark-to-market equity and maxDD, year totals net, annualized Sharpe; cash benchmark 0, gross benchmark separately.
- Stress checks: compare to original constant 1bps/8h funding and no funding; concentration, isolated date windows and fee scenarios; no choosing best coin, no parameter selection.
- Acceptance pre-set: BASE and STRESS net >0 across at least two disjoint years, no catastrophic single-year DD >25%, no scenario depends entirely on 2026; explicit fees+real funding and clean logs. Even if pass, **PROVISIONAL** until independent untouched future and execution/mark/liquidation verification. If fail: `RESEARCH_NEGATIVE`, never adjust lookback to rescue 2024–26.
- Extra risks: source code `tsmom_signals` 24h rebalance grid anchored to dataset starting point; freezing start of monthly history is part of replication. Term date marking no taker partial fills, realized spread unobserved. No need to force hundreds of trades/day.

This is one economic test of a public original, not yet proved. Other repository source-only screens in A221 are separate and may reject before PnL.
