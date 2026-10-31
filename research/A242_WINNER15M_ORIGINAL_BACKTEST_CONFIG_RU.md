# A242 — Winner15m: найден точный исходный Binance Futures backtest config (R026)

Дата 31.10.2026. Исследование only Binance USDT-M Futures; без реальных торгов и изменений PAPER, мандат `main/RESEARCH_MANDATE_LOCKED.md` LOCKED. Не экономический replay, не прибыльный VERIFIED.

## Source receipt (upstream pinned)

`win-boom/BTCquant`, commit `82c6955a15f80196d1e0ae8320b2c41432980b40`:

- `user_data/strategies/winner_strat.py`, Git blob `585df3f6198837230816c73fe59957996f45d13a`. Class `Winner15m`, timeframe **15m**, `can_short=True`, stoploss `-0.025`, trailing stop enabled, startup200, ROI schedule and repeat-entry behavior unchanged. Source docstring advertises 27.6% annual/Sharpe3.23/65.8% win rate and 6 positive rolling windows — these are **author claims**, not tested independently here.
- **Newly restored exact class-specific config**: `bt.json`, Git blob `1bb32124e520afad646cdf66210fc8f853d53395`. It explicitly names `"strategy":"Winner15m"`, `"timeframe":"15m"`, `"trading_mode":"futures"`, `"margin_mode":"isolated"`, exchange Binance, `pair_whitelist=[BTC/USDT:USDT, ETH/USDT:USDT]` in this order, **wallet=100 USDT, stake=30 USDT**, `max_open_trades=10`, entry/exit price_side=same with limit-orderbook top1.
- Repository `docker-compose.yml`, blob `8733f8f96d3e5d9fa10a4a8d78979e28efc44401` lists container `freqtrade-w15` pinned `freqtradeorg/freqtrade:2025.11` and mounts `user_data_w15/config.json` (runtime file not present in pinned tree); author README lists Winner15m as an active 15m strategy at port8084. **The discovered bt.json is source-backed for a historical backtest**, not proof it matches unpublished live config.
- `full_backtest.sh` blob `...not verified in this checkpoint...` lists 8 markets BTC ETH SOL BNB XRP DOGE ADA AVAX, but invokes `--config /freqtrade/config.json` mounted from **MTF** service, not the exact `bt.json`; therefore this 8-pair batched diagnostic is a *different reference* and must not be silently substituted for Winner15m class-specific backtest config.
- `bt_config.json`, blob `cdfe2f3ace94224736cbe2c3a45b02bb3c650b06` points at `BtcEth4hStrategy`; cannot be ascribed to Winner15m. A234 source audit correctly warned about this confusion, but missed `bt.json`.

## New controlled economic replay (not yet executed in this source audit)

Before every test, verify original class/config blob SHA. Use native Freqtrade (priority 2025.11 from author Docker) on genuine MAINNET Binance USDT-M BTC+ETH 5m OHLCV→15m plus historical mark/funding, proper fees and 5m detail. Freeze two fees and multiple annual windows before results; **one account $100** with stake $30, max10; Freqtrade will constrain margin if more than 3 full stakes cannot be covered. No invented leverage; source has no leverage override (use native futures default and explicitly report if different). Do not add cooldown or remove recurrent signals. The prior 2025.11 Docker config may require technical adapter for market metadata if mainnet API returns 451; note its limitations separately.

Status `R026 CONFIG_RECOVERED / ECONOMICS_PENDING / NOT_VERIFIED`. This restores an actionable original for independent evaluation without falsely claiming positive history. A240 Double MA shared account in parallel, A241 BearRegime negative external source evidence. A234+A236 76 records remain in broad re-evaluation.
