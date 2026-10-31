# A217 — frozen original TrendRider futures screen

Mandate: MANDATE-2026-10-31-v1, main blob 6afd84271ec3d07c28d4dc682fcd17eceac22d50; issue 9 read. No change to mandate, live or scheduled PAPER.

Source: darkvolg/Trading commit e67bbb1e1826a5cd582abc6d098e03e7fd4de256, FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py blob b7d013a802b45d2dd1cb0b91d4083fb247efac75. Public v2.12.1, original buy_params/sell_params, no adjacent hyperopt JSON; no strategy edits. Long-only 1x USDT-M, no DCA. This is the untested A210 queue item, not a repeat of failed Donchian or DoubleMA.

Stage 1: audit and native causality/availability preflight with real Binance data. Reject/block if native original cannot run or causal parity fails. No fabricated PnL for failed preflight.
Stage 2 only if stage 1 passes: 2024 and 2025 full calendar years; 2026 Jan-Sep historical validation (not untouched OOS, source selected/published during 2026). BTC/ETH/SOL/LINK, isolated independent $1000 wallets, fixed $100 position. Original stop6%, trailing3% after5%, ROI ladder and custom exits; protections enabled. Native Freqtrade2026.4 reused A199 offline exchange wrapper; metadata is static, not historical exchange certification. 1h decisions, 5m detail; at least 220 preceding daily candles for EMA200; 4h and BTC context as-of closed candles. Real UM trade/mark/funding, SHA receipts and continuity required. Costs 5bps and 12.5bps per side; latter is total-cost stress proxy, not measured spread. No leverage/parameter search.

Acceptance: positive aggregate net in independent years and stressed scenario, report every pair/year including losses and open end exposure; cash benchmark, concentration and marked equity drawdown, adequate sample and interval uncertainty required. Any positive historical screen remains INSUFFICIENT/PROVISIONAL until full execution, liquidation, gap and forward evidence. Separate pair returns are not portfolio returns. Missing data/engine yields BLOCKED, negative economics FAIL. No forced trade count/day or target return.

Reuse A188-A213 negative records and downloader/native infrastructure; A214-A216 explicitly excluded. Historical scalp speed restrictions in A204 are superseded by locked mandate.
