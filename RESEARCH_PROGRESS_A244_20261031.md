# A244 — очередной контрольный срез полного пересмотра 76 записей (2026-10-31)

**LOCKED**: `RESEARCH_MANDATE_LOCKED.md` и issue #9, Binance USDT-M Futures, pinned original source, causal native economic tests, no real/live/PAPER planner changes, 0 independently `VERIFIED_FUTURES_CANDIDATE`. Это дополнение к `RESEARCH_PROGRESS_A239_20261031.md`, которое остаётся неизменным архивным checkpoint.

## Главное новое проверенное — R001 Double MA A240

- [Полный A240 отчёт, оригинальный BTC ETH один общий wallet](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a240-doublema-one-wallet-native-20261101/research/A240_AUTHOR_ONE_WALLET_RESULTS_RU.md); [GitHub Actions 4/4](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41244491757); [машинные результаты](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a240-doublema-one-wallet-native-20261101/research/A240_AUTHOR_ONE_WALLET_RESULTS.json).
- Source commit `40af5c7c1c44253766428cfb06babf22f9817aa4`/Git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`; author config Binance blob `b16e6695673c58d8b7a712fd329994b3a85313f4`. Shared BTC/ETH one $10k account max1, stake unlimited with default custom stake $10k, 2x; native Freqtrade2026.4 genuine Binance USD-M 1h+5m mark/funding, 4 runs, both fee scenarios.
- **STRESS 0.125%/side**: 2025 Apr-Dec **+0.3788%**, model DD **21.43%**, 57 trades; 2026 May-Sep **−13.9674%**, model DD **30.07%**, 45 trades. BASE 0.05%/side: 2025 +17.9204%, 2026 −0.9078%. The earlier positive A233 **four separate $10k wallets** `+7.15%,+5.58%` were **not author BTC ETH shared account**; they remain valid only as archival diagnostic, not deleted.
- R001 now `NEGATIVE_HISTORICAL_SHARED_WALLET_STRESS / NOT_VERIFIED`. Genuine trade ZIP artifact **13059132102**, digest SHA256 `d5f3b450895ec44909450ea7c1e8e7d46bae5acbbf792a4ff9fd3d68b627ab77`. Limit fills, official margin/liquidation tiers, high-fidelity execution still not verified; no prospective untouched OOS. Do **not** move to PAPER or tweak parameters to rescue seen years.

## Additional coverage

- R003 [A241 BearRegime author 20-asset $200 account and author's own negative 3/4-year receipts](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a241-bearregime-author-evidence-audit-20261031/research/A241_BEARREGIME_AUTHOR_PORTFOLIO_EVIDENCE_RU.md). Audit of frozen source/config and author report, **not** new independent EMBER backtest; keep `REVIEW_OPEN_WITH_AUTHOR_NEGATIVE_EVIDENCE`.
- R026 [A242 Winner15m exact author backtest config source-recovered](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a242-winner15m-original-config-recovery-20261031/research/A242_WINNER15M_ORIGINAL_BACKTEST_CONFIG_RU.md): `win-boom/BTCquant` pinned `bt.json` Git blob `1bb32124e520afad646cdf66210fc8f853d53395`, explicit strategy Winner15m, BTC/ETH USDT-M, 15m, wallet $100, stake $30, max10. Previously class configuration was marked not recovered. Distinct from repo's generic `bt_config.json` for a different strategy and 8-market batch diagnostics.
- R026 A243 [native original Freqtrade 2025.11 workflow](https://github.com/SanChi117/EMBER-Research-Engine/actions/workflows/ember-a243-winner15m-original-native.yml) source + author config run at `research/a243-winner15m-original-native-20261031`. The first data staging failed because source downloader was written against Freqtrade 2026.9 funding storage schema. Corrected for 2025.11 with **unchanged real funding rates encoded in expected OHLCV-shaped storage**. As of this checkpoint, data loading has passed; economic runs in progress. No claimed PnL or status until full Freqtrade ZIPs/CI complete.
- R004 Risk_Stair_S5 A238 remains `PROMISING_BUT_UNVERIFIED`: original author 4-asset shared wallet had 2024/2025 positive STRESS and Jan-May2026 negative; 5x official liquidation/fill/OOS still needs independent tests.

## How to continue, not restart

Follow A234 74 + A236 2 additional R075/R076=76 entry/variant queue (not 76 independent tested systems). A240/A241/A242 are distinct evidence types and should update those specific registry cards without conflating 4-wallet and one-wallet tests. Once A243 run succeeds/fails, record full economic PnL/blocked reason without treating a failed job as 0%. Then independently continue next source-based class with original pair universe and account, no new invented signal. Preserve original negative evidence and user veto sources A220 and A214–A216.

**No actual trades, no existing PAPER schedules, no locked mandate changed.**
