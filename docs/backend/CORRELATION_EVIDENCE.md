# Correlation evidence contract (two-file upload and stream reconciliation)

## What an association means

`/api/ingest/correlate` matches ledger and network observations by their **original transaction ID** (`txid` or hash), not by time proximity. `/api/stream/reconcile` uses the same ID and evidence rules. The internal integer ID used by existing graph/ML storage is separate; conflicting internal IDs are rejected before indexing. Records lacking an original ID are rejected on upload. Two different IDs with identical timestamps never become an exact match.

The timestamp interval is **ledger/block timestamp minus earliest recorded relay observation**, in seconds. It is *not* the elapsed time between an originating sender and the network. A negative interval indicates clock ordering/definition concerns. Matching is retained for out-of-window intervals; the configured window (default 120 s, positive finite seconds) is a **timing display/quality flag**, not a match cutoff.

## Two-file upload

`POST /api/ingest/correlate` accepts `ledger_file`, `network_file` CSV multipart fields and optional `max_window_seconds` query parameter. Existing response fields remain, with:

- `correlation_rate`: exact-ID matched records / max(unique ledger IDs, unique network IDs). **Coverage, not confidence.**
- `timing_issue_count`: exact-ID matched records whose timing status is not `WITHIN_WINDOW`.
- `conflicting_records`: repeated ledger IDs with contradictory ledger facts. These are not indexed or scored.
- `correlation_evidence`: one row per match, ledger-only, network-only or conflicting ID. Network-only rows are *not* fabricated into ledger transactions. Repeated network observations are preserved in `observations` (and on the persisted matched transaction).

Ledger-only rows can still be indexed for graph inspection, but upload-time ML analysis is `UNAVAILABLE` for any scenario containing a ledger transaction without matched network telemetry **or observed timestamps**; an incomplete dual-stream scenario is not scored using invented timing/relay evidence.

Each evidence row contains `transaction_hash`, `txid` (numeric internal ID or null), `match_method` (`EXACT_TRANSACTION_ID` or `NONE`), `match_status` (`MATCHED`, `UNMATCHED`, `CONFLICTING`), `ledger_timestamp` (UTC or null), `observations[]` (`relay_timestamp`, `relay_ip`, `asn`, `node_type`, each nullable), `timing_delta_seconds` (signed or null), `timing_status` (`WITHIN_WINDOW`, `OUTSIDE_WINDOW`, `CLOCK_ORDER_ISSUE`, `MISSING_TIMESTAMP`), `correlation_confidence: null`, `attribution_status`, and `reasons[]`.

`correlation_confidence` is deliberately null: no calibrated matching probability exists. `risk_score` and `typology_confidence` in `scenario_results` are **V8 scenario-level ML outputs, unrelated to transaction association or sender identity**. Relay IP describes an observation, not proven origin.

## Stream reconciliation

`POST /api/stream/reconcile` accepts `mempool_stream`, `block_stream` arrays and optional `max_window_seconds`. Exact-ID matched and orphan events carry the same evidence fields, plus existing stream fields (`correlation_status`, `btc_value`, etc.). Summary `correlated_matches` counts all non-conflicting exact-ID matches; `within_window_matches` counts the timing-consistent subset, `timing_issue_count` counts the remainder, and `conflicting_records` counts contradictory repeated block IDs. A repeated relay ID preserves every observation; out-of-order stream input is accepted.

## Limitations and follow-up

This is **not timing-only inference**, a sender-identification model, nor a calibrated forensic confidence estimator. The upload endpoint accepts unique original IDs and rejects collisions in its numeric legacy index; existing non-correlation endpoints still expose numeric `txid`. If a labelled correlation dataset becomes available, evaluate candidate matching separately from these deterministic exact-ID joins before introducing a probability. The legacy app's scenario ML inference and full Linux-offline packaging are separate deliverables.
