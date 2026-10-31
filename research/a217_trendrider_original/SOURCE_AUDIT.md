# A217 original source audit — 2026-10-31

Pinned source commit e67bbb1e1826a5cd582abc6d098e03e7fd4de256 / blob b7d013a802b45d2dd1cb0b91d4083fb247efac75. Public v2.12.1 differs from private later versions and their reported outcomes. Do not transfer author's v2.17 PnL to this code.

Native Freqtrade2026.4 resolver loads original embedded buy_params: ema_fast9, ema_slow16, rsi_period16, pullback30–65, bounce35, ADX20, volume1.3; rsi_exit78. These override several IntParameter default values. No adjacent JSON imported.

- Long-only 1x futures supported by leverage callback and BTC/USDT:USDT informative identifiers. No spot test.
- Stoploss -0.06, use_custom_stoploss=False: comment claiming ATR override is false. Trailing3% after5%; ROI6%/3.5%/2%/1%/0 at 0/60/240/480/720min. Custom loss cuts remain original.
- Six entry branches (trend_pullback, ema50_bounce, rsi_bounce, ema_crossover, bb_bounce, macd_reversal). Only first branch uses daily EMA200 as hard entry gate. Confidence callback uses other context. No blanket claim of daily trend filtering.
- Native default order types entry/exit/stoploss=limit, stoploss_on_exchange=False. Candle touch fill is an assumption; no claim of guaranteed live fill, queue priority or protected exchange stop. Fee stress is not an orderbook simulation.
- Public original hardcodes FNG50 and signal-side funding0/OI0. These are neutral source constants, not genuine macro inputs. Actual settled Binance funding is separately charged by native futures engine.
- informative merge uses native merge_informative_pair (closed HTF bar alignment). No visible negative shift or centered future-gradient. Prefix tests still required; static review is not causal proof.
- confirm_trade_entry uses native analyzed-data slicing; custom_exit uses current modeled profit and duration. Original send_msg methods execute only into disabled/offline messaging path; Telegram and API server disabled. No exchange keys supplied.
- Protections enabled in test. Each independent pair has its own guard wallet; this is not a common live four-pair portfolio.
- startup_candle_count=210. Download includes 2023 warmup for first 2024 interval; native loader controls actual used history. Recursive stability still requires audit before promotion. No strategy parameter edited to improve warmup outcomes.

Earlier economic failures remain unchanged. A204 scalp tempo/leverage constraints are obsolete under locked mandate, not reintroduced here.
