# C77 — original 1H source audit

Date: 2026-10-26. Starting accepted checkpoint C76/A146.

Original Binance USD-M: 45 ZIPs, 5 assets, September 1–October 2 2026. Independent CI 40241597663 succeeded on real 3m/15m/1d market sources. Unit checks: 34 tests each on Python 3.10, 3.11, 3.12.

C73 source contexts: 153 = 47 without selected new 1H POI + 71 unselected/opposite or ambiguous C67 contexts + 35 selected 1H source patterns (28 RB, 7 SNR). All 35 selected source patterns satisfy original C62 construction and raw 3m first visit/episode chronology. No selected IMB in this subset. The earlier naive audit incorrectly treated all 153 as selected; the strict source inspector was not weakened. Separate JSON evidence preserves the forensic counterexamples and the corrected branch-aware audit.

Primary course Rejection Block requires wick-only liquidity raid or prior IMB interaction, and Entry by IMB & SNR requires a first author-valid POI test before later confirmation. The source pattern alone does NOT prove author validity, 15m Trigger/VC, 5m VC, StrongHL, SL/TP or profitability. Route B/C and V5/QFVG unchanged. No orders, fills, trades or PnL. PAPER ONLY; NOT_TRADE_READY.

Sources: evidence/c77/C77_FRESH_ORIGINAL45ZIP_BRANCH_AWARE_POI_REPLAY.json and evidence/c77/C77_NAIVE_FORENSIC_COUNTEREXAMPLES.json. Next: independent replay/final SHA acceptance and historical CI fixes.