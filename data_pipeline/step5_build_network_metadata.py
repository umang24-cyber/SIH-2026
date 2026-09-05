"""
step5_build_network_metadata.py
================================
SIH 2026 — Bitcoin Transaction Analysis Pipeline
Step 5: Network Layer Metadata Generator

Sub-task 1: Setup and Reference Pools
  - Loads txid, timestamp, is_illicit from blockchain_transactions.csv
  - Defines node types, ASNs (licit & suspicious), and user agents
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# 0. Paths
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

# ─────────────────────────────────────────────
# 1. Load Blockchain Transactions (txid, timestamp, is_illicit)
# ─────────────────────────────────────────────
tx_path = os.path.join(PROC_DIR, "blockchain_transactions.csv")
df_tx = pd.read_csv(tx_path, usecols=["txid", "timestamp", "is_illicit"])

# Convert timestamp to datetime
df_tx["timestamp"] = pd.to_datetime(df_tx["timestamp"])

# ─────────────────────────────────────────────
# 2. Define Reference Pools & Distributions
# ─────────────────────────────────────────────

# --- Node Types & Distribution Weights ---
LICIT_NODE_TYPES = ["residential", "datacenter", "mobile"]
LICIT_NODE_WEIGHTS = [0.70, 0.25, 0.05]

ILLICIT_NODE_TYPES = ["tor_exit_node", "vpn_proxy", "bulletproof_host", "residential"]
ILLICIT_NODE_WEIGHTS = [0.45, 0.35, 0.15, 0.05]

# --- Autonomous System Numbers (ASNs) ---
# Normal / Legitimate ASNs with Org Name & typical Country
NORMAL_ASNS = [
    {"asn": "AS15169", "isp": "Google LLC", "country": "US"},
    {"asn": "AS7922",  "isp": "Comcast Cable Communications", "country": "US"},
    {"asn": "AS3215",  "isp": "Orange S.A.", "country": "FR"},
    {"asn": "AS55836", "isp": "Reliance Jio Infocomm", "country": "IN"},
    {"asn": "AS16509", "isp": "Amazon.com, Inc.", "country": "US"},
    {"asn": "AS13335", "isp": "Cloudflare, Inc.", "country": "US"},
    {"asn": "AS6830",  "isp": "Liberty Global Operations", "country": "NL"},
    {"asn": "AS4713",  "isp": "NTT Communications", "country": "JP"}
]

# Suspicious / Bulletproof / VPN / Tor ASNs
SUSPICIOUS_ASNS = [
    {"asn": "AS9009",   "isp": "M247 Ltd", "country": "RO"},
    {"asn": "AS60068",  "isp": "Datacamp Limited", "country": "GB"},
    {"asn": "AS200052", "isp": "Tor-Relay-Network", "country": "DE"},
    {"asn": "AS44050",  "isp": "Petersburg Internet Network", "country": "RU"},
    {"asn": "AS204957", "isp": "Green Floid LLC (Bulletproof)", "country": "SC"},
    {"asn": "AS49870",  "isp": "Alentus Corporation (Darknet Proxy)", "country": "BZ"},
    {"asn": "AS210644", "isp": "AEZA International LTD", "country": "RU"}
]

# --- Bitcoin Node User Agents ---
USER_AGENTS = [
    "/Satoshi:22.0.0/",
    "/Satoshi:21.1.0/",
    "/Satoshi:0.20.1/",
    "/btcd:0.22.0/"
]

USER_AGENT_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

# ─────────────────────────────────────────────
# 3. Summary & Verification
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 1 — Setup & Reference Pools Loaded")
print("=" * 50)
print(f"  Total records loaded : {len(df_tx):,}")
print(f"  Timestamp range      : {df_tx['timestamp'].min()} -> {df_tx['timestamp'].max()}")
print("\nis_illicit distribution:")
print(df_tx["is_illicit"].value_counts().to_string())
print("\nis_illicit percentage:")
print((df_tx["is_illicit"].value_counts(normalize=True) * 100).round(2).to_string())
print(f"\n  Normal ASNs pool size      : {len(NORMAL_ASNS)}")
print(f"  Suspicious ASNs pool size  : {len(SUSPICIOUS_ASNS)}")
print(f"  Licit Node Types           : {LICIT_NODE_TYPES}")
print(f"  Illicit Node Types         : {ILLICIT_NODE_TYPES}")
print(f"  User Agents pool size      : {len(USER_AGENTS)}")
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 2 — Generate Correlated Network Attributes
# ═══════════════════════════════════════════════════════

n_total = len(df_tx)

# 1. relay_timestamp: 50ms to 500ms before blockchain timestamp
random_ms = np.random.randint(50, 501, size=n_total)
df_tx["relay_timestamp"] = df_tx["timestamp"] - pd.to_timedelta(random_ms, unit="ms")

# Helper function to generate realistic IPv4 addresses
def gen_ipv4(count: int) -> list:
    """Generate plausible public IPv4 addresses."""
    o1 = np.random.choice(
        [np.random.randint(11, 100), np.random.randint(101, 126), np.random.randint(128, 223)],
        size=count
    )
    o2 = np.random.randint(1, 255, size=count)
    o3 = np.random.randint(1, 255, size=count)
    o4 = np.random.randint(1, 255, size=count)
    return [f"{a}.{b}.{c}.{d}" for a, b, c, d in zip(o1, o2, o3, o4)]

# 2. Correlated Node Type, ASN, Country Code, and Relay IP
licit_mask = (df_tx["is_illicit"] == 0)
illicit_mask = (df_tx["is_illicit"] == 1)
n_licit = int(licit_mask.sum())
n_illicit = int(illicit_mask.sum())

# Assign node_type
df_tx.loc[licit_mask, "node_type"] = np.random.choice(LICIT_NODE_TYPES, size=n_licit, p=LICIT_NODE_WEIGHTS)
df_tx.loc[illicit_mask, "node_type"] = np.random.choice(ILLICIT_NODE_TYPES, size=n_illicit, p=ILLICIT_NODE_WEIGHTS)

# Assign ASN, Country Code, and ISP
sampled_normal_asns = np.random.choice(NORMAL_ASNS, size=n_licit)
df_tx.loc[licit_mask, "asn"] = [item["asn"] for item in sampled_normal_asns]
df_tx.loc[licit_mask, "country_code"] = [item["country"] for item in sampled_normal_asns]
df_tx.loc[licit_mask, "isp"] = [item["isp"] for item in sampled_normal_asns]

sampled_suspicious_asns = np.random.choice(SUSPICIOUS_ASNS, size=n_illicit)
df_tx.loc[illicit_mask, "asn"] = [item["asn"] for item in sampled_suspicious_asns]
df_tx.loc[illicit_mask, "country_code"] = [item["country"] for item in sampled_suspicious_asns]
df_tx.loc[illicit_mask, "isp"] = [item["isp"] for item in sampled_suspicious_asns]

# Assign relay_ip
df_tx["relay_ip"] = gen_ipv4(n_total)

# 3. relay_port: 85% standard port 8333, 15% dynamic/alt ports
is_standard_port = np.random.rand(n_total) < 0.85
alt_ports = np.random.choice([18333] + list(range(49152, 65536, 64)), size=n_total)
df_tx["relay_port"] = np.where(is_standard_port, 8333, alt_ports)

# 4. protocol_version and user_agent
df_tx["protocol_version"] = 70015
df_tx["user_agent"] = np.random.choice(USER_AGENTS, size=n_total, p=USER_AGENT_WEIGHTS)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 2 — Correlated Network Metadata Generated")
print("=" * 50)
print(f"  Columns present: {df_tx.columns.tolist()}\n")
print("First 5 rows:")
print(df_tx[["txid", "relay_timestamp", "relay_ip", "relay_port", "node_type", "asn", "country_code"]].head().to_string())

print("\nNode Type Distribution by is_illicit (counts):")
print(pd.crosstab(df_tx["node_type"], df_tx["is_illicit"], margins=True))

print("\nNode Type Distribution by is_illicit (% within group):")
print((pd.crosstab(df_tx["node_type"], df_tx["is_illicit"], normalize="columns") * 100).round(2))
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 3 — Save Final network_metadata.csv
# ═══════════════════════════════════════════════════════

# 1. Select and reorder network-layer columns
final_network_cols = [
    "txid",
    "relay_timestamp",
    "relay_ip",
    "relay_port",
    "node_type",
    "country_code",
    "asn",
    "isp",
    "protocol_version",
    "user_agent"
]
df_network = df_tx[final_network_cols].copy()

# 2. Save to data/processed/network_metadata.csv
output_file_path = os.path.join(PROC_DIR, "network_metadata.csv")
df_network.to_csv(output_file_path, index=False)

# 3. Print completion summary
print("=" * 50)
print("SUB-TASK 3 — Network Metadata Pipeline Complete & File Saved")
print("=" * 50)
print(f"  File saved to       : {output_file_path}")
print(f"  Total rows saved    : {len(df_network):,}")
print(f"  Total columns saved : {len(df_network.columns)}")
print(f"  Columns list        : {df_network.columns.tolist()}\n")

print("First 5 rows of final network metadata table:")
print(df_network.head().to_string())
print("=" * 50)
print("🎉 Step 5 network metadata generation complete!")
print("=" * 50)
