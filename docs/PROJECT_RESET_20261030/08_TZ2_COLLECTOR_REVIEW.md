# TЗ-2 — Binance USDT-M forced-flow collector / implementation review

**Owner acceptance scope**: 2026-11-01 specification. Python-only, public API
(no keys), no TS/Telegram, no trading or automated strategy enablement.
Research mandate unchanged. Existing PAPER planners unaffected.

## Original protocol and provenance

OI endpoint: https://fapi.binance.com/fapi/v1/openInterest?symbol=SYMBOL .
Records openInterest in **contracts/base-asset units, NOT USD value**.
Provider time and observed_at_ms kept separately; source fixed.

Funding:
- indicative upcoming funding: https://fapi.binance.com/fapi/v1/premiumIndex?symbol=SYMBOL ;
- settled funding: https://fapi.binance.com/fapi/v1/fundingRate?symbol=SYMBOL&startTime=...&endTime=... .
The first is NOT realized and the second is known only on or after
provider settlement; never retrospectively mark old data as observed then.
The last 72h funding history is collected as actual provider-sourced
settlements, not a fabricated estimate. Larger outages are NOT silently
backfilled; coverage verification must fail if evidence is insufficient.

Liquidations: wss://fstream.binance.com/market/stream?streams=...
symbol@forceOrder. Provider describes snapshots as at most ONE per
1000ms per symbol: NOT every single individual forced liquidation.
This is essential for any later H2 economic claims. Merged UM/CM feed
must reject st != 1. WebSocket requires separately installed optional
websocket-client library, a long-running host, and durable storage.
Every confirmed PONG is a LIQ_HEARTBEAT minute; no packets / missing
PONG do not prove uptime. If the websocket is absent, record
LIQ_SNAPSHOT_PARTIAL; there is NO public authentic REST replay of all
forceOrder snapshots. Never substitute a guessed REST price snapshot.

## Storage, constraints, restart

Storage starts empty and is not deployed in this PR.
data/flows/oi_YYYY_MM.jsonl, funding_YYYY_MM.jsonl,
liquidations_YYYY_MM.jsonl. Per-month append-only existing sha_ledger
SHA256 chain, canonical JSON, UTC observed timestamp, provider source,
Decimal strings, POSIX flock + fsync, duplicated IDs and altered bytes
fail closed. Monthly shards are independent chains; runtime integrity
verifier supports separately pinned external HEAD SHA map to detect
removal of a valid tail. Without independent pins, tail deletion is
not detectible. No automatic truncation or rewrite.

Events: OI_SNAPSHOT, FUNDING_SCHEDULE, FUNDING_SETTLED,
LIQ_FORCE_ORDER; COLLECTOR_RESTART, GAP, SCHEDULER_JITTER,
LIQ_HEARTBEAT, LIQ_SNAPSHOT_PARTIAL, SCHEMA_DRIFT.
SCHEMA_DRIFT is terminal and blocks all subsequent writes to its
stream until a separately audited repair. Missing OI hours after the
first recorded slot get GAP markers, **not synthetic OI records**.
Running an hourly scheduled job has no effect on historical
WebSocket data; it cannot replace the 24/7 daemon.

## Usage (after owner review, on a persistent POSIX host)

  python -m research.platform.flow_collector --root /persistent/flows
  python -m pip install 'websocket-client>=1.8,<2'
  python -m research.platform.flow_liquidations --root /persistent/flows
  python -m research.platform.verify_flows /persistent/flows

To assess seven COMPLETE days, collect first and THEN run:

  python -m research.platform.verify_flows /persistent/flows --start-ms START_UTC_HOUR_MS --end-ms END_MS --report-json coverage.json

Start/end exactly 168 hours apart. For tamper/tail-delete control,
pin per-file HEAD SHAs outside the writable journal and pass
--expected-heads /trusted/witness.json. Only use prospective data;
7-day acceptance must contain real provider+heartbeat evidence.

Integrity alone prints FLOWS_OK. Seven-day report contains strict
coverage states, unmarked hourly OI gaps, funding schedule/settlement
capture and liquidation confirmed PONG uptime. LIQ_SNAPSHOT_PARTIAL is
explicitly partial, not confirmation of full liquidation coverage.
Do not infer strategy alpha before at least 30 days of data accumulation.

## Why no unattended hourly collection is activated in this PR

GitHub Actions hourly schedule only triggers workflows in the
**default** branch, while this work is intentionally on an isolated
research branch; Actions runners are ephemeral. Committing output from
a runner into the current code branch would also require explicit
repository-write approval, a trusted independent head witness, and
a separate persisted data branch. None of these are yet established.
The provided workflow is a CI/mock test workflow ONLY. Claiming
the seven-day trial already started would be false.

**Status expected before live host is provisioned**:
TECHNICAL_CI_PASS possible, DATA_COVERAGE_IN_PROGRESS mandatory.
Seven-day DONE requires 12-symbol real 168h journal, 95% OI slots,
full source-declared funding settlements, 95% authenticated WS uptime
or explicit LIQ_SNAPSHOT_PARTIAL (partial classification), external
SHA witnesses, owner spot-check, verified CI and SHA commit.

No scripts and no credentials for LIVE Binance trading are present.
