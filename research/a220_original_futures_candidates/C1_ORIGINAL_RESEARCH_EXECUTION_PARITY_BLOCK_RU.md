# A220-C1 — parитет оригинала Research ↔ Execution: BLOCKED

Источник [AbdullaE100/perp-quant-lab](https://github.com/AbdullaE100/perp-quant-lab/tree/104dc669084b7f0d0a99748a0f4300950b49930d), commit `104dc669084b7f0d0a99748a0f4300950b49930d`:

- `research/backtest.py` Git blob `cf02c6c525a297112b5f1f594a0ba2a0a1557cf8`: 40-coin panel `prices.csv`, daily rank-weighted factors [XS-MOM L=7,14,30,60,90,120 and ST-REV], long-short gross abs weight sum **2.0**; 5bps taker fee on `w.diff().abs().sum`, *no* funding, slippage, historical availability or liquidation accounting.
- `research/backtest2.py` blob `1ab78864ea632b6ed1469c7781f21f0fa2dec395`: 14d return divided by *30d vol* then ranked; 7 variants compared on the **same OOS** and OOS parameter/result posted. Thus highest OOS Sharpe after comparison is **selection-biased** if used as an untouched winner.
- `scripts/crossmom.ts` blob `94e6db518d6180598beb7728bfbb67f732b4a398`: *different* testnet execution proposal: 6 coins BTC ETH SOL BNB XRP DOGE, **7d** return, top-2 and bottom-2 equal notional, gross **1x**, not the research 40-coin 14d vol-scaled rank portfolio. No matched trade-by-trade research→execution parity. Script even has explicit `--execute` flag; **do not run**.
- `research/fetch.py` blob `a0d8fe281792b2f87b1f66d21bf89b5e32ed1082`: real Binance perpetual source API downloaded separately, with historical funding CSV but not charged in the above research simulation.

**Вердикт: `SOURCE_ONLY / EXECUTION_PARITY_BLOCKED / AFTER_COST_PROOF_MISSING`.** Не считать авторский Sharpe1.62 доказанным EMBER преимуществом. Проверять лишь отдельно пререгистрированную оригинальную *research* систему на true USD-M records, включая funding, bid/ask, time-varying universe и portfolio gross, с независимым хронологическим периодом. Авторский live/testnet скрипт **НЕ является её исполнимым эквивалентом**. Оптимизация окна по OOS запрещена.

Это не отказ от futures cross-sectional momentum как семейства; это дисциплинированное различение источника, отчёта и исполнения. Никаких торговых приказов, никаких изменений действующего PAPER.