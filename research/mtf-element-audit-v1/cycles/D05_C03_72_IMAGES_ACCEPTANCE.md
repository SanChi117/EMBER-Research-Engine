# D05/C03 — acceptance of the final 58 source image inspections (NOT model semantics)

**Date:** 2026-10-15. **Mode:** PAPER ONLY. **Status:** `72/72 SOURCE_IMAGES_INSPECTED; 0/72 INDEPENDENT ACADEMIC FUTURES CHART CASES APPROVED`.

## Evidence and what was done

Read C02 frozen source inventory and fetched remaining **58 original Google Drive PNG files**, keeping Drive file IDs and computing SHA256 on the retrieved **original bytes**. Visually reviewed all 58 in their original or contact-sheet forms, including enlarged checks of potentially useful price-axis charts. The preceding C02 reviewed 14 image binaries. **72/72 source images from the eight C02 teaching folders now have a classified, referenced source record**, with C01/C02 original proof files not overwritten.

New records: `research/mtf-element-audit-v1/d05/C03_58_IMAGE_REVIEW.json`. They contain the stable source URL, binary SHA, expected file size, thematic lesson group, exact category and limitations.

| New classification | Images |
|---|---:|
| Desktop teaching-page screenshots with small embedded charts, no replayable axes | 26 |
| Cropped candle fragments without complete venue/TF/time/price evidence | 22 |
| Unscaled academic candle/line schematics | 6 |
| **EURUSD OANDA original screenshots with visible TF and numeric axes** | **3** |
| Price-axis graphic without independently known symbol/TF | 1 |
| **Total C03 additions** | **58** |

Earlier C02 contained 3 EURUSD charts with a readable price axis. **Six** source Forex chart figures are now price-scaled and venue-labelled across C02+C03, but none has raw author-exchange candles with individually verified `known_at`.

The new three came from **TDA**, filenames:
- `Untitled (25).png`: original EURUSD **1W** OANDA TradingView teaching reference, `Daily RB`, image ID `1xRwHSdeGPh-EdsAYNblHY_WVYbihA7mq`.
- `Untitled (26).png`: EURUSD **1D** OANDA teaching chart with Daily RB and contextual liquidity, image ID `1bW_s5gSwq9-LLZehoeUjxAFZotDygix-`.
- `Untitled (34).png`: EURUSD **1H** OANDA source teaching chart with `4H IMB [from]`, `1H Trigger [fractal]` and `4H Target [to]`, image ID `1XeyRLeQOwMNlcPw3wWLzNfPF0zqamC0U`.

Additional relevant graphic: `POI/Untitled (10).png` (Drive ID `10eGpOY9DkYpV1vbbOymoWZ0PaSCvI_GX`) visibly illustrates a `Raid 1H SSL` → `IMB` reaction and an apparent price scale. Instrument and **chart timeframe** are not independently identified, so status `PRICE_AXIS_MARKET_TF_UNKNOWN`, not course-attested.

A TDA source chart `Untitled (37).png` depicts **4H fractal raid → 1H RB new POI → 15m trigger → 5m VC**, but is a cropped chart with no verified symbol/time/price scale. It supports teaching hierarchy, **not numeric replay**.

## Tests and attempt at falsification

GitHub Actions run [38779488935](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38779488935): **SUCCESS** with **35 tests**, combining the original 10 D05 schema tests, 12 C02 source tests, and 13 C03 source-contract / mutation tests. The suite catches missing source ID, duplicate assets, malformed SHA fields, false Forex→Futures relabeling, fabricated numerical approvals and inconsistent counts.

The initial construction of the C03 index caught a **54/58** completeness error; the first published raw C03 version also contained **four shorthand, invalid image digests** for POI images 6–9. The exact hashes were recomputed from fetched bytes and corrected in commit `45f151554176b653ade39540184028137dc96233` **before** independent C03 Actions PASS. Old mistakes remain visible in Git history; not rewritten as successes. CI tests validate the new source metadata **internally** and do not download all Drive original PNG bytes on the runner. Therefore source SHA values are based on local original-byte download; they have **not** been independently re-fetched by Actions.

No original course image was rewritten or reannotated to match an intended signal. The 2025-01-29 BTC volume discrepancy remains quarantined separately in C07.

## Strict acceptance and next dependency

**ACCEPTED within the explicitly narrow scope:** completeness of image candidate inspection, SHA-linked catalogue, grouping and fail-closed eligibility checks.

**NOT ACCEPTED:** any price/volume market replay against original EURUSD OANDA candles; identifying missing exchange/TF on the seventh figure; automated BOS/IDM/StrongHL/POI/IMB/SNR semantics; PAPER signals or performance. `ACADEMIC_APPROVED` cases = **0**.

Next task D05/D06: map the six **Forex** course visuals to independently sourced OANDA/SAXO historical OHLCV where legally and technically obtainable, keeping a separate label `ACADEMIC_COURSE_FIGURE_REFERENCE` versus the Futures-only trading execution `FUTURES_VALIDATION_CANDIDATE`. If inaccessible, set `NEEDS_DATA_SOURCE`; independent Binance Futures case must be labelled from an author-defined rule with actual Binance OHLCV, not falsely copied from EURUSD.

Unchanged: C07/SPEC status register, preserved raw source receipts, D01–D04, mtf_engine frozen SHA, SMOKE OS, V5, QFVG, AppDeploy, live keys, exchange trading. No changes to trading logic.
