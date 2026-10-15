# ACADEMIC_ENGINE_RECOVERY_AUDIT
**Cycle:** Recovery A / 2026-10-15. **Research only — PAPER ONLY; NO LIVE ORDERS.**
**Baseline:** `research/mtf-element-audit-C07-20261014` @ `7f6e81bc405d4139b6206a9c5300725e59c5e0d0`.
**Audit method:** authenticated GitHub connector (repository trees, branch HEADs, comparisons, direct source files) and Google Drive connector (source text). This is *read-only source comparison*, not a fresh local test run nor semantic/visual acceptance. Historical CI is cited as past evidence, not rerun today.

## A. Scope and non-destructive conclusion

Keep the **existing EMBER repository** and audited C07 foundation. Branches share ancestry but have diverged. Do **not** merge automatically. None of the inspected code verifies all academic pattern geometries; no model gets `ACADEMIC_APPROVED` on this cycle. Main, Smoke-strategy, smoke-trading-terminal, telegram-signal-bot, V5, QFVG_FS15 and AppDeploy were not altered. No network exchange keys, no real orders.

The frozen C07 SPEC-0.1 inventory contains exactly **45 IDs** (D01–D04, C01–C05, L01–L05, P01–P10, T01–T11, R01–R04, X01–X06). Its *baseline* statuses are **3 INFRA_ENGINEERING_CHECKED, 30 PARTIAL_OR_PROXY, 12 MISSING_OR_NOT_SEMANTICALLY_APPROVED**. Those are historical SPEC-0.1 classifications, **not recomputed signoffs**. In later cycles D03 has a formally verified isolated lineage contract; D04 remains `VERIFIED_FORMAL_SAMPLED_SOURCE_ONLY` for provenance (not all 315 archives).

## B. Branches (GitHub readback on 2026-10-15)

| Branch | HEAD SHA |
|---|---|
| `agent/config-sync-frequency-30000` | `9e5fcf9a0f5fd671f1bd9c222233605114a4feaf` |
| `agent/core-15000-validation` | `0854cbabe52e4d7e4be2999c6aad165c3f4e368b` |
| `agent/diagnostics-and-real-sanity` | `73c3bf97ca46b011e2260bb50002708329d93354` |
| `agent/htf-bias-experiments` | `19b73fe1878ffd59eab3ef564b9bcc85068c9aef` |
| `agent/implement-portfolio-wfo-tz` | `feda21c6c8f2c44bec927238abe8ac85fd450c69` |
| `agent/oos-portfolio-wfo` | `50192482ec00111d8b6988c6b3d139dc85ae4035` |
| `agent/out-of-sample-4alts` | `adaad9db4231dff13227111c0ee224ae82f527f6` |
| `agent/validate-ember-engine` | `b61ddc946b0d1bd0e096c870f06fc6d80ef56010` |
| `agent/validate-ember-engine-2` | `00a9ca3521d0dcf949ae1eb4d711163a4eed49ef` |
| `main` | `5fa8ebf75410b47c327e323dbd1d1218d47aecde` |
| `research/academic-engine-recovery-20261015` | `7f6e81bc405d4139b6206a9c5300725e59c5e0d0` |
| `research/mtf-course-fidelity-v05` | `9f69d0e874dbd21a83f7c4c6bc66c43cb3ddcc25` |
| `research/mtf-element-audit-C04-20261014` | `69847d95d64911455a97d4a590f8e1eeda2b2be7` |
| `research/mtf-element-audit-C05-20261014` | `77b8e36f4e9f3f1d16d2302364d4258ab7443441` |
| `research/mtf-element-audit-C06-20261014` | `f4ad834b934839188bda5a034c6ebe4a6601691f` |
| `research/mtf-element-audit-C07-20261014` | `7f6e81bc405d4139b6206a9c5300725e59c5e0d0` |
| `research/mtf-element-audit-ledger-20261014` | `ef18515b10ed352409c8fd4c72a3ac79ce71387d` |
| `research/mtf-frozen-oos-2025` | `7a8c41c7bdff9e69be11e7bbef3a5be63557cb93` |
| `research/mtf-route-v04-futures-20261014` | `a042163ea98e2b98ce951e693609f9b61548ab46` |
| `research/mtf-v05-parent-lifecycle-20261014` | `8d788407d4214a4ba15f07f46a94fb7eadb9f144` |

GitHub commit dates: C07 2026-10-14 16:12:22Z; separate course-fidelity-v05 2026-10-13 23:34:36Z; parent-lifecycle-v05 2026-10-14 11:24:48Z. Default `main` is dated 2026-08-04 and is **not** newer academic research. `C06...C07` is a 5-commit fast-forward; C07 vs course-fidelity, parent-lifecycle, route-v04 **diverged**. C07 should remain the sole audit/foundation base for this work branch.

## C. Already proven — scope delimited

- **D01** separate closed OHLCV bar contract and strict reject controls (`strict_bar_closed.py`); local CSV loader alone is not enough.
- **D02** temporal aggregation/snapshot and delayed pivot availability (`strict_tf_d02.py`); 3m/5m source archives and academic structures are not thereby proven.
- **D03** `strict_event_lineage_d03.py` formally checks causal timestamps and replay: C06 reported **96 PASS**, 180 corrupted relations rejected, 20 future modifications ignored, but linked VC may still be geometrically unrelated to trigger — semantics **not** verified.
- **D04** `strict_vision_d04.py` verifies a specified Futures HTTPS Vision ZIP + `.CHECKSUM` and normalized history. C07 reported **134 tests PASS**, **200/200** adversarial examples rejected; 10 normalized CSV, 98,680 bars, **315** declared 2026 ZIPs, but only **10** 2026 original ZIP + **2** BTC 2025 ZIP were independently retrieved with receipts. **305 of 315** 2026 ZIPs remain unverified over network. Jan 29 2025 BTC volume 169393.057 vs 169989.952 is **quarantined**. Source checksum from same host is not a digital signature. CI run https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38595068903 success as reported in C07.
- **course-fidelity-v05 isolated primitives:** `confirmed_pivots` (right-bar timing), `confirmed_hourly_raids` (wick reclaim), `bos_after_raid` (3m/5m close BOS), `quote_bos_next_open` (hypothetical next-bar quote), `confirmed_strong_hl` (requires evidence), `select_idm` (inside/ahead of POI), `PoiLifecycle` (first post-knowledge test), `confirmed_imb` + `imbs_after_trigger` (5m FVG candidates). Its MANIFEST/README reports **29/29 synthetic PASS**, **0 visual course-verified**, **NO heavy backtest**; THESE ARE NOT FINISHED ROUTES.
- **parent-lifecycle-v05 independent fix:** `parent_issue_guard` in `research/mtf-v05/mtf_engine_v05.py` prevents new idea creation after exact parent invalidation, separately for A/B/B4/C. Prior signal based on invalid 4H parent was reproducible (BTC 2026-05-22 12:15 UTC). The earlier v0.4 remains frozen. Test file: `research/mtf-v05/test_parent_lifecycle_v05.py`; earlier GitHub run 38554780180 reported **126 PASS**, no guarantee after idea generation or pending-order cancellation.
- **old route-v04**: portfolio ID namespace bug was fixed via `symbol|source_id`, preserving original `source_id`. The 2026 baseline COURSE_PARENT_FTA/BASE **−15.66%**, not proof against the original course. V0.5 old route remains negative on all 8 listed 2025/2026 portfolio configurations. Freeze these facts; avoid tuning to PnL. Old C route is explicitly `C_BOS_15M_PROXY`, **not** BOS 3m/5m.

## D. All 45 entries — existing registry crosswalk (NOT approvals)

The `source` column means **text was found**, not that its graphical example was validated. A status of `NEEDS_SOURCE` is deliberately retained where no exact rule/figure has been tied to the ID. `ENG` items have engineering specification rather than a supposed trading academy definition. Baseline issues/details remain preserved at `research/mtf-element-audit-v1/baselines/spec_0_1/ELEMENTS_STATUS.json`.

| ID | Academic / engineering element | SPEC-0.1 baseline status | Source evidence level | Existing code reuse candidate |
|---|---|---|---|---|
| D01 | Закрытая свеча OHLCV | INFRA_ENGINEERING_CHECKED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-element-audit-v1/tools/strict_*` + `tests/test_d0*` |
| D02 | Агрегация и синхронизация TF | INFRA_ENGINEERING_CHECKED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-element-audit-v1/tools/strict_*` + `tests/test_d0*` |
| D03 | Время появления/подтверждения/исполнения | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-element-audit-v1/tools/strict_*` + `tests/test_d0*` |
| D04 | Подлинность и тип рыночного источника | INFRA_ENGINEERING_CHECKED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-element-audit-v1/tools/strict_*` + `tests/test_d0*` |
| C01 | Структура HH/HL и LH/LL | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Order Flow (text only)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| C02 | Order Flow (OF) | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Order Flow (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| C03 | Глобальное направление / конфликт TF | PARTIAL_OR_PROXY | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| C04 | Торговая сессия / PDH/PDL / AH/AL | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Session Liquidity (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| C05 | Окружение BTC/ETH, funding/OI и новости | MISSING_OR_NOT_SEMANTICALLY_APPROVED | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| L01 | Обычный фрактал / swing pivot | PARTIAL_OR_PROXY | NEEDS_SOURCE | `course_primitives_v05.py`: `confirmed_pivots` |
| L02 | BSL — Buy Side Liquidity | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS + Liquidity (text)) | `course_primitives_v05.py`: `confirmed_hourly_raids` |
| L03 | SSL — Sell Side Liquidity | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS + Liquidity (text)) | `course_primitives_v05.py`: `confirmed_hourly_raids` |
| L04 | EQH/EQL — равные экстремумы | MISSING_OR_NOT_SEMANTICALLY_APPROVED | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| L05 | Liquidity Raid / sweep | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by BOS (text)) | `course_primitives_v05.py`: `confirmed_hourly_raids` |
| P01 | POI — Point of Interest, родительская зона | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (POI (text)) | `research/mtf-v05/mtf_engine_v05.py`: parent as-of guard; `course_primitives_v05.py`: `PoiLifecycle` |
| P02 | IMB / FVG | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Fair Value Gap (text)) | `course_primitives_v05.py`: `confirmed_imb`, `imbs_after_trigger` |
| P03 | Order Block (OB) | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Order Block (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| P04 | Rejection Block (RB) | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Rejection Block (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| P05 | SNR — Support becomes Resistance / наоборот | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (SNR (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| P06 | Volume Confirmation (VC) — структурное | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (IMB/SNR + IDM (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| P07 | First test / Freshness / mitigation | PARTIAL_OR_PROXY | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py`: parent as-of guard; `course_primitives_v05.py`: `PoiLifecycle` |
| P08 | Инвалидация / время жизни POI | PARTIAL_OR_PROXY | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py`: parent as-of guard; `course_primitives_v05.py`: `PoiLifecycle` |
| P09 | Strong High / Strong Low | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Strong High & Low (text)) | `course_primitives_v05.py`: `confirmed_strong_hl` (evidence contract) |
| P10 | Сила зоны S1/S2/S3 | PARTIAL_OR_PROXY | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T01 | Тест POI | PARTIAL_OR_PROXY | NEEDS_SOURCE | `research/mtf-v05/mtf_engine_v05.py`: parent as-of guard; `course_primitives_v05.py`: `PoiLifecycle` |
| T02 | 1H Trigger для маршрута A | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry IMB & SNR (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T03 | Inducement (IDM) | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by IDM (text)) | `course_primitives_v05.py`: `select_idm`; existing v0.5 route proxy |
| T04 | BOS — Break of Structure | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by BOS (text)) | `research/mtf-course-v05/src/course_primitives_v05.py`: `bos_after_raid`; existing v0.5 route proxy |
| T05 | 15m/5m реакция и дочерняя VC | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry IMB & SNR (text)) | `course_primitives_v05.py`: `confirmed_imb`, `imbs_after_trigger` |
| T06 | Причинная ссылка между событиями | MISSING_OR_NOT_SEMANTICALLY_APPROVED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T07 | FTA — First Trouble Area | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS/IDM target notes (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T08 | Entry — условие входа | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS/IDM entry notes (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T09 | Структурный стоп (SL) | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS/IDM structural SL (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T10 | Одна структурная TP / Target | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (BOS/IDM FTA target (text)) | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| T11 | Расчёт Net RR и размера риска | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-v05/mtf_engine_v05.py` (legacy approximations) or NOT_IMPLEMENTED; inspect exact route before reuse |
| R01 | Маршрут A: IMB/SNR entry | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by IMB & SNR (text)) | `research/mtf-v05/mtf_engine_v05.py`: A route (partial/proxy) |
| R02 | Маршрут B: IDM early limit | PARTIAL_OR_PROXY | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by IDM (text)) | `course_primitives_v05.py`: `select_idm`; existing v0.5 route proxy |
| R03 | Маршрут C: raid→3–5m BOS | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry by BOS (text)) | `research/mtf-course-v05/src/course_primitives_v05.py`: `bos_after_raid`; existing v0.5 route proxy |
| R04 | Маршрут A2: 1H POI→15m trigger→5m VC | MISSING_OR_NOT_SEMANTICALLY_APPROVED | TEXT_LOCATED__NOT_VISUALLY_ATTESTED (Entry IMB & SNR (text)) | `course_primitives_v05.py`: `confirmed_imb`, `imbs_after_trigger` |
| X01 | TradeIdea и разрешение заявки | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |
| X02 | Лимитная заявка / заполнение / отмена | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |
| X03 | Позиция / защитные заявки / выход | MISSING_OR_NOT_SEMANTICALLY_APPROVED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |
| X04 | Портфельная арбитрация | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |
| X05 | Журнал и доказательства | PARTIAL_OR_PROXY | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |
| X06 | Проверка качества отдельного элемента | MISSING_OR_NOT_SEMANTICALLY_APPROVED | ENGINEERING_NO_COURSE_SIGNOFF | `research/mtf-route-lab/` + `ember/` for research architecture; not academic signoff |

**Caution:** ID enumeration covers all 45; `P09` and `T03` are still semantically unapproved despite newer synthetic contracts. `D03` is stronger than its historical status **only for formal causal integrity**; `D04` status is conditional on sampled external origin. For `L01`, the 2-left/2-right confirmation is a **research rule**, not a proven author-specific swing definition. For `L05`, fixed 24h freshness is an **approximation** for “previous session / previous day”. For `P02`, the FVG detector proves wick-gap geometry but not full IMB context. For `P09`, supplying an arbitrary `Evidence` object does not prove contact existed on the chart. For `T03`, using a known pivot does not by itself prove inducement. For `T04`, source allows market on crossing BOS or a later limit after confirmation, while `quote_bos_next_open` only studies next-open, not both variants.

## E. Direct course material located

- [Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): 1H fresh fractal raid by wick, 3m/5m BOS, stop outside the raid, first HTF liquidity target; session limits require an explicit source time zone. Unresolved price unit of “15 pips” for USDT pairs must **not** be translated blindly.
- [Entry by IMB & SNR](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view): POI→lower-TF VC with IMB/SNR entry; 4H POI→1H VC→4H FTA, 1H POI→15m VC→1H FTA; 1H→15m→5m branch. Not one universal entry trigger.
- [Entry by IDM](https://drive.google.com/file/d/19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs/view): 4H VC→1H IDM or 1H VC→15m IDM; no final BOS required; StrongHL must be established.
- [Strong High & Low](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view): contact with liquidity/inefficiency + VC POI or BOS, not rolling extrema.
- [Order Flow](https://drive.google.com/file/d/1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN/view), [POI](https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view), [FVG](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view), [OB](https://drive.google.com/file/d/102w8UWvfGgS_ZMc-fD3xc6b7-AZ3IBg5/view), [RB](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view), [SNR](https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view), [Inducement definition](https://drive.google.com/file/d/1CJaLi_rssYaf_EupYUgz63s95nukvZRb/view), [Session Liquidity](https://drive.google.com/file/d/1HqGlqYUZptdNvOVLBHftx03XYASvo9MZ/view), [Premium / Discount](https://drive.google.com/file/d/1JpNhEPq79kiXQhaGPEte40V6QrtMdYed/view): preliminary textual sources obtained, 0 author-labeled chart geometries fully attested.
- [Academic summary](https://docs.google.com/document/d/1IG_NzvG9AZN7WD185WnHl9ZOkcUSY6EJxVMeCpZmi4g/edit) and [Atlas](https://docs.google.com/document/d/1zobqNAuGRjgOt7-cPW6GQR2HSzsxYGRQAPpMfrpk0OA/edit) are secondary consolidated indices, not substitutes for original course evidence.

## F. Reuse / explicit non-reuse decisions

| Component | Keep / candidate | Conflict / constraint |
|---|---|---|
| C07 D01–D04 tools, tests and SHA-chained action log | **KEEP AS BASE** | D04 sample only; formal lineage != semantic |
| C07 45 passports and matrix | **KEEP IMMUTABLE; overlay new status in new file only** | Old assessment not overwritten |
| v05 course `confirmed_pivots`, `confirmed_hourly_raids`, `bos_after_raid`, `select_idm`, `confirmed_strong_hl`, `PoiLifecycle`, `confirmed_imb` | **COPY CANDIDATES ONLY after semantic negatives and integration contracts** | no clean merger proven; isolated tests not full graph |
| v05 parent-as-of guard | **REUSE CONCEPT and negative case** | does not cancel pending orders; legacy assumptions remain |
| Old route-v04 portfolio scoped IDs / conservative simulation | **REUSE INFRA pattern**, not 15m BOS | no executed fills; incompatible academic proxy |
| Smoke-strategy `strategy_lab/mtf_feature_builder.py` | **research comparison only** | indicator/feature heuristics; not academic labeler or direct code port |
| smoke-trading-terminal `core/contracts/trade-plan.ts` | **future integration interface reference** | no changes to terminal or automatic orders |
| telegram-signal-bot rolling research tools | **optional engineering utilities only** | Runner/impulse logic may not be conflated with EMBER |

## G. Pending work ordered by dependency

1. **Recovery completion:** tie each of 45 IDs to source URL, exact section, figure, time/price geometry, code function, and positive/negative test. A text link is not a `SOURCE_VERIFIED` label. Initialize `ACADEMIC_SOURCE_TO_CODE_TO_TEST.md` separately.
2. **C08 D04:** independent HTTPS receipts for remaining 305 original 2026 ZIPs (not simply 305 local hashes), reconstruct comparison, record any changed original source; 2025-01-29 remains quarantined. This step **not executed** in this recovery audit.
3. **D05 semantic golden cases:** source visual examples + negative counterexamples of L01→L05, P01/P07/P09, T03/T04; explicit screenshot SHA, market/time/TF, known_at, rectangle edges. If inaccessible, `NEEDS_VISUAL_LABEL`.
4. **Compatibility contract:** choose one canonical `BarClosed` and event lineage shape from C07; adapt v05 research objects without rewriting trading rules, test invalid parents, late pivots, wrong price geometry, replay and prefix invariance, and pending-order lifecycle.
5. **Route validation A/B/C/A2 separately:** only after source-aligned structures accepted. No proxy treated as course rule; all missing evidence → `BLOCKED`.
6. **Frozen realistic historical PAPER replay:** after semantic approval, independent windows not previously revealed holdout, SL-first if OHLC ambiguity, fees, slippage, funding/liquidation limitations. The old negative results stay preserved.
7. **Prepare PAPER-only adapter**, separate strategy version and decision log, without touching live terminal.

## H. Self-falsification of this audit

- **Repro claim:** This document was generated from GitHub/Drive readbacks; the C07 branch, 45 registry rows, v05 code/tests and historical reports were fetched. **No local clone/network availability** was possible in this runner; no 2026 archive download, no rerun of 134/29/126 tests. Treat past CI as archived evidence, not fresh pass.
- **Strong counterexample:** formal D03 linkage can point to a temporally valid but physically unrelated trigger, so `known_at<=decision_at` is necessary, **not sufficient**.
- **Source fidelity counterexample:** `confirmed_strong_hl(contact, VC)` may receive evidence labels with no provable wick/POI/geometry; and 24h raid freshness ≠ verified Frankfurt/NY session.
- **PnL counterexample:** course primitives v05 passed synthetic unit tests and have **no** course chart labels, therefore no warranted extrapolation from historic old engine PnL to academy semantics.
- **Audit incompleteness:** no source bytes/figure hashes for 45 entries, no independent CI on this new branch yet, C08 not run. Stages B–H must not be marked complete.

## I. Audit evidence links and next verifiable action

- C07 snapshot: https://github.com/SanChi117/EMBER-Research-Engine/tree/research/mtf-element-audit-C07-20261014
- C07 source report: `research/mtf-element-audit-v1/C07_ИТОГ_И_ОГРАНИЧЕНИЯ.md` and `СЛЕДУЮЩАЯ_ОЧЕРЕДЬ_C08.md`
- v05 isolated: https://github.com/SanChi117/EMBER-Research-Engine/tree/research/mtf-course-fidelity-v05
- v05 parent: https://github.com/SanChi117/EMBER-Research-Engine/tree/research/mtf-v05-parent-lifecycle-20261014
- frozen: https://github.com/SanChi117/EMBER-Research-Engine/tree/research/mtf-frozen-oos-2025
- Unique next action: build source-grounded 45-row traceability, check GitHub CI on audit-only branch, then C08 D04 and D05 semantic labels. **Not** start new strategy code or merge experimental branches.
