# B1 / C27 — Academic target families and FTA source gap (PRELIMINARY / NO ACCEPTANCE)

**Status:** [~] source discovery ONLY, NOT an accepted research cycle. No A097 record, no new algorithm, no source-pinned CI, no positive/negative author-labelled Binance Futures cases. PAPER ONLY / NOT_TRADE_READY. Do not change C26's pinned JSON or earlier receipts.

## Exact source documents reopened via Google Drive (2026-10-18)

1. [4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): academic model HTF liquidity raid -> LTF BOS, often 1H -> 3m/5m; first 1H liquidity is discussed as target. The illustrated SHORT uses **1H EQL** for TP. Notes also favor the prior session high/low as suitable TP; warn that FTA before the raid/target may make RR unattractive (skip); require fresh 1H fractal (previous session or at most previous day), HTF wick raid, LTF BOS, and SL beyond liquidity swept in raid. Entry on BOS crossing versus confirmed-close / retrace limit are **different execution interpretations**. Author's timezone remains unidentified.
2. [ликвидность.txt](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): BSL/SSL are strict three-candle fractals (one lower-high/higher-low candle to left and right, known only after right candle closes). EQH/EQL are **clusters of at least two** swing BSL or SSL, not just one pivot. The text does NOT specify a numeric crypto-tick or price tolerance for clustering. Compression and EQH/EQL are separately named; do not silently merge them. A swept level is distinct from a fresh one.
3. [Strong High & Low.txt](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view): strong highs/lows rely on prior contact with liquidity or inefficiency and evidence through VC POI or BOS; they are NOT all equal to a raw three-bar high/low. Source suggests safe structural stop placement beyond strong high, but does not provide a Binance USD-M numeric stop buffer.

## What C26 does, and what it DOES NOT implement

C26's reproducible 45-ZIP receipt proves: of 165 C24 source-only singleton edge observations, 137 closest HISTORICAL *single opposing 1H fractal* prices had a strict earlier wick/body cross before technical break; 28 did not; 74 had known intermediate single 1H fractal obstacles. This is useful negative geometry, NOT an academic TP classification. No discrepancy with source should be hidden by relabelling EQL as a single fractal.

Before an author-calibrated TP could be selected, these **distinct** hypotheses require source-positive and source-negative examples:

| Target family | Directly supported source constraint | Currently missing for mechanical approval |
|---|---|---|
| Single opposite 1H BSL/SSL | 1+1 fractal is known only after right candle, historical 1H liquidity may be target | Which one author selects when multiple, whether a swept historical price is reused as a POI |
| 1H EQL/EQH cluster | Liquidity course defines >=2 distinct swing levels; BOS lesson explicitly illustrates EQL TP | Exact equal-level price/tick tolerance, cluster birth/expiration; *EQH as target is a candidate extension, not a specifically timestamped author TP case* |
| Previous session high/low | BOS source names previous-session extremum as suitable TP | Author session timezone/DST, session boundaries, which prior trading day/session, whether level already raided |
| Known intermediate reaction/FTA | BOS says poor FTA/RR can invalidate the model | Exact FTA taxonomy (1H fractal vs cluster vs SNR/IMB/POI), strength, ranking, numeric minimum RR |
| Raid/StrongHL stop | Stop goes beyond swept raid liquidity; StrongHL requires confirmation by VC/POI/BOS | Tick buffer, bid/ask/mark/execution rules, precise author-certified raid/strong pivot |

## Adversarial questions that must be tested before any C27 [x]

- A single isolated high cannot be promoted to EQH/EQL merely because it is visually near another swing; no arbitrary 0.1%, ATR or tick equality rule.
- A possible 1H cluster formed using a future right-confirmation candle is NOT known at break.
- A swept historic standalone target cannot become a valid unswept EQL merely by renaming.
- A supposed previous-session high/low must remain UNKNOWN until author's timezone and DST policy are determined.
- Multiple overlapping target families and FTA obstacles must remain separate candidates, not hand-picked to improve RR.
- Forex-specific pip distances must not be converted to arbitrary USD-M price increments.
- A strong high/low must not be inferred from the three-candle fractal alone; source's contact and confirmation prerequisites matter.
- A textbook reaction screenshot does not establish executable live Binance trade, fill or complete author-selected BOS pivot.
- Neither 137 negative cases nor 28 source-intact cases represent trade results, expectancy, or percentage profitability.

## Proposed C27 bounded execution order (still NOT performed)

(1) Pin primary text versions and source→exact-clause index without copying old evidence retroactively; (2) distinguish typed target candidate families with `NEEDS_AUTHOR_EQH_TOLERANCE`, `NEEDS_AUTHOR_SESSION_TIMEZONE`, `NEEDS_AUTHOR_FTA_CRITERION` statuses; (3) build fail-closed negative tests and price causality; (4) original 45 ZIP source replay; (5) attempt to falsify classifications and compare to C26 without overwriting it; (6) immutable receipt, independent source CI, new A097 only after success, map update only then.

**Academic dependency blocker:** original author-labelled positive and negative USD-M 1H raid→3m BOS examples with pivot, time, instrument, previous-session timezone and actual reason for selecting target/FTA are not available. Keep B1 [~], Routes [ ], PAPER ONLY.
