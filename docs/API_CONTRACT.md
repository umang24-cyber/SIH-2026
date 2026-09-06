# API Contract — Bitcoin AML Forensics Platform

> **Source-of-Truth Note:** Backend (P6) and Frontend (P1/P2) both build against this contract. Update this document **BEFORE** changing any endpoint signature, parameter, or response shape.
> **Offline Status:** 100% self-contained in-memory engine running on WSL2 / native Linux with zero runtime cloud dependencies.

---

## 1. Complete Endpoint Summary

All API endpoints strictly use field names and types specified in [DATA_DICTIONARY.md](../DATA_DICTIONARY.md).

| Method | Route | Description | Primary Owners |
|---|---|---|---|
| `GET` | `/health` | System telemetry, loaded transaction count, unique wallets, uptime. | P6 (Backend) |
| `GET` | `/entity/{address}` | Retrieve address metadata, transaction counts, and exchange flag. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/entity/{address}/cluster` | Retrieve Common-Input Ownership Heuristic (CIOH) co-owned wallet cluster. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/transaction/{txid}` | Retrieve full transaction details (on-chain multi-I/O UTXO + network telemetry). | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/transaction/{txid}/flow` | Structured input-to-output financial decomposition with entity cluster tags. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/graph/{scenario_id}` | Retrieve graph nodes (`Wallet`, `Transaction`, `IP`) and edges (`SENT`, `RECEIVED`, `BROADCAST`). | P4 (Graph), P6 (Backend), P2 (Graph UI) |
| `GET` | `/graph/{scenario_id}/communities` | Modularity-based syndicate & community detection on scenario graph. | P4 (Graph), P6 (Backend), P2 (Graph UI) |
| `GET` | `/trace` | Compute multi-hop shortest path between source and destination wallets. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/taint` | Forward dirty coin risk propagation (Haircut & FIFO models) with distance decay. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/alerts` | Retrieve prioritized list of forensic candidate alerts with ML predictions and explanations. | P5 (ML), P6 (Backend), P1 (Alert Feed) |
| `GET` | `/alerts/{candidate_id}/evidence` | Deep forensic evidence dossier and SHAP feature attribution breakdown. | P5 (ML/SHAP), P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/alerts/{candidate_id}/export` | Export formatted investigation summary for authorized review. | P6 (Backend) |
| `GET` | `/search` | Universal search across TxIDs, Wallet Addresses, IPs, ASNs, and Scenarios. | P6 (Backend), P1 (Search UI) |
| `GET` | `/scenarios` | Paginated scenario cluster explorer with transaction count and volume. | P6 (Backend), P1 (Dashboard) |
| `GET` | `/scenarios/{scenario_id}` | Deep forensic risk profile, infrastructure score, and hub wallets. | P6 (Backend), P1 (Dashboard) |
| `GET` | `/stats/telemetry` | Global network telemetry distribution (ASNs, node types, latency percentiles). | P6 (Backend), P1 (Dashboard) |
| `GET` | `/eval/benchmark` | Quantitative offline benchmark evaluation metrics (Precision, Recall, F1). | P5 (ML), P6 (Backend) |

---

## 2. Response Timing Header
Every endpoint returns an `X-Process-Time` HTTP header (e.g. `X-Process-Time: 0.45ms`), confirming sub-millisecond execution times.
