# C58 — Route C 1H parent identity and 3m/5m observation state

Status: **[~] IMPLEMENTED, FULL FROZEN REGISTRY REPLAY PENDING**. Separate branch `research/c58-route-c-parent-state-20261025`; no merge, no journal append and no change to accepted C56/A125 or supplemental A126 evidence.

## Purpose and correct layer

C56 compares closed 3m and native 5m research breaks belonging to one exact 1H raid. It does not provide a reusable object identity/state registry. C58 addresses only that semantic/state gap:

`perceived C56 objects → exact 1H parent identity → separate native 3m/5m child states → source-coverage-aware relationship`.

It does **not** select an entry, authorize an order, choose FTA/SL/TP or promote adapted geometry to author-confirmed BOS.

## Contract

- `parent_identity`: deterministic SHA-256 identity over symbol, BSL/SSL kind, 1H pivot center, first breach and raid confirmation. Changing a child event cannot rename the parent; another parent cannot share the same identity by merely reusing a child bar.
- `identify_route_c_parent_state`: validates the actual C56 dataclass, native raw-row ID timestamps, strict parent/child knowledge chronology, non-trade blockers and C56 status/event consistency.
- `NativeSourceCoverage`: distinguishes a complete closed native stream through the common as-of from stale or incomplete coverage.
- Five states: `BOTH`, `ONLY_3M`, `ONLY_5M`, `UNKNOWN_3M`, `UNKNOWN_5M`. `ONLY_*` means absence **under the existing adapted detector in complete source**, not absence of market structure. Incomplete other-TF coverage must produce `UNKNOWN`, never proven absence.
- Earlier 3m/5m close or equal close time is a timing relation, **not directional contradiction** and not one merged child event.
- `build_parent_state_registry`: deterministic order, one exact parent once, duplicate rejection and full recomputation of every state to reject forged IDs, changed observation states, readiness or order fields.

## Tests actually performed locally

`d05/test_c58_route_c_parent_object_state.py`: **40/40 PASS**, then repeated **40/40 PASS** with the actual current C56 source file as the interface. Coverage includes positive dual/single/same-close states, stable identities, stale/incomplete sources, future or boundary-time events, raw-ID substitution, cross-TF hash borrowing, false C56 status, duplicate parents, forged registry fields, FX, author/trade/readiness promotion.

Two defects found during self-review were fixed before publication: child knowledge exactly at parent confirmation is now rejected, and registry admission recomputes the complete state rather than checking only its ID.

No original 60 ZIP were downloaded by C58. No C56 evidence bytes were changed. No author golden, market signal, order, fill, trade or PnL was produced.

## Full frozen-source replay added, not yet claimed PASS

`tests/probe_c58_frozen_c56_parent_state_registry.py` reads the complete pinned C56 JSON (Git blob `98f087a731d30c2191dc443038c371751456f316`) and reconstructs all **542** parent states with a common closed as-of `1790985600000`.

Preregistered expected relations from accepted C56:

- 509 `BOTH_CHILD_BREAKS_OBSERVED`;
- 30 `ONLY_3M_CHILD_BREAK_OBSERVED_5M_ABSENT_IN_COMPLETE_SOURCE`;
- 3 `ONLY_5M_CHILD_BREAK_OBSERVED_3M_ABSENT_IN_COMPLETE_SOURCE`.

The probe also requires 542 unique IDs, permutation-invariant registry order, duplicate rejection, and incomplete-source controls converting exactly the 30 missing-5m and 3 missing-3m records to the corresponding `UNKNOWN` state. These are **acceptance expectations, not locally observed C58 results yet**. Local evidence download failed by network; therefore no full-registry PASS is claimed in this report.

A workflow definition was prepared locally but GitHub rejected workflow creation with `403 insufficient scopes`. No permission bypass was attempted. Full checkout execution remains required:

```bash
cd research/mtf-element-audit-v1
python -m unittest -v d05/test_c58_route_c_parent_object_state.py
python tests/probe_c58_frozen_c56_parent_state_registry.py /tmp/C58-registry.json
```

## Boundaries and next step

This is `ADAPTED_ROUTE_C_PARENT_CHILD_OBSERVATION`, `PAPER ONLY · NOT_TRADE_READY`. It is not academic object certification and not Route A/B semantics. The parallel C57 Route A work remains separate and untouched.

Next: execute the full frozen registry probe and the 40-test matrix on Python 3.10/3.11/3.12 in an environment with workflow permission or a full local checkout. Only after actual PASS consider freezing C58 derived evidence; do not append a journal action merely because code exists.
