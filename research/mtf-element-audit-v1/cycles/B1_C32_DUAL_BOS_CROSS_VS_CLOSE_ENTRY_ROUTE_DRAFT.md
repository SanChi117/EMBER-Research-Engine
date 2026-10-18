# B1 / C32 — implement TWO explicit 3m BOS entry-time paths without inventing fills (WIP)

**Status:** SOURCE-DERIVED DESIGN ONLY [~]. No code or acceptance yet. No author positive BOS goldens / No live orders. PAPER ONLY · NOT_TRADE_READY. Preserve all historical C20–C31 source receipts and append-only A001–A101 unchanged.

## Evidence that forced this design

Direct instructor [4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) recognizes two distinct possible entry mechanisms:

1. **Immediate market entry when price crosses a selected BOS level**, after correct 1H fractal wick raid and LTF BOS reaction.
2. **Wait for BOS candle confirmation, then use a limit order** (with exact price/mitigation rule not established by text alone).

C31 full 45 original futures ZIP observed 539 strict C21 first **close** breaks; in **122 of those** there was a *previous source 3m candle* whose **wick** already crossed the same retrospectively chosen C21 swing, without 3m settlement across it. This does **NOT** prove 122 missed trades: original tick order, spread, author-selected 3m swing, crossing fill, valid session and FTA remain unknown. But it **does** disprove equating 3m first closed BOS trigger time with first price touch of that same pivot. [C31 original source report](B1_C31_ORIGINAL_BOS_WICK_VS_CLOSE_SOURCE_REPORT.md).

External internet examples in [provenance audit](B1_C31_PUBLIC_BOS_EXAMPLES_SOURCE_PROVENANCE.md) show materially different MSS/BOS/FVG definitions and even strict vs relaxed rule sample counts. Their author entry rules cannot fill gaps in our original academy.

## Proposed explicit event-state contract (no signal or order)

`PREKNOWN_1H_FRACTAL` → `CLOSED_FRACTAL_WICK_RAID` → `LTF_REACTION_OBSERVED` → `AUTHOR_SELECTED_3M_BOS_SWING` → route split:

| Entry route | Exactly what must become known | Impossible to prove from 3m OHLC alone | Fail closed |
|---|---|---|---|
| MARKET_AT_BOS_CROSS | true time-ordered tick/price crossing of the chosen BOS pivot AFTER confirmed raid, and no prior invalidation | tick-time ordering relative to stop/FTA, bid-ask fill, slippage; 3m candle HIGH/LOW only witnesses price reach | `NEEDS_TICK_SOURCE_AND_AUTHOR_PIVOT` |
| CLOSE_THEN_LIMIT | complete closing of selected 3m candle beyond author BOS pivot, followed by author-defined valid limit/retest zone, no target/SL violation | exact author limit price, partial fill, intra-bar order, price return to level | `NEEDS_AUTHOR_LIMIT_RETEST_ZONE` |
| BOTH | If one route succeeds/exists, cannot silently create the other route or declare a trade | neither fill nor user permission is implicit | `NOT_TRADE_READY` |

**Shared source blockers:** direct instructor-labeled *chosen* BOS swing vs C21 latest 1+1 strict proxy, precisely attributable reaction after local raided HTF pivot, 1H raid pivot freshness given correct source IANA timezone, exact reaction/FTA and target, author-selected stop buffer. 2023 original [Notion BackTest](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) user and assistant cannot presently access. Do not fabricate charts or missing labels.

## Negative-first tests before any future integration

1. Reject BOS pivot not yet confirmed by next/right-hand 3m bar; reject a 3m BOS that precedes relevant 1H wick raid or completion gate.
2. Reject BOS pivot on wrong side of HTF swept BSL/SSL.
3. Reject body 1H liquidity pass and equality as clean fractal wick raid.
4. Reject market-on-cross route from bare **3m OHLC**; even an earlier lower wick does not supply actual tick order or valid fill.
5. Reject close route when wick only crosses but 3m candle closes back on wrong side; never treat wick as confirmed close.
6. Reject limit order without source-certified retest price, validity duration, chosen BOS swing/author session.
7. Reject late BOS after stop/raid-extreme invalidation; stop and TP first in same bar -> source tick-order UNKNOWN, not inferred.
8. Reject FTA ranking if multiple valid preknown IMB/RB/SNR/BSL/SSL obstacles and no author disambiguation.
9. Fail closed for absent 2023 author goldens instead of silently substituting public ICT MSS or FVG.
10. Preserve no-money-execution terminal boundary; any study output `PAPER_ONLY`, `NOT_TRADE_READY`, with source SHA and exact as-of.

## Acceptance only when author evidence exists

Prioritize finding author positive/negative examples or an authorized export. Make **source→author label→3m timestamp→selected pivot** mapping per example, independently adjudicate divergence with existing C21/C31 technical proxies. Then run 45 original ZIP only on valid same-instrument/time research scope, real tick replay only if an actual tick stream exists; no proxy repaint from 3m OHLC, no live orders. Record independently successful CI and append-only A102 only after testable source evidence. This is not an instruction to install a trading bot or apply live positions.
