# C08 — independent full 315-archive Binance USDⓈ-M provenance: ACCEPTED within defined scope

**Date:** 2026-10-15. **Mode:** PAPER RESEARCH ONLY. **No trading core or terminal edits.**
**Verified GitHub Actions run:** https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38750996053
**Run HEAD:** `42ff29aa5e7effe6ad0aab8c87877d9e126b2c1f`.
**Status:** `FULL_315_ATTESTED` — all 315 declared raw ZIP sources in the frozen C08 history manifest passed independent per-file validation.

## Result and evidence boundary

- 5 isolated GitHub Actions shard jobs **SUCCESS**: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT.
- **63/63** original ZIP sources for each symbol, **315/315** unique source URLs across the frozen manifest.
- Each source fetched over HTTPS from the strict `data.binance.vision/data/futures/um` allowlist together with its `.CHECKSUM`; raw ZIP SHA256 revalidated, metadata/expected row count/time-grid/OHLCV checked through original `strict_vision_d04.verify_raw_zip`.
- **Each raw candle individually checked** against the frozen normalized CSV: eleven mapped numeric fields `open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base_volume, taker_buy_quote_volume`. The extra raw ignored Binance field is not used. Symbol is checked in normalized history.
- All 315 received `HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED`, no mismatches/quarantined sources in this 315-source set.
- Frozen trade core SHA guard PASSED (legacy file digest unchanged).
- Preflight unit chain: `139 tests`, `OK (skipped=1)`; separate accepted D05 checks are a different run, not to be added as trading semantics.
- Aggregator output: `unique_sources=315`, `verified_archives=315`, `quarantined_or_unverified_urls=[]`.
- Aggregate job **SUCCESS**; manually re-opened five downloadable source-receipt artifacts and rechecked **63 per file**, unique 315 URL and all eleven fields indicated as matched.

## Original GitHub Actions proof artifacts

| Symbol | Number | Artifact ID | Raw JSON SHA256 (downloaded and independently computed) |
|---|---:|---:|---|
| BCHUSDT | 63 | `11980404893` | `93e084c42bba50b3a112486444dc5de878ba12fa4168dbb0970b22e63f54b1af` |
| BTCUSDT | 63 | `11981701338` | `9d2079325a24c863e4e3c4157003de742d9279dd007e1cc6c4c3c16e66daec48` |
| ETHUSDT | 63 | `11981147605` | `08debff6e3c69a3ccb6925e07f4297818a41d988d4b6cf5d357089562aa7e4d1` |
| SOLUSDT | 63 | `11980782897` | `84d83e7165cb734dfe040ad0366c99cca1c2f2ce474bff65b4f5f8bbd83d095a` |
| XRPUSDT | 63 | `11981416321` | `0d3f6d4ec7d6ba74ceb04cd987357437a18e7bc3a74518a33dd29850da378107` |

Aggregate artifact `11981636644`, original 580-byte `c08-aggregate.json` declaring FULL_315_ATTESTED. These GitHub Action artifacts have a retention window; preserve canonical textual receipts separately, rather than relying only on this link.

## Crucial non-claims / falsification attempts

1. **No cryptographic Binance signature.** The `.CHECKSUM` comes from the *same* HTTPS origin and depends on TLS/CA and host integrity. This is independent HTTPS validation versus the previously local manifest, not third-party notarization of historical trades.
2. **No semantic market-pattern approval:** neither BOS nor IDM nor StrongHL/POI/FTA was checked by these tests. As of this cycle, independently price-scaled course chart examples accepted = **zero**.
3. **Jan 29, 2025 conflict remains quarantined.** The separately verified BTC 15m/1d volume mismatch in C07 is not resolved by this run; do not interpret `315 PASS` as removal of the existing separate 2025 source anomaly.
4. **No live order execution claim.** All historical data work; no Spot, keys, exchange orders, PnL recalculation or parameter fitting.
5. **Two CI assertion/format failures and one broken YAML publication were preserved in GitHub history** before the clean C08 run. They were CI harness errors, not hidden strategy errors. Final clean workflow from original commit with corrected 139 test and `OK (skipped=1)` acceptance was verified.
6. Automated row matching is a test of data provenance and normalization. It does not prove real-time latency or that the future exchange feed would have exactly matched the archive at historical execution time.

## Acceptance verdict

**D04 C08 scope FULL 315/315 ACCEPTED FOR RESEARCH HISTORY PROVENANCE** subject to the trust limits above.
Advance to **D05 source/geometry semantics** on course-labeled evidence. Keep existing route-v0.4 negative returns immutable, do not run fresh profit optimization before semantic approvals.
