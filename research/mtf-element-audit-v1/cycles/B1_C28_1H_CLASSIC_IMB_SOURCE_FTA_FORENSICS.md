# B1/C28 — source-native classic 1H IMB potential FTA (source forensic)

**PAPER ONLY · NOT_TRADE_READY · no author-selected FTA · no author-BOS or live order.** This is a read-only standalone original source experiment. Historical C26 and C27 and ledger A001–A097 remain unchanged. A098 acceptance requires independent full-pinned JSON replay and SHA journal proof.

## Primary author-source evidence recovered (Google Drive)

| Primary course | Verified claim from source text | Operational limit |
|---|---|---|
| [Imbalance / Fair Value Gap](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view) | Classic three-candle inefficiency is the empty price interval **between wicks** of first/third candles; functions as VC, POI and problem area. It distinguishes classic FVG, BPR and inverted FVG. Only the **first POI test** is the trusted test; test depth arbitrary. | No numeric acceptance rule for age, class ranking, mitigation, or priority vs RB/SNR. Do not promote full wick fill to author mitigation. |
| [3. Rejection Block](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view) | RB involves opposite-colored **two candles**, with a raid or IMB test **specifically by wick**; depicts first/second-candle raids and IMB-wick interactions, requires body settlement beyond IMB for particular pattern; zone marked by **wicks**, and first POI test is distinguished. | Plain candle-color flip, generic two-bar OB and any price level without raid/IMB context **cannot be silently called RB**. Diagram-dependent precision not separately source-attested in data. |
| [5. Support and Resistance](https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view) | SNR's sequence includes opposite Buy/Sell candles, SSL raid or FVG test, **new completed candle closing over the level**, then test and reaction; MB is weaker no-raid/no-FVG exception, not normal SNR VC. Unlike RB, SNR raid or FVG test **may involve candle body**. First POI test privileged. | No author-certified bounds or live selection in historical data. No shortcut by treating RB and SNR as the same candle reversal. |
| [Context & TDA](https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view) | 'from FTA to FTA' range and FTA candidates **IMB, RB, BSL/SSL fractal, SNR**, including same or lower TF. | Does not assign first-obstacle priority, expiry, RR cutoff or Binance author labels. |
| [Types of sessions](https://drive.google.com/file/d/1DZ9fClxslV7GkQhIKNS-lh8EksePh3zQ/view) | Asian/session or previous-day liquidity can already be consumed; IMB or fractal FTA may become more relevant than Asia target. | Calendar author timezone/DST unidentified. |
| [4. Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | 1H raid to 3m/5m BOS, illustrated 1H EQL, poor FTA/RR → skip, structural stop beyond swept raid liquidity. | Exact BOS goldens, executable crossing time, entry fill, RR and stop buffer unknown. |

**Important source distinction:** the separate file 'Fractal Break Imbalance / Fair Value Gap / Liquidity Void' is a Pine Script credited to `geneclash`, not proved to be the course author's formal FTA specification. It is deliberately **not** substituted for these lessons.

## New frozen technical-source hypothesis and falsification

`d05/c28_source_fta_inventory.py` detects only **classic three-candle 1H IMB** via strict:
- Bullish: first 1H high strictly below third 1H low, zone `[first.high, third.low]`.
- Bearish: first 1H low strictly above third 1H high, zone `[third.high, first.low]`.
- Both intervals must be strictly positive width; equality is NOT FVG. The third closed hour proves availability, backed by 20 original 3m rows per 1H. No future/partial hours.
- Independently observe zone *first wick touch* and first full wick traversal using original **closed 3m** candles after FVG formation and **before** the candidate break bar. No implied tick order or executable fill.
- Record how often a preknown IMB overlaps the **retrospective** C26 range from later-known research 3m break close toward the historical closest opposite 1H fractal. Range overlap is **not** an author's FTA decision or a valid entry-bar-start forecast: 3m break `close` was only known at the break candle **close**, not at its `start_ms`. This is separately surfaced in every case.
- The output saves all-overlap SHA256 and up to three explicitly labelled illustrative witnesses; the exhaustive catalog is represented by counts and digest, NOT misrepresented by the sample. No automatic TP selection, RB/SNR inferred zones, assumed author class strength, FTA priority, RR or stop distance.

`d05/test_c28_source_fta_inventory.py` contains 22 adversarial controls: bullish/bearish geometry, equality, source row integrity, partial/noncontiguous hours, original price NaN, first-touch/full traverse, future touch/no-lookahead, price-side and strict interval overlap, tamper and false READY, independently truncated native source equivalence and zero approved trades.

## Original 45-ZIP technical price findings (FIRST PINNED RECEIPT)

First source-native replay produced a pinned JSON receipt at `evidence/c28/C28_ORIGINAL_1H_CLASSIC_IMB_FTA_SOURCE.json` (Git blob `ed3aca9384c8e49d07220f04b7d363df92689317`), backed by 45 original SHA-checked Binance Futures USD-M ZIP, 76,800 original closed 3m bars, 15,360 native 15m decimal OHLCV equalities and 3,840 reconstructed 1H bars. On five symbols, the 1H classic three-candle wick-gap observer recorded **646** gap formations. On 165 previous C26 technical singleton cases, there were **10,720 repeated event-to-preknown-gap relationships** (not independent IMB), and **383** positive-width intersections between gap zones and the *retrospective* research entry-close → historic nearest opposing 1H fractal interval; **133/165** cases had at least one intersecting gap. Of 383 intersections, **366** had some earlier original3m wick touch; **220** had a recorded prior full-wick-range traversal; **17** had no earlier wick touch, represented in **16** research cases. Same price gap may be referenced in multiple cases; do NOT count the 383 as distinct trade opportunities.

Per-market independently reproducible gap counts (full 32d original source):
- BCHUSDT 139 1H gaps, 120 interval overlap relations in 39/45 research cases
- BTCUSDT 123 gaps, 61 overlaps in 24/30 cases
- ETHUSDT 126 gaps, 74 overlaps in 20/23 cases
- SOLUSDT 126 gaps, 50 overlaps in 19/30 cases
- XRPUSDT 132 gaps, 78 overlaps in 31/37 cases

**Adversarial interpretation:** A gap passing strict 1H price geometry does NOT mean it would be the instructor's first problem zone, OB, SNR, RB, trade target or entry filter. Even the retrospective overlap interval could not have been known before the BOS break bar closes, and C26 nearest historic 1H fractal itself was already crossed in 137/165 cases. Thus there is no portfolio, realized trade, expectancy, RR or author acceptance inference. The broad lesson requires SNR/RB/IMB/fractal contextual ranking, not a gap-only first target rule.

## Acceptance gate, external dependencies and limitations

The original ZIP replay is `tests/probe_c28_original_1h_classic_imb_fta.py`; frozen target `evidence/c28/C28_ORIGINAL_1H_CLASSIC_IMB_FTA_SOURCE.json`. Replay must preserve C26 and C27 original Git blob SHAs, original 45 SHA-checked Binance USD-M 3m/15m/1d ZIP, 76,800 native3m bars, 15,360 exact Decimal native15m OHLCV checks, 539 C21B parent edges and 165 C24 singleton research cases. First synthetic test run [39123913002](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39123913002) **PASS 22/22**.

**NOT source-certified:** full FTA taxonomy / intrafamily selection (RB and SNR structural conditions), author priority IMB-vs-RB-vs-SNR-vs-fractal, chosen 1H EQL, author liquidity freshness/session timezone/DST, RR cutoff, 3m BOS pivot goldens, SL buffer or trade execution. Accordingly B1 macro stays [~] and Routes E/G/H blocked. No paper or live order.

**C28 can be marked source [x] only after:** complete original 45-ZIP replay, immutable full JSON pin, independent second replay and Python 3.10/3.11/3.12 negative matrix, six new evidence SHA with A098, independent 98/98 ledger verification, main project map update. Until then, [~].
