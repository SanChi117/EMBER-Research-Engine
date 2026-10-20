# EMBER B1/C34 — instructor BOS text audit and negative-only source gate

**Scope:** source audit and reject-only textual rule mechanics, not price data detector or author-approved entry. Source search and unit tests, not a new crypto setup. **PAPER ONLY · NOT_TRADE_READY**. Previous C20–C33 original 45 ZIP, source SHA and 103 ledger events immutable.

## Original lessons actually reviewed — source provenance

Search on user's authorized Google Drive for `BOS`, `Entry`, `BackTest`, `Fractal`, `Break Of Structure`, `рейд`; directly read:

| Source | Author-stated information relevant to C34 | What source does **not** prove |
|---|---|---|
| [4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view), **PRIMARY** | After HTF liquidity raid and reaction, LTF 3m/5m BOS (typically 1H raid → 3–5m BOS); HTF BSL raid wick requires BOS **below** swept liquidity; HTF SSL wick requires BOS **above**. Market on price crossing OR closed candle then limit are distinct. TP to first 1H liquidity/opposite previous session target. SL behind swept liquidity; fresh prior-session/day fractal; avoid case if target absent, first FTA blocks acceptable RR, no actual raid, or 3m BOS absent. Mentions trading hours 09–17 and 15-pip FX stop risk caveat. | Exact chosen 3m BOS swing when multiple strict 3m pivots preexist; symbol/bar timestamps of trade examples; actual cross tick/fill; crypto-specific pip meaning; IANA timezone DST and source FTA priority among multiple obstacles. |
| [2. Entry by IMB & SNR.txt](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view), **different entry route** | 4H POI→1H trigger→15m volume confirmation or 1H POI→15m trigger→5m VC, 1H/15m trigger with IMB/SNR, target and stop nuances. | These LTF IMB/SNR 15m/5m methods are NOT a definition of the BOS 1H→3m swing. |
| [3. Entry by Inducement [IDM].txt](https://drive.google.com/file/d/19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs/view), **different entry route** | HTF VC/strong high/low, limit entry at IDM liquidity/trigger on one lower TF; target FTA at originating POI TF. | Cannot import IDM's direct limit trigger into BOS close-then-limit as if identical. |
| [ліквидність.txt](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view), [3. Rejection Block.txt](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view), [Context/TDA](https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view) | Previously surveyed native 1H fractal / first-wick raid and separate IMB/RB context or first trouble area / target. | No complete numeric author ranking that identifies a single 3m BOS pivot or source labeled chart. |
| [Entry By BOS folder screenshot "Снимок экрана (2102).png"](https://drive.google.com/file/d/1DjAUNwDiNmr3a_ySSreSdtfBzVCWZPaZ/view), **source visual inspected** | Desktop screenshot displaying original Notion *text* of BOS rules and schematic RAID/SL drawings. | No identifiable instrument/date/time, no labelled actual author 3m swing price; cannot map to 2023 historical bars or 2026 USD-M source. |
| [Entry Model Logic "Снимок экрана (2092).png"](https://drive.google.com/file/d/1Yv1Q--0aKYGqVHYlBNdTEFHtXg-04r79/view) and ["(2093).png"](https://drive.google.com/file/d/12k5YK1GyzeIT1oFXpnVFKNL-zvKFTXOX/view), **source visuals inspected** | Screenshots show Notion multi-TF examples of **IMB/SNR 4H/1H/15m/5m** logic. | They are not author-positive BOS 1H/3m screenshots; can't ground exact 3m BOS pivot. |

Course explicitly refers to [BackTest 1H/3M 2023.01–2023.07](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21), which both user and public search couldn't access. Direct Drive title and ID search found only its hyperlink in lesson. Never claim source permanently missing or replace original cases with independent ICT examples.

## Concrete negative-only implementation, no authored BOS pivot positives

`d05/c34_author_bos_text_negative_gate.py` and `d05/test_c34_author_bos_text_negative_gate.py` encode **only explicit instructor conditions for INVALIDATION**:

- BSL raid → selected BOS lower than source raid level, SSL raid → selected BOS higher; price equality fails strict directional condition.
- True **wick** 1H raid, not body cross or price falling short of fractal; 3M BOS must actually exist as scenario premise. Missing target / first FTA makes RR unattractive → skip.
- Selected stop must sit beyond liquidity extreme of actual raid; no guesses for buffer from course's 15 **pips** on a different market.
- Source reaction, zone geometry, first FTA order, session IANA timezone/DST, author selected pivot and 2023 positive/negative labels remain **UNKNOWN**. A caller can only supply hypothetical flags; this module does **not** fetch or verify source market data itself.
- Even when every hypothetical condition satisfies geometry, **NEVER** upgrade to author approval / paper signal / market / limit order / actual trade. `available_for_paper_signals=False`, `market_orders_allowed=False`, `limit_orders_allowed=False`, `trades_allowed=False`, `NOT_TRADE_READY`. Forged source-approval booleans cannot override this.
- Unknown inputs yield unresolved evidence markers, **not** fabricated positive/negative market observations.

**38 deterministic source-rule negative/ambiguity unit tests**: 6-way multiple rejection, true BSL/SSL direction, equality, no raid/body-only, no 3m BOS/target, FTA before acceptable target, inadequate stop, unknown case evidence, no selected author BOS, no 3m tick, unknown limit/retest, 15-pip not crypto, invalid Decimal and forged/invalid booleans and session claims. These tests measure local code consistency, **not** market or academic profitability.

## Falsification, evidence and blockers

First CI attempt [39458131235](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39458131235) failed **before any of 38 unit tests**: Git SHA check called `git rev-parse HEAD:evidence/c33/...` after `cd research/mtf-element-audit-v1` although `HEAD:` resolves from Git root. Old A103 103/103 SHA verify succeeded. Workflow source path was corrected; diagnostic `evidence/c34/diagnostics/C34_AUTHOR_BOS_NEGATIVES.json` preserves original skipped result. Do not count this as a negative-test PASS.

**Remaining acceptance for source-text C34 [x]**: successful 38 controls on Python 3.10/3.11/3.12, independent negative-source comparison and SHA/file evidence after immutable source report freeze, append-only A104 and independent 104/104 audit. Does NOT require a new 45 ZIP replay because **this C34 does not introduce or evaluate any market data observations**; previous C33 original source Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df` must remain byte identical. Likewise C34 cannot certify author selected pivot, FTA exact entry, SL buffer or session. The 29/40 major program points remain unchanged; B1 stays [~].

## Next decisive work

**Find or access author-dated positive and negative 1H/3m swing-chart goldens**, or instructor's textual exact definition for identifying a particular 3m BOS pivot after local 1H raid. Then compare source-labeled selected swing against all 5,285 C33 previously known 3m technical candidates, link FTA/SL and entrance variants, and test source time. No arbitrary pivot-strength ranking to disguise absent author evidence.
