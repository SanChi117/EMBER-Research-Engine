# C75 — external adaptation of missing IMB/FVG geometry and first-return lifecycle

**2026-10-26, Binance USD-M crypto research; PAPER ONLY / NOT_TRADE_READY.**
Started from independently accepted C74/A144 tip `6fb263fbf4661fe47a34334f175466d58277dbbbf9359b2fc3f7319b4d07ce3d`.
Nothing from frozen C46–C74 was edited.

## Academy first, then external adaptation

The original Google Drive course `2. Entry by IMB & SNR.txt` defines the causal Route A
fork and original `Rejection Block.txt` requires the first POI test. Their definition
and timeframes remain controlling.

Two researched third-party sources provide an **independently implementable technical geometry**
for a three-candle FVG/IMB:
- https://cmcmarketsfunded.com/learn/fair-value-gap/
- https://github.com/SrsBlack/ict-knowledge-library/blob/master/concepts/06-fair-value-gaps/fair-value-gap.md

Both use first/third candle wick bounds, bullish `low_3 > high_1`, bearish
`high_3 < low_1`. This is *compatible* with existing strict IMB geometry
but is neither author authentication nor evidence of an edge. No outside source
is accepted as authority for placing a trade.

No-lookahead engineering: https://www.tradingview.com/pine-script-docs/concepts/repainting/.
Archive provenance requirements: https://github.com/binance/binance-public-data.
The provider's ZIP CHECKSUM is same-host, not an independent signature.

## Actual implementation

- Isolated `d05/c75_external_imb_first_visit_lifecycle.py`:
  typed source adapter for already-validated C21 original native3m,
  C72 original native5m and C16 original native15m. Exact Decimal OHLCV,
  correct timestamps, contiguity, source-row ID format and known-at
  cutoffs; do not claim the module independently authenticates ZIP bytes.
- All closed 3-bar FVG geometry is discovered only upon third bar closure.
  Revisit episodes count only AFTER full formation, without bar-by-bar
  double counting or future reaction. Full close beyond far edge marks
  technical candidate invalidation, never an assumed fill/SL/trade.
- Route A `classify_c73_fork` keeps the 15m Trigger vs 15m VC fork
  **UNRESOLVED**, no Route B IDM or C Raid/BOS crossover. Every candidate
  bears `ADAPTED_HYPOTHESIS`; all author gates false.
- Registry `evidence/c75/C75_EXTERNAL_ADAPTED_RULE_REGISTRY.md` marks
  AUTHOR_RULE / ADAPTED_HYPOTHESIS / REJECTED / DEFERRED and
  identifies next-stage conditions for adaptation review.
- Independent static verifier `tests/probe_c75_frozen_original60zip_adaptation.py`
  hashes C73's exact frozen 303,327-byte source then independently
  classifies all 153 source contexts: 141 insufficient, 9 first
  continuous POI visit, 3 separate repeat visits. Every one remains
  source-only with 0 author Trigger/VC, 0 author goldens or trades.

## Falsification and independent tests

- **39 negative/positive source-and-counterexample tests on each of
  Python 3.10 / 3.11 / 3.12**, including actual dataclass paths for all
  three candle periods; future candles, missing/duplicate bars, bad
  SHA-ID, symbol/TF mixing, impossible/NaN OHLC, gaps of zero width,
  first return versus second return, invalidation, forged author flags
  and artificial entries.
- Independent C75 workflow [CI #40237156704](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40237156704):
  **SUCCESS 3/3, 39 tests per interpreter**. General CI on code
  change also checked separately. Previous 144-entry journal verified
  during C75 tests.
- Original 60 market ZIPs **NOT freshly redownloaded** in C75.
  Old C73 provenance is checked by pinning its raw evidence digest only.
  Synthetic OHLC test fixtures are not presented as Binance-market cases.

## Remaining blocker

The course has no identified author-labelled positive/negative Binance
cases for actual valid POI first test, eligible IMB Trigger versus
actual SNR/IMB Volume Confirmation, 5m VC, genuine structural
StrongHL, FTA/SL/TP. No proof of winrate, any alpha or trading edge.
The internet adaptation is compatible **geometry only**, intentionally
never AUTHOR_VERIFIED or TRADE_READY.

Next C76: independent source-bound FVG lifecycle on **real original
candles** (including first vs revisit under 1H parent), static semantic
crosscheck with RB/SNR and without nested IMB; keep independent A/B/C,
counterexamples, exact source SHA + timestamps, and PAPER-only execution.
