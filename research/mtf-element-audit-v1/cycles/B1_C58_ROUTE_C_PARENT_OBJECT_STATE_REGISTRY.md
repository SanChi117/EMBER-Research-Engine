# C58 — Route C 1H parent identity and 3m/5m observation state

Status: **[x] WORKING RESEARCH CONTRACT IN ISOLATED BRANCH**. Full frozen-C56 registry replay and Python matrix PASS. This is not trade readiness and not an accepted academic rule.

Branch: `research/c58-route-c-parent-state-20261025`. The shared research branch, its handoff/map, accepted C56/A125 and supplemental A126 evidence, parallel C57 Route A work and the append-only audit journal were not modified. No merge was performed.

## Purpose and correct layer

C56 compares closed 3m and native 5m research breaks belonging to one exact 1H raid. C58 adds the missing reusable semantic/state layer:

`perceived C56 objects → exact 1H parent identity → separate native 3m/5m child states → source-coverage-aware relationship`.

It does not select an entry, authorize an order, choose FTA/SL/TP or promote adapted geometry to author-confirmed BOS.

## Working contract

- `parent_identity`: deterministic SHA-256 identity over symbol, BSL/SSL kind, 1H pivot center, first breach and raid confirmation. A child event cannot rename the parent.
- `identify_route_c_parent_state`: validates the actual C56 dataclass, native raw-row ID timestamps, strict parent/child knowledge chronology, non-trade blockers and C56 status/event consistency.
- `NativeSourceCoverage`: distinguishes complete closed native coverage through the common as-of from stale or incomplete coverage.
- Five states: `BOTH`, `ONLY_3M`, `ONLY_5M`, `UNKNOWN_3M`, `UNKNOWN_5M`. `ONLY_*` means absence under the existing adapted detector in complete source, not absence of market structure. Incomplete other-TF coverage produces `UNKNOWN`.
- Earlier 3m/5m close or equal close time is a timing relation, not directional contradiction and not one merged child event.
- `build_parent_state_registry`: deterministic order, duplicate rejection and complete state recomputation to reject forged IDs, changed states, readiness or order fields.

## Actual verification results

### Adversarial matrix

`d05/test_c58_route_c_parent_object_state.py`: **40/40 PASS on each** Python **3.10.22**, **3.11.2**, **3.12.12**.

Coverage includes positive dual/single/same-close states, stable identities, stale/incomplete sources, future and boundary-time events, raw-ID substitution, cross-TF hash borrowing, false C56 status, duplicate parents, forged registry fields, FX and author/trade/readiness promotion.

Two defects found during self-review were fixed before these final runs: child knowledge exactly at parent confirmation is rejected, and registry admission recomputes the complete state rather than checking only its ID.

### Complete frozen C56 replay

`tests/probe_c58_frozen_c56_parent_state_registry.py` replayed the complete pinned C56 JSON, Git blob `98f087a731d30c2191dc443038c371751456f316`, SHA-256 `24db86b20e0454d6ac5abd1e4506f092f23d9c448d77c1862c3c777c40b7af07`, at closed as-of `1790985600000`.

Observed PASS on each Python 3.10/3.11/3.12:

- **542** unique parent identities;
- **509** `BOTH_CHILD_BREAKS_OBSERVED`;
- **30** `ONLY_3M_CHILD_BREAK_OBSERVED_5M_ABSENT_IN_COMPLETE_SOURCE`;
- **3** `ONLY_5M_CHILD_BREAK_OBSERVED_3M_ABSENT_IN_COMPLETE_SOURCE`;
- duplicate identity rejected;
- input permutation produces identical registry order;
- incomplete-5m control produces exactly **30** `UNKNOWN_5M`;
- incomplete-3m control produces exactly **3** `UNKNOWN_3M`.

All three full outputs are byte-identical: **1,025,051 bytes**, SHA-256 `81d1d0350b9f0e59a5f2d27c12e7296de792714c62bb83e9e7860d82f28ebeab`. The full derived JSON is reproducible by the probe and is not published as a new frozen evidence file. The compact factual witness is `evidence/c58/C58_LOCAL_FULL_FROZEN_C56_REGISTRY_WITNESS_20261025.json`.

C58 did not redownload the original 60 market ZIP and does not claim independent original-market validation. It independently replays the already accepted frozen C56 derived evidence for the new identity/state contract.

## Workflow and acceptance boundary

GitHub workflow creation was rejected with `403 insufficient scopes`; no permission bypass was attempted. The successful matrix and replay reported here are actual local executions, not GitHub Actions runs.

No new audit-journal action was appended. Code existence and local PASS are not silently converted into shared acceptance. The isolated branch is ready for subsequent independent review/replay, not for live or paper execution.

`ADAPTED_ROUTE_C_PARENT_CHILD_OBSERVATION` · `PAPER ONLY · NOT_TRADE_READY` · 0 author approvals · 0 orders · 0 fills · 0 trades · no PnL.
