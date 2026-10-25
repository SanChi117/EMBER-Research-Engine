# C77 — original 1H source audit

Date: 2026-10-26. Starting accepted checkpoint C76/A146.

Original Binance USD-M: 45 ZIPs, 5 assets, September 1–October 2 2026. Independent CI 40241597663 succeeded on real 3m/15m/1d market sources. Unit checks: 34 tests each on Python 3.10, 3.11, 3.12.

C73 source contexts: 153 = 47 without selected new 1H POI + 71 unselected/opposite or ambiguous C67 contexts + 35 selected 1H source patterns (28 RB, 7 SNR). All 35 selected source patterns satisfy original C62 construction and raw 3m first visit/episode chronology. No selected IMB in this subset. The earlier naive audit incorrectly treated all 153 as selected; the strict source inspector was not weakened. Separate JSON evidence preserves the forensic counterexamples and the corrected branch-aware audit.

Primary course Rejection Block requires wick-only liquidity raid or prior IMB interaction, and Entry by IMB & SNR requires a first author-valid POI test before later confirmation. The source pattern alone does NOT prove author validity, 15m Trigger/VC, 5m VC, StrongHL, SL/TP or profitability. Route B/C and V5/QFVG unchanged. No orders, fills, trades or PnL. PAPER ONLY; NOT_TRADE_READY.

Sources: evidence/c77/C77_FRESH_ORIGINAL45ZIP_BRANCH_AWARE_POI_REPLAY.json and evidence/c77/C77_NAIVE_FORENSIC_COUNTEREXAMPLES.json. Next: independent replay/final SHA acceptance and historical CI fixes.
## Independent C77 acceptance evidence (26 Oct 2026)

Second fresh original45ZIP replay GitHub Actions #40242209632: SUCCESS,
full C77 frozen market result 8,148 bytes byte-identical to repeat,
SHA256 170ffad3d49af83324ea3da12d031c2f53842bf7e1604cee6b1bfb9f4f01e394.
The second run retained 45 original ZIP provenance; 3m->15m parity holds.
The 15 historical final independent CI workflows C59-C73 were corrected
to run pinned A129-A143 source commits instead of accidentally running
old exact-length assertions against a longer current journal. All 15
replayed final historical Actions successfully. Current full journal
integrity remains checked separately, not disabled. See
evidence/c77/C77_HISTORICAL_CI_C59_C73_PROOF.json and
tests/probe_c77_historical_ci_archives.py.
C77 independent tests + source proof x Python 3.10/3.11/3.12:
GitHub Actions #40242587647 SUCCESS.

No AUTHOR_VERIFIED signal, no live execution; statuses unchanged:
PAPER ONLY / NOT_TRADE_READY. This report is part of the A147 evidence
set, while the permanent SHA-journal will be appended separately.
