# A237 prereg — TrendFollowing original common account and complete author universe

Date 2026-10-31. No changes to source strategy and no live/PAPER orders. Binance USDT-M futures ONLY, mandate locked. Preserves A235 18 controlled TF backtest results intact.

Original strategy: `krantikaridev/freqtrade` commit `11d7d66c60cf49a148cb61619b8061dc40d2510c`, `strategies/TrendFollowing.py` Git blob `ee2293e19f3cdecb082525f6d55a166249f74eb2`.

**Pinned authored portfolio config**: `config/config.dryrun.json` same commit, Git blob `965193dbe93e65389c0ce8b5669229667e9fd846`. `strategy=TrendFollowing`, timeframe 4h, BTC/ETH/SOL/BNB USDT perpetuals, `max_open_trades=3`, `stake_amount=unlimited`, `dry_run_wallet=1000`, `tradable_balance_ratio=0.95`, futures isolated, entry/exit pricing and order timeout retained. Difference from A235: adds BNB, changes single-account sizing from fixed $100 to author's unlimited-balance model, and balance ratio from .99 to .95. Some Freqtrade backtest callbacks still model fills without historical exchange orderbook. No dynamic portfolio selection.

Use frozen Freqtrade 2026.9 and pinned strategy from A228 downloader; genuine Binance MAINNET USD-M 5m klines, 8h mark and funding for all **four** pairs 2023-11..2026-05. For BNB no A217 pre-recorded funding SHA exists, download directly from official Binance Vision monthly fundingRate ZIP and record SHA256 of ZIP/CSV, require complete monthly settlement coverage; absolutely no spot fallback or fabricated funding. Testnet futures contract metadata only due mainnet HTTP451, note limitation. If source missing -> fail BLOCKED, not replace with surrogate.

Original single shared $1000 wallet in three independent windows: 2024, 2025, Jan–May 2026, normal 0.05%/side and stress 0.11%/side. **6 predeclared no-selection native runs**; strategy timeframe 4h and finer 5m execution detail, author's protections enabled, no hyperopt. Report total net account return, drawdown, trade count and full ledgers. Previous years already viewed; these are parity replays, **not untouched prospective out-of-sample**.

This is author portfolio correction only for TrendFollowing, not a claim of verified edge. All 76 candidate/variant records remain under audit. If positive, still need current futures fees/slippage/margin/liquidation, genuine order book and forward PAPER before VERIFIED.
