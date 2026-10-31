# A218 — original two-perpetual cointegration source/execution audit

2026-10-31. Locked mandate main blob 6afd84271ec3d07c28d4dc682fcd17eceac22d50 and issue9 reread after A217 completion. No spot, no orders, no existing PAPER changes.

Source found by GitHub query `binance futures pairs trading cointegration language:Python`: djienne/pair_trading_NEDL at commit 1823a2137d5b02a5649b32328d024057c968ada0. pair_trading.py blob65e7c6dd3b8d62067704ad2148082392bbc17814; backtest.py blob48bcb2417fb3798349df9be97244ddb829e19121; config.json blobefbb698bc1072356051fcbc669943fddf1b3a6b7. Related fork is NOT a second independent mechanism.

Family: cross-asset cointegration / relative-value mean reversion, BTCUSDT and ETHUSDT perpetuals, source config window100, daily, equal-gross-normalized long/short weights, threshold.02, stop-.05, fee.0001, no parameter search. This is distinct from directional TrendRider and from spot-perp funding carry.

Preflight only: run original pair class on genuine Binance daily BTC/ETH Jan2024–Dec2025 with original config, examine executable accounting before considering profitability. Use A217 SHA-verified real UM daily data; no synthetic return series. Test whether original reports funding/mark/liquidation, whether constant weights imply uncharged rebalancing, terminal closing costs and signal-close fill timing. A missing essential execution/cost ledger yields BLOCKED, not an economic loss claim and no tuning. No full PnL or VERIFIED claim from a deficient cost model. If preflight fails, preserve diagnostics and move to another independently sourced mechanism; do not silently repair this original.
