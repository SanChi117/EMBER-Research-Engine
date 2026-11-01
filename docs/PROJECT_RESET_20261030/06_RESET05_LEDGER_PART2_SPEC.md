# RESET-05 / Part 2 — persistent PAPER ledger v1 (2026-11-01)

## Scope and dependencies

This is **part 2 only** (append-only PAPER ledger), after the owner's accepted
risk-first stage. No registry (part 3), Python golden-fixture freeze (part 1),
gate report (part 4), OI/funding/liquidation collector, detector, or live trading
is implemented here. R030 continuous extraction/closure is queued **after all
RESET-05 parts** and is not touched by this commit.

The existing research/platform/sha_ledger.py canonical/extend/verify format
is reused without modification. The existing paper_execution.py is unchanged.
No TS, AppDeploy, Google Drive, live exchange clients, keys, or scheduled
PAPER automations are modified. The research mandate in main remains locked.

## Storage / schema

- Linux/POSIX Python (fcntl advisory locks), filesystem with durable writes.
- Root: caller-supplied location, e.g. **data/paper/** on a persistent volume.
- Exactly three event files: signals.jsonl, trades.jsonl, executability.jsonl.
  Independent SHA chains, unique event IDs per stream, strict type prefixes.
  Small auxiliary .<stream>.lock files are permitted.
- One line is one existing sha_ledger.extend record. Canonical UTF-8 JSON,
  sorted keys, UTC observed_at_ms (positive integer), Decimal encoded as
  strings; nested floats/NaN/Infinity prohibited.
- API: PaperLedgerStore protocol (append/read/verify); implementation
  JsonlPaperLedgerStore. Postgres can implement the same interface later.
- Appends use exclusive file locks, O_APPEND, fsync(fd), and directory fsync on
  initial file creation. No in-place rewrite, compaction, or auto-repair.
- Concurrent processes on ONE POSIX host are serialized by flock. On a
  network/shared filesystem where flock or fsync semantics are not guaranteed,
  this contract is **NOT validated**; do not deploy there untested.
- Fail closed on corrupted chain, noncanonical JSON, duplicate ID, truncated
  final line, invalid stream/type, invalid observed_at_ms, or invalid number.
  An interrupted append leaving a torn line needs explicit offline incident
  handling; no rollback/truncation of evidence is performed automatically.

**Durability limitation:** this module preserves complete records across a
process restart ON THE SAME persistent volume. GitHub Actions runners are
ephemeral and cannot serve as a persistent production journal. This package
DOES NOT deploy or activate a journal daemon or move existing PAPER records.
It does not make an already-running PAPER planner use this store.

**Integrity limitation:** without an independent pinned head SHA, deleting
entire valid records from the tail is undetectable by a local chain alone.
Use verify(stream, expected_head=<externally pinned SHA>) to detect that.
The part-2 source-artifact SHA witness in this repo is a CODE provenance
receipt, not a substitute for future EXTERNAL runtime ledger-head witnesses.

## Risk integration (owner's nonblocking note)

The accepted risk_guard.py remains pure preflight. This part is storage only;
it does NOT connect risk verdicts to paper_execution.py. When the subsequent
RESET-05 wiring is explicitly authorized, gap-through-stop modeled by
paper_execution must dominate the optimistic stop-loss estimate from the
preflight; never understate risk. PASS never becomes LIVE permission.

## Independent checks

    ruff check research/platform/paper_ledger.py tests/test_reset05_paper_ledger.py tests/test_reset05_witness.py
    python -m pytest tests/test_reset05_paper_ledger.py tests/test_reset05_witness.py tests/test_risk_guard.py tests/test_reboot_platform.py -q

CI: matrix Python 3.10 / 3.11 / 3.12, plus the unchanged repo-wide CI.
Adversarial cases: three stream isolation, crash/restart recovery, duplicates
after restart, middle-byte tamper and refuse subsequent append, torn tail
without repair, externally pinned tail-deletion detection, cross-stream
rejection, mandatory observation time, Decimal normalization, duplicate JSON
keys, and two concurrent process writers.

Owner acceptance only after actual commit SHA + CI-run SUCCESS and inspection
of the SHA witness at
docs/PROJECT_RESET_20261030/06_RESET05_LEDGER_PART2_SHA_WITNESS.jsonl.

**Next after acceptance:** RESET-05 part 3 (immutable strategy registry), and
part 1 (single-stack freeze + golden fixtures), then part 4 (machine gates);
collector only after RESET-05. Order: risk -> RESET-05 -> collector.
