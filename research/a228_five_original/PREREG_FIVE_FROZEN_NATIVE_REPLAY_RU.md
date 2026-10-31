# A228 — заранее зафиксированный независимый тест ПЯТИ готовых исходников (не самодельные стратегии)

31.10.2026. Мандат `main/RESEARCH_MANDATE_LOCKED.md` **не изменён**. Пользователь выбрал 5 готовых вариантов и прямо поручил **проанализировать**. Запрещены новые механизмы, оптимизация, удаление отрицательных годов, реальные или существующие PAPER-ордера.

### Freeze originals

| Code class | Exact pin commit SHA | exact git blob SHA | native TF |
|---|---|---|---|
| DualTrendCompressionRestartShortV1Strategy | wangc-joker/ft_userdata @ `6833cb9b4bc5bfb01c3f5829ff11cc02b0814fd9` | `36cfb029cd7dc871160b037548db2c57de852969` | 1h + 4h |
| TrendFollowing | krantikaridev/freqtrade @ `11d7d66c60cf49a148cb61619b8061dc40d2510c` | `ee2293e19f3cdecb082525f6d55a166249f74eb2` | 4h |
| NASOSv7LongShort | remiotore/ccxt-freqtrade @ `44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03` | `172fd2b5e76cb1b14d4c9547b6046bff7f19ba7a` | 5m + 1h |
| BearRegimeShortV1 | IvPalmer/Master-Trader @ `8e29d170982c36a502de2c6ed14a80c6510c4921` | `a6c62639e60a28b050a462f646241e7a2ba9076c` | 1h + BTC 1h informative |
| Risk_Stair_S5 | linhuang1212-coder/crypto-quant-trading @ `63c012a0329a280f99fe57896456d4b9363c9c71` | `9b6ba1f5466727da1e9446f4e283b1c555fca59b` | 15m + 4h |

### Independent first-pass parity

- **Actual ready source**: fetch all 5 at pinned GitHub commits, **git blob hash assert**, no source rewrites.
- **Genuine market**: Binance Vision `data/futures/um/monthly/klines` 5m, BTCUSDT/ETHUSDT/SOLUSDT, source ZIP SHA256 and full month row continuity. Resample **real 5m** to 15m, 1h, 4h exactly at UTC candle boundaries. Missing genuine 5m raw = BLOCKED, no gap fill. Do not use Spot.
- **Funding**: independently fetch genuine `data/futures/um/monthly/fundingRate` 8h settlements, audit SHA against A217 where matched; **mark price** `data/futures/um/monthly/markPriceKlines` 8h, standalone ZIP SHA receipts. Native Freqtrade funding engine *must load actual mark and funding*; no disabling if missing.
- **Native open source execution**: Freqtrade CLI actual `backtesting` and SAME five original source classes; never implement a surrogate signal generator. `trading_mode=futures, margin_mode=isolated`. Comparability: 3 majors only, fixed $1000 starting equity, max open trades = 3, default author's risk, leverage, stop, trailing and ROI; fee **BASE=0.0005/side** (matching Freqle league), **STRESS=0.0011/side** (fee surcharge used only as one *proxy* for spread+slippage, not actual fill impact). No source parameter tuning.
- **Years** 2025 Jan–Dec and Jan–Sep 2026, 2024 Nov–Dec used as chronology warmup, **2024 table from Freqle is third-party not our parity**. Separate independent full year restarts; preserve negative/zero outcomes and full trace.
- **Risk**: compare PnL, maxDD, trade counts, worst trade, exits; if source cannot load or exchange fails HTTP451, explicit `BLOCKED_RUNTIME` / `INSUFFICIENT` instead of fictional backtest. Stable positive on two later periods and stress needed to promote to PROVISIONAL, before mark/liq/fill/tail and forward tests.
- **Possible known limitations**: Freqtrade backtest with candle OHLCV has intrabar stops assuming fills and no actual orderbook liquidity; stop-at-mark vs last may differ, maintenance/liquidation tiers remain independent external requirement. Higher `--fee` is not true slippage simulation. Isolated 5x can liquidate mid-candle — no trust until margin stress. All external league numbers are not our verification.

No dispatch to real or existing PAPER. The test is a GitHub Actions *one-shot source-and-research audit* only.
