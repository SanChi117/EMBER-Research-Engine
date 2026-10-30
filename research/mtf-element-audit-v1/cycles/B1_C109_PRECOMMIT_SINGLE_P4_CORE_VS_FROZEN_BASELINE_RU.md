# C109 — конечный проверяемый механизм вместо бесконечной подгонки
Дата: 2026-10-30. До открытия новой выборки. Только PAPER, НЕ обещание прибыли.

## Задача
Перевести обнаруженные в C107 дефекты в одну небольшую, связанную, практически исполнимую систему, **НЕ добавляя «весь LuxAlgo» и не переписывая C105**. C108 строгое единственное H1-child FVG требование было чрезмерно редким и на n2 убыточным; нет оснований «докручивать» на тех двух результатах. Поэтому независимая C109 гипотеза проверяет простую *реальную реакцию на 4H*, а не слабую H1-midpoint и 15m prev-candle break.

## ДВА ПРЕДРЕГИСТРИРОВАННЫХ сравнения; не выбирать лучший после теста
B0: неизменная семантика C105, воссозданная только в переносимом event loop с теми же h4.zone_from_three, h4.first_touch, h4.rejection, h4.vc и h4.parent_plan/simulate. Closed 1H H1 midpoint and closed 15m IMB OR prior single candle breakout. Use exact 4H exit model and cost stress 14/25/40bps.
B1 CORE: единственная новая законченная проверка H4 parent birth → first 15m physical touch after zone birth → **1H close beyond original FVG NEAR EDGE in setup direction and real candle body in that direction** (no middle-of-zone "reaction" accepted), plus hour must have touched original H4 gap. Valid only when 1H candle **CLOSED AFTER first 4H POI touch**; i.e. no intrahour knowledge. → then 15m closed **same-direction IMB 3 closed bars** OR **close breaking a bona fide preconfirmed (2 left+2 right) 15m swing pivot**, with swing `confirmed_ms <= 15m confirmation candle START_MS` and prior candle close on other side. Does NOT use previous single-candle-high proxy mislabeled BOS. → next real native3m OPEN. This one route needs no added OB, liquidity zoo, H1 child formation, 5m nested pipeline or lookahead.

Both B0/B1:
- D1/W1 context and 4H FVG parent birth unchanged C105, 4H expiry 48h, first-test TTL 8h, 4H-close zone invalidation on original 4H FVG far-edge.
- **Exactly identical 4H-source SL and 4H-source TP** from untouched `c105_parent4h_structural_geometry.parent_plan`: 4H far FVG edge ±0.15 ATR14 of completed H4 = protective native3m executable stop, nearest confirmed+unswept H4 pivot ±0.15ATR4H target. Entry after confirmed 15m via genuine next3m open. Derived RR >=1.25 filter (not fixed target), risk percent 0.2–10%, max48h hold, bps 14/25/40, stop-first OHLC ambiguity.
- zone one shot, on eligible 15m confirm DONE even if trade rejected on geometry, one concurrently open PAPER trade per symbol. 7d historical warmup, 48h end embargo. Do not alter source baselines or model parameters after data opened.
- Score B1 vs B0 separately and together. B1 may trade fewer; no artificial minimum-frequency easing. Main scientific gate: n>=30, each 2 temporal folds>=10, netR25>0, PF25>1.2, PF40>1.1, DD25<10% with 1%-risk/trade model. Result can be FAIL, not a reason to fudge.

### New never-touched DATE window, 64 full UTC days
2026-05-01 inclusive -> 2026-07-04 exclusive (64 calendar days); 12 eligible source symbols `BNBUSDT,XLMUSDT,HBARUSDT,INJUSDT,OPUSDT,ALGOUSDT,CHZUSDT,ICPUSDT,SEIUSDT,PENDLEUSDT,LINKUSDT,UNIUSDT`.
**768 original Binance Vision USD-M daily 3m ZIP**, same-host .CHECKSUM + ZIP SHA and CSV SHA, expected 64×12×480=368640 native3m candle. Fully closed D1/W1 and 4H derived from native3m; invalid/missing days BLOCKED_SOURCE. Time fold pivot 2026-06-02 UTC, pre/after (same source month classes), 7-day warmup and final48h embargo. No Oct or Aug samples in current model test. Different historical time period, **not future prospective OOS**; no claim pristine alpha.
- This window and fixed symbols may be selected for source availability only, not on any inspected C109 outcome.
- Serial code comparisons must assert frozen C105 original bytes hash and 41 earlier C105/C106 records.
- Synthetic **adversarial tests**: 4H POI inside H1 midpoint vs outer edge, initial touch before completed H1, 15m pivot known only after right 2 bars, genuine close crossing vs wick, not prev single candle, true native3m open, no future 4H FTA, no SL TP from smaller timeframes, no different strategy after cost stress, no false "AI certified" label.

## Main business decision
A mechanically functioning engine is one that produces independently reproducible PAPER decisions with source-aware event chronology and honest economic gates. **A profitable stable trading system cannot be guaranteed by passing unit tests, increasing leverage, changing TP or increasing sample size.** If B1 still fails the predeclared gate, report FAILED and keep PAPER. Do not integrate risky live orders.

## Output
Single `cycles/B1_C109_SIMPLE_CORE_ORIGINAL_NEW_TIME_COMPARATIVE_REPORT_RU.md`, evidence `evidence/c109/C109_CORE_VS_ORIGINAL_768_3M_PROVIDER_ZIPS.json`, honest success/fail by B0 and B1, no copied Pine, root journal A172 only after end-to-end source + regressions.
