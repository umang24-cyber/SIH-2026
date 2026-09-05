"""
validate_pipeline.py
====================
SIH 2026 — Bitcoin Transaction Analysis Pipeline
Automated Dataset Validator & Data Dictionary Generator

Performs 5 critical integrity checks across:
  - data/processed/blockchain_transactions.csv
  - data/processed/network_metadata.csv

Generates:
  - data/DATASET_HANDOFF.md (Comprehensive team data dictionary)
"""

import os
import sys
import pandas as pd

# ─────────────────────────────────────────────
# 0. Paths
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROC_DIR = os.path.join(DATA_DIR, "processed")

BLOCKCHAIN_CSV = os.path.join(PROC_DIR, "blockchain_transactions.csv")
NETWORK_CSV    = os.path.join(PROC_DIR, "network_metadata.csv")
HANDOFF_MD     = os.path.join(DATA_DIR, "DATASET_HANDOFF.md")

# ─────────────────────────────────────────────
# 1. Load Processed Tables
# ─────────────────────────────────────────────
print("=" * 65)
print("🔍 SIH 2026 — AUTOMATED DATASET INTEGRITY VALIDATOR")
print("=" * 65)

if not os.path.exists(BLOCKCHAIN_CSV):
    print(f"❌ Error: {BLOCKCHAIN_CSV} does not exist!")
    sys.exit(1)

if not os.path.exists(NETWORK_CSV):
    print(f"❌ Error: {NETWORK_CSV} does not exist!")
    sys.exit(1)

df_block = pd.read_csv(BLOCKCHAIN_CSV)
df_net   = pd.read_csv(NETWORK_CSV)

# Convert timestamps for validation
df_block["timestamp"] = pd.to_datetime(df_block["timestamp"])
df_net["relay_timestamp"] = pd.to_datetime(df_net["relay_timestamp"])

# ─────────────────────────────────────────────
# 2. Run 5 Critical Integrity Checks
# ─────────────────────────────────────────────
results = []

# --- Check 1: Row Count Match ---
len_b = len(df_block)
len_n = len(df_net)
chk1_pass = (len_b == len_n)
results.append({
    "Check": "1. Row Count Match",
    "Expected": f"{len_b:,} rows",
    "Actual": f"Blockchain: {len_b:,} | Network: {len_n:,}",
    "Status": "✅ PASS" if chk1_pass else "❌ FAIL"
})

# --- Check 2: Key Alignment (0 Orphans) ---
set_b = set(df_block["txid"])
set_n = set(df_net["txid"])
orphan_in_net   = len(set_n - set_b)
orphan_in_block = len(set_b - set_n)
chk2_pass = (orphan_in_net == 0 and orphan_in_block == 0 and len(set_b) == len_b)
results.append({
    "Check": "2. Key Alignment (txid)",
    "Expected": "100% 1:1 match, 0 orphans",
    "Actual": f"Orphans: {orphan_in_net + orphan_in_block}, Unique txids: {len(set_b):,}",
    "Status": "✅ PASS" if chk2_pass else "❌ FAIL"
})

# --- Check 3: Timing Logic (relay <= blockchain) ---
merged_time = pd.merge(
    df_block[["txid", "timestamp"]],
    df_net[["txid", "relay_timestamp"]],
    on="txid",
    how="inner"
)
time_violations = (merged_time["relay_timestamp"] > merged_time["timestamp"]).sum()
chk3_pass = (time_violations == 0)
results.append({
    "Check": "3. Timing Logic",
    "Expected": "100% relay_timestamp <= timestamp",
    "Actual": f"{time_violations} timing violations",
    "Status": "✅ PASS" if chk3_pass else "❌ FAIL"
})

# --- Check 4: Null Values ---
nulls_b = df_block.isnull().sum().sum()
nulls_n = df_net.isnull().sum().sum()
chk4_pass = (nulls_b == 0 and nulls_n == 0)
results.append({
    "Check": "4. Null Values",
    "Expected": "0 nulls in all columns",
    "Actual": f"Blockchain: {nulls_b} | Network: {nulls_n}",
    "Status": "✅ PASS" if chk4_pass else "❌ FAIL"
})

# --- Check 5: Class Balance Verification ---
illicit_cnt = (df_block["is_illicit"] == 1).sum()
licit_cnt   = (df_block["is_illicit"] == 0).sum()
illicit_pct = (illicit_cnt / len_b) * 100
ransomware_cnt = (df_block["pattern_type"] == "ransomware").sum()
chk5_pass = (35 <= illicit_pct <= 50 and ransomware_cnt == illicit_cnt)
results.append({
    "Check": "5. Class Balance & Patterns",
    "Expected": "35-50% illicit & patterns aligned",
    "Actual": f"Illicit: {illicit_cnt:,} ({illicit_pct:.1f}%), Ransomware: {ransomware_cnt:,}",
    "Status": "✅ PASS" if chk5_pass else "❌ FAIL"
})

# ─────────────────────────────────────────────
# 3. Print Pass/Fail Report Table
# ─────────────────────────────────────────────
df_report = pd.DataFrame(results)
print("\n" + df_report.to_string(index=False))
print("-" * 65)

all_passed = all("PASS" in r["Status"] for r in results)
if all_passed:
    print("🎉 ALL 5 INTEGRITY CHECKS PASSED PERFECTLY!")
else:
    print("⚠️ SOME CHECKS FAILED — PLEASE REVIEW THE REPORT ABOVE.")
print("=" * 65)

# ─────────────────────────────────────────────
# 4. Generate data/DATASET_HANDOFF.md
# ─────────────────────────────────────────────
handoff_content = f"""# 🚀 SIH 2026 — Bitcoin Forensics Dataset Handoff & Data Dictionary

This document provides a comprehensive technical overview of the synchronized multi-layer Bitcoin dataset generated for the **SIH 2026 Bitcoin Transaction Forensics & Network Analysis System**.

---

## 📌 Dataset Overview

- **Primary Join Key:** `txid` (64-bit integer, 100% 1:1 mapped across both layers)
- **Total Records:** `{len_b:,}` transactions
- **Licit Transactions (`is_illicit = 0`):** `{licit_cnt:,}` ({(licit_cnt/len_b)*100:.2f}%)
- **Illicit Transactions (`is_illicit = 1`):** `{illicit_cnt:,}` ({(illicit_cnt/len_b)*100:.2f}%)
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
  - `:Wallet {{address: string}}`
  - `:Transaction {{txid: int, amount: float, timestamp: datetime, is_illicit: int, pattern: string}}`
  - `:IP {{address: string, country: string, asn: string, node_type: string}}`
- **Edge Relationships:**
  - `(:Wallet)-[:SENT {{amount: float, fee: float}}]->(:Transaction)`
  - `(:Transaction)-[:RECEIVED]->(:Wallet)`
  - `(:IP)-[:BROADCASTED {{relay_timestamp: datetime, port: int}}]->(:Transaction)`
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
"""

with open(HANDOFF_MD, "w", encoding="utf-8") as f:
    f.write(handoff_content)

print(f"📄 Data Dictionary generated and saved to:\n   {HANDOFF_MD}")
print("=" * 65)
