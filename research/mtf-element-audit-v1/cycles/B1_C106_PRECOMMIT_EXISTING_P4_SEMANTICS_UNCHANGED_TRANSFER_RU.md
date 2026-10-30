# C106B — предварительная регистрация до новых котировок (2026-10-30)
## Решение владельца
Из LuxAlgo **не добавлять лишние алгоритмы, BOS/CHoCH, OB, EQH, premium/discount и др.**. Цель — проверить **существующие** C105 4H FVG POI + 4H confirmed pivot TP + закрытая 1H reaction + 15m VC + native3m next-open. **БЕЗ изменений в торговых правилах**, включая 4H SL, 4H TP, исходный derived RR, предварительное 1D/1W, 48h hold и 14/25/40bps. Никаких новых индикаторов, оптимизаций, замен целей или экзотических фильтров.

## Проверить прежде всего на уровне определения событий
1. 4H FVG известен только после закрытия 3-й 4H свечи, даже если нарисованный уровень находится в прошлом. Соседние бары строго непрерывны и только полностью закрыты.
2. 4H цель из 4H pivot 2-left/2-right появляется только после **закрытия обеих правых 4H свечей**, не в момент исторического экстремума. Ближайшая уже взятая после подтверждения 4H ликвидность недоступна.
3. First touch 4H после рождения POI (не те же 4h/15m бар), 1H rejection **позднее первого touch** по закрытой свече, VC 15m позднее 1H, next native3m open = закрытие 15m. Никакие 1H/15m экстремумы не используются для 4H SL/TP.
4. Проверить разделение signal time vs historical pivot display time на примере пользовательского LuxAlgo Pine 848 строк, не копируя его реализацию. Источник там может перерисовывать HTF FVG по lookahead_on с high[0]/low[0]; его сигналы НЕ считать эталонными историческими таймштампами. Ему не приписывать неподтверждённые авторские торговые SL/TP.
5. Сохранить SHA исходного C105 и 25/25 оригинальных исторических сделок; любые расхождения или invalid causal chain — **REJECT/DIAGNOSE**, а не косметическое переписывание журналов.

## Замороженный новый набор оригинальных 3m данных
Ранее не участвовавшие в C93/C102/C104/C105 оригинальных independent transfers: **ALGOUSDT, CHZUSDT, CRVUSDT, EGLDUSDT, ENSUSDT, ICPUSDT, MANAUSDT, PENDLEUSDT, SEIUSDT, TIAUSDT**; 32 полностью закрытых UTC дня 2026-09-26..2026-10-27 включительно. Exactly 320 Binance Vision USD-M original daily 3m ZIP, original same-host CHECKSUM, SHA ZIP and CSV, expected 153600 original native3m bars. C105 source and engine untouched: C106 runner uses temporary, immediately restored scoped SYMBOLS whitelist of 10 tickers while executing **byte-identical** C105 event_per_coin. If any source absent or continuity / checksum fail, NO data swap and **BLOCKED_SOURCE**. 7d existing warmup and 48h final embargo unchanged.
Новизна выборки **только по символам**; тот же рыночный период, не настоящий future prospective OOS, к тому же прошлые исследования по другим инструментам уже открыты. В точности прежняя оценка C105: >=30 trades, two temporal folds >=10 each, netR25>0, PF25>1.2, PF40>1.1, modeled 1%-risk DD25<10%. Проверять также side asymmetry, early vs late, source-wise proof, completeness. **Не подгонять по 10 монетам, не переносить эти исторические trades на реальный счёт**.

## Результаты, подлежащие фиксации
- C106 scope/semantic invariants test script: ZERO added trading components.
- 25 historical source C105 positions and A168 hash chain unchanged.
- C106 new 10-coin unmodified C105 exact signal/path result + 4H-only structural SL/TP source, full original checksum manifest, independent CI three Python versions including all 664 old C105 tests, immediate PASS or FAIL with complete reasons.
- C106 source evidence JSON SHA256 pinned; append A169 *only after* whole source and CI validation, update map/handoff; no WRITE to any C105 module, original C105 evidence or A168 journal entries.
