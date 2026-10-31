# Reproduce A217 (research only)

Read `/RESEARCH_MANDATE_LOCKED.md` and issue #9 first. Use this branch's unchanged source and frozen protocol. No exchange credentials or messaging service is required.

```bash
python3.12 -m venv /tmp/ember-a217-env
/tmp/ember-a217-env/bin/pip install -r research/a217_trendrider_original/evidence/runtime_requirements.txt
/tmp/ember-a217-env/bin/python research/a217_trendrider_original/prepare.py /tmp/ember-a217
/tmp/ember-a217-env/bin/python research/a217_trendrider_original/preflight.py /tmp/ember-a217
/tmp/ember-a217-env/bin/python research/a217_trendrider_original/run_native.py /tmp/ember-a217
/tmp/ember-a217-env/bin/python research/a217_trendrider_original/verify.py /tmp/ember-a217
```

Downloader reuses A203 `load_zip` / timestamp parser, stores URL+ZIP+CSV SHA receipts and local raw CSV caches, validates OHLC bounds, timestamps and uninterrupted grids, repairs monthly mark gaps only from genuine daily mark archives. 4h is deterministic UTC aggregation of real 1h. Funding settlement milliseconds are floored to the corresponding hour solely for native accounting. No synthetic price fills or substitute markets.

Native adapter is existing A199 script, unchanged. Static exchange metadata is a modeling limitation, not proof of historical lot sizes or liquidations. The source's original limit-order assumptions remain native candle-touch assumptions. 12.5bps per-side is a combined stress-cost proxy. No results prove a real fill.

Native loader requests 210 daily startup candles (original source setting), despite the larger downloaded 2023 warmup. The protocol's 220-day intent therefore is not an achieved loaded-history assertion. This is disclosed; original strategy and parameters were not edited. Recursive startup stability remains a prerequisite for promotion, not an assumed PASS.

`evidence/*-trades.json` preserves full native trade rows. `evidence/native/*.zip` preserves native reports, configs and embedded original source. `RESULTS.json` independently reconciles trade PnL/counts and checks embedded source hash when available. Native reported realized DD is explicitly not a marked portfolio DD. The cash comparison is zero USDT interest, zero trading costs. No hypothetical interest benchmark is asserted.

Two initial attempts stopped at config schema validation before data simulation (disabled Telegram/API required schema fields). Only those offline harness fields were added; strategy untouched. They are not separate strategy trials.
