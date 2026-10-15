# ACADEMIC_SOURCE_TO_CODE_TO_TEST — provisional source crosswalk
**Date:** 2026-10-15. **Status: INCOMPLETE / INITIAL TRACEABILITY**, not semantic acceptance or executable strategy.
**Upstream:** `ACADEMIC_ENGINE_RECOVERY_AUDIT.md` on `research/academic-engine-recovery-20261015`.
**Rule:** a source *URL* and source *text* do not validate its precise chart object. Missing exact annotation, file SHA, time/price, zone edges, known_at, negative counterexample and course-specific semantics means `NOT_ACADEMICALLY_APPROVED`. `ENG_SPEC` requires an engineering acceptance test rather than fabricating a course figure.

| ID | Source / nearest text lesson | Existing code / reuse candidate | Existing tests (scope limited) | Current acceptance |
|---|---|---|---|---|
| D01 | ENG_SPEC (not a trading pattern) | C07 tools/strict_*; tests/test_d01* | C07 tests/test_d01* / previous CI only | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| D02 | ENG_SPEC (not a trading pattern) | C07 tools/strict_*; tests/test_d02* | C07 tests/test_d02* / previous CI only | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| D03 | ENG_SPEC (not a trading pattern) | C07 tools/strict_*; tests/test_d03* | C07 tests/test_d03* / previous CI only | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| D04 | ENG_SPEC (not a trading pattern) | C07 tools/strict_*; tests/test_d04* | C07 tests/test_d04* / previous CI only | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| C01 | [Order Flow text](https://drive.google.com/file/d/1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| C02 | [Order Flow text](https://drive.google.com/file/d/1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| C03 | NEEDS_SOURCE | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| C04 | [PDH/PDL session text](https://drive.google.com/file/d/1HqGlqYUZptdNvOVLBHftx03XYASvo9MZ/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| C05 | NEEDS_SOURCE | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| L01 | NEEDS_SOURCE | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| L02 | [BOS lesson raid text](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| L03 | [BOS lesson raid text](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| L04 | NEEDS_SOURCE | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| L05 | [BOS lesson raid text](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P01 | [POI text](https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view) | research/mtf-v05/mtf_engine_v05.py (old/proxy as-of) | test_parent_lifecycle_v05.py (12 methods, not full route) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P02 | [FVG 3-bar gap text](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P03 | [OB two-bar body engulf text](https://drive.google.com/file/d/102w8UWvfGgS_ZMc-fD3xc6b7-AZ3IBg5/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P04 | [RB wick boundary and liquidity/IMB text](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P05 | [SNR flip text](https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P06 | [IMB/SNR VC notes](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P07 | NEEDS_SOURCE | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| P08 | NEEDS_SOURCE | research/mtf-v05/mtf_engine_v05.py (old/proxy as-of) | test_parent_lifecycle_v05.py (12 methods, not full route) | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| P09 | [StrongHL contact + VC text](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| P10 | NEEDS_SOURCE | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| T01 | NEEDS_SOURCE | research/mtf-v05/mtf_engine_v05.py (old/proxy as-of) | test_parent_lifecycle_v05.py (12 methods, not full route) | NEEDS_SOURCE; NOT_ACADEMICALLY_APPROVED |
| T02 | [IMB/SNR route text](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T03 | [IDM route text](https://drive.google.com/file/d/19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T04 | [BOS 1h→3/5m text](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T05 | [IMB/SNR VC text](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T06 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| T07 | [same-TF POI FTA notes](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T08 | [BOS entry alternatives](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T09 | [SL beyond raided liquidity](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T10 | [FTA at parent TF](https://drive.google.com/file/d/19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs/view) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| T11 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| R01 | [Route A source](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | research/mtf-v05/mtf_engine_v05.py (old/proxy as-of) | test_parent_lifecycle_v05.py (12 methods, not full route) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| R02 | [Route B source](https://drive.google.com/file/d/19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| R03 | [Route C source](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| R04 | [Route A2 source](https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view) | course_primitives_v05.py (isolated; function-by-function review) | test_course_primitives_v05.py (synthetic 29-case suite, not visual) | TEXT_FOUND__NEEDS_VISUAL_LABEL; NOT_ACADEMICALLY_APPROVED |
| X01 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| X02 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| X03 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| X04 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| X05 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |
| X06 | ENG_SPEC (not a trading pattern) | legacy v0.5 module or NO VERIFIED IMPLEMENTATION | NO DIRECT COURSE-LABELED TEST | ENGINEERING_ONLY; NOT_ACADEMICALLY_APPROVED |

## Exact acceptance schema to fill before approving each item

- `source_uri`, `source_sha256`, `course_section`, `figure_id`, `source_version`, `source_tf`.
- `golden_symbol`, `golden_exchange`, `golden_market_type`, `open_at`, `known_at`, `as_of`.
- `golden_geometry`: level/low/high/extreme, parent/child IDs, side, source screenshot SHA and **independent** human chart annotation where necessary.
- `function_path`, `function_ref_sha`, `test_path`, `positive_case`, `negative_case`, `mutation_case`, `cross_tf_case`, `prefix_replay_case`.
- `pass_status` in {NEEDS_SOURCE, NEEDS_VISUAL_LABEL, IMPLEMENTED_UNVERIFIED, FAIL_SEMANTIC, APPROVED_ENGINEERING, APPROVED_ACADEMIC}; **default is not APPROVED_ACADEMIC**.
- Attach prior errors, falsification attempts, CI run ID and data SHA. Do not write run IDs that did not occur.

## Priority: explicit source/implementation differences

1. BOS (T04/R03): core legacy uses 15m SNR proxy, v05 source-aligned research uses 1H wick raid→3/5m BOS; no completed integrated route.
2. IDM (T03/R02): legacy 2+2 pivot alone; v05 adds StrongHL evidence contract and inside/in-front geometry, still lacks completed contextual POI graph and early limit order lifecycle.
3. StrongHL (P09): v05 evidence contract, but labels may be supplied without independent chart geometry.
4. POI (P01/P07/P08/T01): v05 parent-as-of block + v05 isolated PoiLifecycle, not a unified consumed/retired/pending-order cancellation.
5. IMB/SNR (P02/P05/R01): source 3-wick gap, parent→trigger relationships; no validated complete SNR boundaries or cross-timeframe geometry.
6. Data (D01–D04): independently audited foundation with C07 D04 only sample provenance; missing origin of 305 ZIP archives. Do not relabel as semantically approved.

## Evidence currently only historical

C07 GitHub Actions run 38595068903; course-v05 MANIFEST local 29/29; parent-lifecycle run 38554780180. Independent tests on this new audit branch **not run**. Course-labeled chart cases accepted: **0**. C08 independent archive review: **not run in this cycle**. No trading performance evaluated by these documents.
