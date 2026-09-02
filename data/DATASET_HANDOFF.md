# 🚀 SIH 2026 — Bitcoin Forensics Dataset Handoff & Data Dictionary

This document provides a comprehensive technical overview of the synchronized multi-layer Bitcoin dataset generated for the **SIH 2026 Bitcoin Transaction Forensics & Network Analysis System**.

---

## 📌 Dataset Overview

- **Primary Join Key:** `txid` (64-bit integer, 100% 1:1 mapped across both layers)
- **Total Records:** `71,564` transactions
- **Licit Transactions (`is_illicit = 0`):** `42,019` (58.72%)
- **Illicit Transactions (`is_illicit = 1`):** `29,545` (41.28%)
- **Data Period:** `2011-09-03` to `2018-11-17`

---

## 📁 Files & Schemas

### 1. `data/processed/blockchain_transactions.csv`
Contains the on-chain ledger state, financial amounts, wallet addresses, and ground-truth crime labels.

| Column | Type | Description | Example / Values |
|---|---|---|---|
| `txid` | `int64` | **Primary Key**: Unique identifier for the Bitcoin transaction | `245355036` |
| `timestamp` | `datetime` | Timestamp when the transaction was confirmed on-chain | `2017-01-29 18:27:29` |
| `input_wallet` | `string` | Base58 sender wallet address (real Heist address for illicit) | `1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh` |
| `output_wallet` | `string` | Base58 receiver wallet address | `1EcgU6KKSdjtWmXzy5W3EX34ibCoH` |
| `amount_btc` | `float64` | Transaction value in BTC (lognormal distribution, 8 decimals) | `0.26326308` |
| `fee_btc` | `float64` | Miner fee in BTC (uniform 0.00001 - 0.0005) | `0.00035108` |
| `script_type` | `string` | Bitcoin script format | `P2PKH`, `P2SH`, `P2WPKH`, `P2WSH` |
| `is_illicit` | `int` | Binary ground-truth label (`0` = Licit, `1` = Illicit/Criminal) | `0` or `1` |
| `pattern_type` | `string` | Specific threat category | `normal`, `ransomware`, `layering`, `mixing`, `chain_hop` |

---

### 2. `data/processed/network_metadata.csv`
Contains the P2P broadcast and network telemetry captured before block confirmation.

| Column | Type | Description | Example / Values |
|---|---|---|---|
| `txid` | `int64` | **Foreign Key**: Links 1:1 to `blockchain_transactions.csv` | `245355036` |
| `relay_timestamp` | `datetime` | P2P broadcast timestamp (50ms–500ms before `timestamp`) | `2017-01-29 18:27:28.545` |
| `relay_ip` | `string` | First-seen relay peer IPv4 address | `119.11.219.103` |
| `relay_port` | `int` | Peer connection port | `8333` (standard) or dynamic (`18333`, `49152+`) |
| `node_type` | `string` | Originating network infrastructure | `residential`, `datacenter`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`, `mobile` |
| `country_code` | `string` | ISO 3166-1 alpha-2 origin country code | `US`, `DE`, `IN`, `RU`, `BZ`, `FR`, `JP`, etc. |
| `asn` | `string` | Autonomous System Number of the relay node | `AS15169`, `AS55836`, `AS210644`, `AS9009`, etc. |
| `isp` | `string` | Internet Service Provider or hosting entity name | `Google LLC`, `Reliance Jio`, `AEZA International`, etc. |
| `protocol_version`| `int` | Bitcoin protocol version | `70015` |
| `user_agent` | `string` | Client node software banner | `/Satoshi:22.0.0/`, `/Satoshi:21.1.0/`, `/btcd:0.22.0/` |

---

## 🛠️ Role-Specific Implementation Guide

### 🧑‍💻 1. Backend Engineer (APIs & Database Ingestion)
- **Database Indexing:**
  - Create Primary Key on `txid` on both tables.
  - Add secondary indexes on `input_wallet`, `output_wallet`, `relay_ip`, and `timestamp`.
- **Fast Lookup Endpoint:**
  - Build `GET /api/v1/tx/:txid` joining both tables:
    ```sql
    SELECT b.*, n.relay_ip, n.relay_timestamp, n.node_type, n.asn, n.isp
    FROM blockchain_transactions b
    JOIN network_metadata n ON b.txid = n.txid
    WHERE b.txid = :txid;
    ```
- **Live Search Filters:**
  - Filter by `is_illicit`, `node_type`, `country_code`, or address search.

---

### 🕸️ 2. Graph Engineer (Neo4j / NetworkX / Link Analysis)
- **Node Entities:**
  - `:Wallet {address: string}`
  - `:Transaction {txid: int, amount: float, timestamp: datetime, is_illicit: int, pattern: string}`
  - `:IP {address: string, country: string, asn: string, node_type: string}`
- **Edge Relationships:**
  - `(:Wallet)-[:SENT {amount: float, fee: float}]->(:Transaction)`
  - `(:Transaction)-[:RECEIVED]->(:Wallet)`
  - `(:IP)-[:BROADCASTED {relay_timestamp: datetime, port: int}]->(:Transaction)`
- **Graph Traversal / Subgraph Extraction:**
  - Trace multi-hop laundering chains from high-risk Tor/VPN nodes across 3 to 5 hops.

---

### 🤖 3. Machine Learning Engineer (Dual-Layer Threat Detection)
- **Feature Matrix:**
  - **On-Chain Features:** `amount_btc`, `fee_btc`, fee-to-amount ratio, `script_type` (One-Hot), in-degree/out-degree from graph.
  - **Off-Chain / Network Features:** `node_type` (One-Hot / Target Encoded), `asn` risk score, relay delta `(timestamp - relay_timestamp)` in milliseconds.
- **Target:** `is_illicit` (Binary classification) and `pattern_type` (Multi-class threat categorization).
- **Validation Split:** Use time-based splitting (`train: 2011-2017`, `test: 2018`) to simulate realistic zero-day detection.

---

### 🎨 4. Frontend Developer (Dashboard, Threat Map & Visualizer)
- **Threat Map Component:** Plot transactions on a global choropleth map using `country_code` and color-code by `node_type` (Red for `tor_exit_node` / `bulletproof_host`, Green for `residential`).
- **Transaction Detail Drawer:** Display dual-card comparison:
  - *Left Card (On-Chain):* Wallets, BTC amount, confirmation time, Script type.
  - *Right Card (Network Relay):* Origin IP, ASN, ISP, User Agent, Network Latency Delta.
- **Badge Indicators:** Distinct badges for `ransomware` (Red), `mixing` (Orange), and `normal` (Green).

---
*Generated automatically by `data_pipeline/validate_pipeline.py`*
