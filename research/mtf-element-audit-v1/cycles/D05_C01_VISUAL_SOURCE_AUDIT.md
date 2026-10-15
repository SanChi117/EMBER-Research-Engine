# D05/C01 — Academic image-source inspection and fail-closed golden-case gate

Date: 2026-10-15. Status: `SOURCE_IMAGES_FOUND / NUMERIC_GOLDEN_CASES_NOT_ATTESTED`.

## What was read

Authenticated original Google Drive lesson source text for BOS, IDM, Strong High/Low, FVG, OB, RB, SNR, Order Flow, POI, session liquidity and Premium/Discount. Also inspected the six source screenshot PNG files **at original 4480x1440 resolution**:

- `VIS-BOS-2102`: screenshot of Notion notes + conceptual diagrams; the actual underlying trading-time geometry cannot be dated.
- `VIS-SHL-2143`: academic conceptual strong high/low line diagrams with BOS/contact; **not** symbol + price-axis source.
- `VIS-SHL-2144`: conceptual candlestick examples with Raid/Strong HL labels; no independently readable time/price axis.
- `VIS-IDM-2098`, `VIS-IDM-2099`, `VIS-IDM-2100`: Notion pages with 4H/1H/15m trading-chart thumbnails. Visible parent context and lower-TF placement, but actual price/TF candle timestamps and zone limits are too small to reproduce against OHLCV.

File IDs, original Drive references, full-screen byte SHA256 and status are preserved in `research/mtf-element-audit-v1/d05/C01_VISUAL_CANDIDATES.json`. All six remain `NEEDS_NUMERIC_CHART_SOURCE` or `SCHEMATIC_ONLY_NOT_GOLDEN`. No OHLC candles or coordinates were fabricated from thumbnails.

## What was actually implemented (quality gate, NOT strategy logic)

`d05/semantic_label_gate.py` defines an independent fail-closed verification boundary for chart labels: source URI, exact image SHA, source section, original author numeric chart classification, symbol/futures market, TF, timed event and as-of decision, valid price bounds, route ID, explicit positive/negative case type, and pending independent review. A case with syntactically valid metadata remains `SCHEMA_VALID_NEEDS_INDEPENDENT_VISUAL_REVIEW`, **never** `APPROVED_ACADEMIC`.

`d05/test_semantic_label_gate.py` contains 10 negative/positive *schema* tests: rejects screenshot thumbnails as original numeric chart, future event, broken zone geometry, corrupted image hash, Spot market, missing explanation for negative, self-approval and source omissions.

GitHub Actions: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38751579043 — **SUCCESS**, `10 tests`, `OK`, explicit `D05_SEMANTIC_SIGNOFF_BLOCKED_UNTIL_NUMERIC_SOURCE_CHARTS`.

## Attempted falsification

A complete metadata dictionary **can** be internally consistent even when source image is fictional. The D05 validator therefore does **not** and must **never** grant academy truth by passing schema. Independent source-image recognition with actual price/time, author lesson and chart replay remain separate. Current source capture set cannot support that.

## Next acceptance requirements

For each applicable one of the 45 IDs: recover original chart crop/bytes, asset, TF, timestamp, actual price-axis object bounds; connect to lesson paragraph/figure; annotate one valid and one invalid market example; ensure bar-closed event `known_at`; reproduce on exact Futures history without future suffix; add price-lineage causal test; only then grant a scoped semantic approval.

No live trading, no model parameter tuning, no change to V5, QFVG or working SMOKE.
