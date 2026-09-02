"""
validate_v2.py
==============
SIH 2026 — Bitcoin AML Dataset v2.0 Validator

Performs 15 integrity checks across the v2.0 dataset files:
  - data/processed/blockchain_transactions.csv
  - data/processed/network_metadata.csv

Checks:
  1.  Row count match
  2.  Key alignment (0 orphans)
  3.  Duplicate txids
  4.  Timing logic (relay_timestamp <= timestamp)
  5.  Null values
  6.  Array column validity (JSON parse, length consistency)
  7.  Accounting identity (sum(inputs) ≈ sum(outputs) + fee)
  8.  Typology distribution (all 5 pattern_types present)
  9.  Scenario_id coverage (no nulls)
  10. Hard negatives (licit wallets with >=50 txns)
  11. Network decorrelation (pools overlap)
  12. Txid uniformity (no contiguous label-correlated blocks)
  13. Timestamp overlap (both classes in 2011-2016 AND 2017-2018)
  14. Split integrity (no scenario in both train and test)
  15. Split stratification (similar illicit ratios)

Usage:
    python data_pipeline/validate_v2.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# 0. Paths
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

BLOCKCHAIN_CSV = os.path.join(PROC_DIR, "blockchain_transactions.csv")
NETWORK_CSV = os.path.join(PROC_DIR, "network_metadata.csv")

# ─────────────────────────────────────────────
# 1. Load
# ─────────────────────────────────────────────
print("=" * 70)
print("🔍 SIH 2026 — v2.0 DATASET INTEGRITY VALIDATOR")
print("=" * 70)

for path in [BLOCKCHAIN_CSV, NETWORK_CSV]:
    if not os.path.exists(path):
        print(f"❌ Error: {path} does not exist!")
        sys.exit(1)

df_b = pd.read_csv(BLOCKCHAIN_CSV)
df_n = pd.read_csv(NETWORK_CSV)

results = []

def add_result(name, expected, actual, passed):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append({"Check": name, "Expected": expected, "Actual": actual, "Status": status})
    return passed

# ─────────────────────────────────────────────
# Check 1: Row Count Match
# ─────────────────────────────────────────────
add_result(
    "1. Row Count Match",
    "blockchain rows == network rows",
    f"Blockchain: {len(df_b):,} | Network: {len(df_n):,}",
    len(df_b) == len(df_n),
)

# ─────────────────────────────────────────────
# Check 2: Key Alignment (0 orphans)
# ─────────────────────────────────────────────
set_b = set(df_b["txid"])
set_n = set(df_n["txid"])
orphan_b = len(set_b - set_n)
orphan_n = len(set_n - set_b)
add_result(
    "2. Key Alignment",
    "0 orphan txids",
    f"Orphans: B→N={orphan_b}, N→B={orphan_n}",
    orphan_b == 0 and orphan_n == 0,
)

# ─────────────────────────────────────────────
# Check 3: Duplicate txids
# ─────────────────────────────────────────────
dup_b = df_b["txid"].duplicated().sum()
dup_n = df_n["txid"].duplicated().sum()
add_result(
    "3. Duplicate txids",
    "0 duplicates",
    f"Blockchain: {dup_b}, Network: {dup_n}",
    dup_b == 0 and dup_n == 0,
)

# ─────────────────────────────────────────────
# Check 4: Timing Logic
# ─────────────────────────────────────────────
merged = pd.merge(
    df_b[["txid", "timestamp"]],
    df_n[["txid", "relay_timestamp"]],
    on="txid",
    how="inner",
)
merged["timestamp"] = pd.to_datetime(merged["timestamp"])
merged["relay_timestamp"] = pd.to_datetime(merged["relay_timestamp"])
time_violations = (merged["relay_timestamp"] > merged["timestamp"]).sum()
add_result(
    "4. Timing Logic",
    "0 violations (relay <= block)",
    f"{time_violations} violations",
    time_violations == 0,
)

# ─────────────────────────────────────────────
# Check 5: Null Values
# ─────────────────────────────────────────────
nulls_b = df_b.isnull().sum().sum()
nulls_n = df_n.isnull().sum().sum()
add_result(
    "5. Null Values",
    "0 nulls",
    f"Blockchain: {nulls_b}, Network: {nulls_n}",
    nulls_b == 0 and nulls_n == 0,
)

# ─────────────────────────────────────────────
# Check 6: Array Column Validity
# ─────────────────────────────────────────────
array_cols = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]
array_valid = True
array_errors = []

for col in array_cols:
    try:
        parsed = df_b[col].apply(json.loads)
        # Check all are lists
        non_lists = (~parsed.apply(lambda x: isinstance(x, list))).sum()
        if non_lists > 0:
            array_errors.append(f"{col}: {non_lists} non-list entries")
            array_valid = False
        # Check non-empty
        empties = (parsed.apply(len) == 0).sum()
        if empties > 0:
            array_errors.append(f"{col}: {empties} empty arrays")
            array_valid = False
    except Exception as e:
        array_errors.append(f"{col}: JSON parse error: {e}")
        array_valid = False

# Check length consistency within rows
if array_valid:
    in_addr_len = df_b["input_addresses"].apply(lambda x: len(json.loads(x)))
    in_amt_len = df_b["input_amounts"].apply(lambda x: len(json.loads(x)))
    out_addr_len = df_b["output_addresses"].apply(lambda x: len(json.loads(x)))
    out_amt_len = df_b["output_amounts"].apply(lambda x: len(json.loads(x)))

    mismatches_in = (in_addr_len != in_amt_len).sum()
    mismatches_out = (out_addr_len != out_amt_len).sum()
    if mismatches_in > 0 or mismatches_out > 0:
        array_errors.append(f"Length mismatches: input={mismatches_in}, output={mismatches_out}")
        array_valid = False

add_result(
    "6. Array Columns",
    "Valid JSON, consistent lengths",
    "; ".join(array_errors) if array_errors else "All valid",
    array_valid,
)

# ─────────────────────────────────────────────
# Check 7: Accounting Identity
# ─────────────────────────────────────────────
in_sums = df_b["input_amounts"].apply(lambda x: sum(json.loads(x)))
out_sums = df_b["output_amounts"].apply(lambda x: sum(json.loads(x)))
fees = df_b["fee_btc"]
residuals = np.abs(in_sums - out_sums - fees)
acct_violations = (residuals > 1e-4).sum()
add_result(
    "7. Accounting Identity",
    "sum(in) ≈ sum(out) + fee (tol 1e-4)",
    f"{acct_violations} violations (max residual: {residuals.max():.8f})",
    acct_violations == 0,
)

# ─────────────────────────────────────────────
# Check 8: Typology Distribution
# ─────────────────────────────────────────────
expected_types = {"normal", "ransomware", "peeling_chain", "layering", "mixing"}
actual_types = set(df_b["pattern_type"].unique())
missing = expected_types - actual_types
extra = actual_types - expected_types
add_result(
    "8. Typology Distribution",
    f"5 types: {sorted(expected_types)}",
    f"Found: {sorted(actual_types)}, Missing: {sorted(missing)}, Extra: {sorted(extra)}",
    missing == set() and extra == set(),
)

# ─────────────────────────────────────────────
# Check 9: Scenario_id Coverage
# ─────────────────────────────────────────────
null_scenarios = df_b["scenario_id"].isnull().sum()
add_result(
    "9. Scenario_id Coverage",
    "0 null scenario_ids",
    f"{null_scenarios} nulls",
    null_scenarios == 0,
)

# ─────────────────────────────────────────────
# Check 10: Hard Negatives
# ─────────────────────────────────────────────
# Count licit wallets appearing in >=50 txns (as input)
all_licit = df_b[df_b["is_illicit"] == 0]
licit_input_wallets = []
for addrs_json in all_licit["input_addresses"]:
    for a in json.loads(addrs_json):
        licit_input_wallets.append(a)

licit_wallet_counts = pd.Series(licit_input_wallets).value_counts()
high_activity_licit = (licit_wallet_counts >= 50).sum()
add_result(
    "10. Hard Negatives",
    ">=25 licit wallets with >=50 txns",
    f"{high_activity_licit} licit wallets with >=50 txns",
    high_activity_licit >= 25,
)

# ─────────────────────────────────────────────
# Check 11: Network Decorrelation
# ─────────────────────────────────────────────
merged_labels = pd.merge(df_b[["txid", "is_illicit"]], df_n[["txid", "node_type"]], on="txid")
# Check that suspicious types appear in licit rows
suspicious_types = {"tor_exit_node", "vpn_proxy", "bulletproof_host"}
licit_node_types = set(merged_labels[merged_labels["is_illicit"] == 0]["node_type"].unique())
illicit_node_types = set(merged_labels[merged_labels["is_illicit"] == 1]["node_type"].unique())

susp_in_licit = suspicious_types & licit_node_types
normal_in_illicit = {"datacenter", "mobile"} & illicit_node_types

decorr_ok = len(susp_in_licit) > 0 and len(normal_in_illicit) > 0
add_result(
    "11. Network Decorrelation",
    "Suspicious types in licit + normal in illicit",
    f"Susp in licit: {sorted(susp_in_licit)}, Normal in illicit: {sorted(normal_in_illicit)}",
    decorr_ok,
)

# ─────────────────────────────────────────────
# Check 12: Txid Uniformity
# ─────────────────────────────────────────────
sorted_by_txid = df_b.sort_values("txid").reset_index(drop=True)
# Check rolling window of 500 consecutive txids
window = 500
max_label_concentration = 0.0
for start in range(0, len(sorted_by_txid) - window, window):
    chunk = sorted_by_txid.iloc[start:start + window]
    illicit_pct = chunk["is_illicit"].mean()
    max_label_concentration = max(max_label_concentration, illicit_pct)

# A perfectly leaked dataset would have 100% concentration; OK threshold: <80%
txid_ok = max_label_concentration < 0.80
add_result(
    "12. Txid Uniformity",
    "No block of 500 consecutive txids >80% same label",
    f"Max illicit concentration in 500-txid window: {max_label_concentration:.1%}",
    txid_ok,
)

# ─────────────────────────────────────────────
# Check 13: Timestamp Overlap
# ─────────────────────────────────────────────
df_b["_ts"] = pd.to_datetime(df_b["timestamp"])
licit_years = df_b[df_b["is_illicit"] == 0]["_ts"].dt.year
illicit_years = df_b[df_b["is_illicit"] == 1]["_ts"].dt.year

licit_has_early = (licit_years < 2017).any()
licit_has_late = (licit_years >= 2017).any()
illicit_has_early = (illicit_years < 2017).any()
illicit_has_late = (illicit_years >= 2017).any()

ts_overlap = licit_has_early and licit_has_late and illicit_has_early and illicit_has_late
add_result(
    "13. Timestamp Overlap",
    "Both classes span 2011-2016 AND 2017-2018",
    f"Licit early: {licit_has_early}, late: {licit_has_late}; Illicit early: {illicit_has_early}, late: {illicit_has_late}",
    ts_overlap,
)
df_b.drop(columns=["_ts"], inplace=True)

# ─────────────────────────────────────────────
# Check 14: Split Integrity
# ─────────────────────────────────────────────
train_scenarios = set(df_b[df_b["split"] == "train"]["scenario_id"].unique())
test_scenarios = set(df_b[df_b["split"] == "test"]["scenario_id"].unique())
leak_scenarios = train_scenarios & test_scenarios
add_result(
    "14. Split Integrity",
    "0 scenarios in both train and test",
    f"{len(leak_scenarios)} leaking scenarios",
    len(leak_scenarios) == 0,
)

# ─────────────────────────────────────────────
# Check 15: Split Stratification
# ─────────────────────────────────────────────
train_illicit_pct = df_b[df_b["split"] == "train"]["is_illicit"].mean() * 100
test_illicit_pct = df_b[df_b["split"] == "test"]["is_illicit"].mean() * 100
pct_diff = abs(train_illicit_pct - test_illicit_pct)
add_result(
    "15. Split Stratification",
    "Train/test illicit % within 5pp",
    f"Train: {train_illicit_pct:.1f}%, Test: {test_illicit_pct:.1f}% (diff: {pct_diff:.1f}pp)",
    pct_diff <= 5.0,
)

# ─────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────
print()
df_report = pd.DataFrame(results)
print(df_report.to_string(index=False))
print("-" * 70)

all_passed = all("PASS" in r["Status"] for r in results)
n_passed = sum(1 for r in results if "PASS" in r["Status"])
n_total = len(results)

if all_passed:
    print(f"🎉 ALL {n_total} INTEGRITY CHECKS PASSED!")
else:
    print(f"⚠️  {n_passed}/{n_total} CHECKS PASSED — REVIEW FAILURES ABOVE")

# ─────────────────────────────────────────────
# Additional Statistics
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("📊 DATASET STATISTICS")
print("=" * 70)
print(f"  Total rows: {len(df_b):,}")
print(f"\nis_illicit distribution:")
print(df_b["is_illicit"].value_counts().to_string())
print(f"\npattern_type distribution:")
print(df_b["pattern_type"].value_counts().to_string())
print(f"\nsplit distribution:")
print(df_b["split"].value_counts().to_string())
print(f"\nscenario_id count: {df_b['scenario_id'].nunique():,}")

# Array size statistics
in_sizes = df_b["input_addresses"].apply(lambda x: len(json.loads(x)))
out_sizes = df_b["output_addresses"].apply(lambda x: len(json.loads(x)))
print(f"\nInput addresses per txn:  min={in_sizes.min()}, median={in_sizes.median():.0f}, max={in_sizes.max()}")
print(f"Output addresses per txn: min={out_sizes.min()}, median={out_sizes.median():.0f}, max={out_sizes.max()}")

# Wallet reuse stats
all_input_addrs = []
for addrs_json in df_b["input_addresses"]:
    for a in json.loads(addrs_json):
        all_input_addrs.append(a)
wallet_counts = pd.Series(all_input_addrs).value_counts()
print(f"\nWallet reuse (as input):")
print(f"  Wallets with 1 txn   : {(wallet_counts == 1).sum():,}")
print(f"  Wallets with 2-10 txn: {((wallet_counts >= 2) & (wallet_counts <= 10)).sum():,}")
print(f"  Wallets with 11+ txn : {(wallet_counts > 10).sum():,}")
print(f"  Max txns per wallet  : {wallet_counts.max():,}")

print("=" * 70)
