# B1/C24 — fail-closed original 1H raid → 3m BOS research admission

Date 2026-10-17. **PAPER ONLY; NOT_TRADE_READY; zero approved orders**.

## Identified problem and honest limit

Original author [Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) requires an actual HTF 1H wick liquidity raid followed by a suitable LTF 3m BOS below BSL/above SSL, fresh preceding-session liquidity, legitimate FTA/1H target and SL beyond swept liquidity. Their material does **not** identify which one of competing Binance original 3m structural pivots should be selected in 2026, or supply author-labelled positive/negative timestamp cases. The linked 2023 Notion backtest was not accessible, and the source screenshot merely depicts the academy text. We may verify causal original 3m geometry but cannot claim to reconstruct the author's private choice without additional author evidence.

Frozen C21B's **539** researcher-selected original 3m parent break edges included **1,408** previously close-broken swing-level relations (discovered in C23), including **13** cases where C21B's latest selected proxy swing was already broken before the event. C23 correctly reduces the historic **3,393** candidate relations to **1,985** close-intact relations, then to **285** single-first-close and **242** multi-first-close edges, plus **12** no-first-close. C23's 285 singles still include several events on the same original 3m bar linked to different 1H raids.

## NEW C24 enforceable research-only gate

The isolated `d05/c24_bos_research_admission_gate.py` is a pure, read-only admission adapter on genuine original C21A/C21B source. For each original native 3m 1H-raider candidate it:
1. Verifies 3m raw original source IDs, 1H raid close confirmation and only previously known 3m strict fractals.
2. Retires any 3m swing **already crossed by an earlier closed 3m candle** after the swing became known. A prior *wick* excursion remains separately researched (C22A/C23), not silently treated as a proven tick fill.
3. Rejects multiple first-intact crossing levels on the same original native3m candle; rejects missing first-intact structures.
4. Rejects competing 1H raid parent edges anchored to the same original 3m price-break bar instead of choosing the nearest/most attractive arbitrary parent.
5. Even when **exactly one** source-confirmed 3m first-intact pivot and **one** 1H raid parent remain, classifies only **`RESEARCH_SINGLE_CANDIDATE_AUTHOR_SESSION_FTA_SL_UNVERIFIED`**. This is **not a trade signal**; author BOS selection, venue-specific risk/FTA/SL, source-labelled examples, market entry timing remain missing.

These rules are an explicit **engineering first-break and ambiguity policy** and must not be represented as exact author pivot selection. Zero trades in every code path, no exchange connection. Previously frozen C08/C21/C22/C23 receipts remain unchanged.

## Independent five-market native3m original-source replay

`tests/probe_c24_author_bos_failclosed_45zip.py` independently downloads original **45 Binance USD-M Futures ZIP** (15 native 3m + 30 C08 original 15m/1d with .CHECKSUM), re-derives all closed 3m and native 15m equality, asserts as-of independently reconstructed truncated prefix and no hidden future. Original five symbols BTC ETH SOL XRP BCH, 2026-09-01..2026-10-02 UTC, 76,800 original 3m rows and 15,360 source native15m Decimal OHLCV matches.

| C24 status | Number of research parent-edge cases |
|---|---:|
| `REJECT_MULTIPLE_FIRST_INTACT_3M_PIVOTS` | **242** |
| `REJECT_MULTIPLE_1H_RAID_PARENTS` | **120** |
| `REJECT_NO_FIRST_INTACT_3M_PIVOT` | **12** |
| `RESEARCH_SINGLE_CANDIDATE_AUTHOR_SESSION_FTA_SL_UNVERIFIED` | **165** |
| **Original C21B parent edges** | **539** |
| Author-approved BOS / trades | **0 / 0** |

The categories are mutually exclusive per original **parent edge**, NOT per independent transaction or original 3m candle. **374** cases are explicitly rejected for structural ambiguity/no true first break, **165** are *research-unambiguous but still author-unverified*, and therefore **zero** may be automatically traded. These counts prove a deterministic and fail-closed research routing improvement, **not** the uniqueness of any author's BOS decision.

Original source frozen receipt `evidence/c24/C24_ORIGINAL_3M_FAIL_CLOSED_ADMISSION.json` blob `163a0a41a9e5b51320e8f4baaad85cfd0be7c0a9`. C24 source CI [39063728817](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39063728817) **SUCCESS** six new falsification tests and original 45ZIP replay. Follow-up pinned source CI should pass before final acceptance.

## Next independent route C25

Resolve author sessions/timezone/DST and fresh previous-session HTF fractal without importing arbitrary FX/crypto trading hours; original 1H first liquidity target, FTA obstacles, structural SL only using true author-supported numerical definitions. A **timestamp-labelled primary author positive and negative BOS annotated dataset** is still required to certify exact author's 3m swing pivot choice. The unavailable 2023 external course backtest cannot magically be treated as 2026 Binance Futures goldens. Never upgrade author READY on synthetic/chart-inferred evidence.
