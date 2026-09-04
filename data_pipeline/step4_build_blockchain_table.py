"""
step4_build_blockchain_table.py
================================
SIH 2026 — Bitcoin Transaction Analysis Pipeline

Sub-task 1: Load and clean the Elliptic classes data.
  - Removes 'unknown' labelled rows
  - Encodes class: 1 (illicit) stays 1, 2 (licit) becomes 0
  - Renames columns: txId -> txid, class -> is_illicit
"""

import os
import random
import string

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR  = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(PROC_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Step 1 — Load raw classes CSV
# ─────────────────────────────────────────────
classes_path = os.path.join(RAW_DIR, "elliptic_txs_classes.csv")
df_classes   = pd.read_csv(classes_path)

# ─────────────────────────────────────────────
# Step 2 — Remove rows where class == "unknown"
# ─────────────────────────────────────────────
df_classes = df_classes[df_classes["class"] != "unknown"].copy()

# ─────────────────────────────────────────────
# Step 3 — Encode labels
#   class 1 (illicit)   → 1  (no change)
#   class 2 (licit)     → 0
# ─────────────────────────────────────────────
df_classes["class"] = df_classes["class"].astype(int)          # "1"/"2" strings → int
df_classes["class"] = df_classes["class"].replace({2: 0})      # licit → 0

# ─────────────────────────────────────────────
# Step 4 — Rename columns
# ─────────────────────────────────────────────
df_classes.rename(columns={"txId": "txid", "class": "is_illicit"}, inplace=True)

# ─────────────────────────────────────────────
# Step 5 — Reset index
# ─────────────────────────────────────────────
df_classes.reset_index(drop=True, inplace=True)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 1 — Classes Data: Load & Clean")
print("=" * 50)
print(f"  Total rows kept  : {len(df_classes):,}")
print(f"  is_illicit = 0   : {(df_classes['is_illicit'] == 0).sum():,}  (licit)")
print(f"  is_illicit = 1   : {(df_classes['is_illicit'] == 1).sum():,}  (illicit)")
print(f"\n  First 5 rows:")
print(df_classes.head())
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 2 — Add Timestamps from Features File
# ═══════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Step 1 — Load ONLY txid + time_step columns
# ─────────────────────────────────────────────
features_path = os.path.join(RAW_DIR, "elliptic_txs_features.csv")

df_time = pd.read_csv(
    features_path,
    header=None,       # no header row in this file
    usecols=[0, 1],    # first two columns only
    names=["txid", "time_step"]
)

# ─────────────────────────────────────────────
# Step 2 — Left join onto df_classes on 'txid'
#   Keep all 46k labelled rows; unmatched → NaN
# ─────────────────────────────────────────────
df_classes = df_classes.merge(df_time, on="txid", how="left")

# ─────────────────────────────────────────────
# Step 3 — Convert time_step → timestamp
#   Base date: 2017-01-01 (time_step 1)
#   Each step = 14 days
#   Add random jitter (0 – 1,209,600 seconds) per row
# ─────────────────────────────────────────────
base_date = pd.Timestamp("2017-01-01")

# Vectorised: compute the base datetime for each row's time_step
step_offsets = pd.to_timedelta((df_classes["time_step"] - 1) * 14, unit="D")

# Random jitter in seconds (reproducible with a fixed seed)
rng = np.random.default_rng(seed=42)
jitter_seconds = rng.integers(0, 1_209_601, size=len(df_classes))   # 0 to 1,209,600 inclusive
jitter_offsets = pd.to_timedelta(jitter_seconds, unit="s")

df_classes["timestamp"] = base_date + step_offsets + jitter_offsets

# ─────────────────────────────────────────────
# Step 4 — Drop the intermediate time_step column
# ─────────────────────────────────────────────
df_classes.drop(columns=["time_step"], inplace=True)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 2 — Timestamps Added")
print("=" * 50)
print(f"  Columns now : {df_classes.columns.tolist()}")
print(f"  Null timestamps: {df_classes['timestamp'].isnull().sum()}")
print(f"\n  First 5 rows (txid | is_illicit | timestamp):")
print(df_classes[["txid", "is_illicit", "timestamp"]].head())
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 3 — Add Wallet Addresses
# ═══════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Step 1 — Helper: generate a synthetic Bitcoin wallet address
#   Format: "1" + 25-33 random chars from Base58 alphabet
# ─────────────────────────────────────────────
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def gen_wallet() -> str:
    """Return a synthetic Base58-style Bitcoin address (26–34 chars, starts with '1')."""
    length = random.randint(25, 33)   # 25 random chars + leading "1" = 26–34 total
    return "1" + "".join(random.choices(BASE58_ALPHABET, k=length))

# ─────────────────────────────────────────────
# Step 2 — Load BitcoinHeistData: address + label only
#   Keep only heist (non-white) addresses, then deduplicate
# ─────────────────────────────────────────────
heist_path = os.path.join(RAW_DIR, "BitcoinHeistData.csv")
df_heist   = pd.read_csv(heist_path, usecols=["address", "label"])

# Keep only actual heist addresses (exclude the "white"/legitimate ones)
df_heist   = df_heist[df_heist["label"] != "white"].copy()

# Drop duplicate addresses — keep first occurrence (preserves its label)
df_heist.drop_duplicates(subset="address", keep="first", inplace=True)
df_heist.reset_index(drop=True, inplace=True)

# ─────────────────────────────────────────────
# Step 3 — Assign input_wallet and heist_label
#   Illicit rows → sample real heist addresses
#   Licit rows   → generate synthetic wallets
# ─────────────────────────────────────────────
n_illicit = int((df_classes["is_illicit"] == 1).sum())
n_licit   = int((df_classes["is_illicit"] == 0).sum())

# Sample real heist addresses for illicit rows (with replacement if needed)
sampled_heist = df_heist.sample(
    n=n_illicit,
    replace=(len(df_heist) < n_illicit),
    random_state=42
).reset_index(drop=True)

# Initialise new columns
df_classes["input_wallet"] = None
df_classes["heist_label"]  = None

# --- Illicit rows: real wallet + heist label ---
illicit_idx = df_classes[df_classes["is_illicit"] == 1].index
df_classes.loc[illicit_idx, "input_wallet"] = sampled_heist["address"].values
df_classes.loc[illicit_idx, "heist_label"]  = sampled_heist["label"].values

# --- Licit rows: synthetic wallet, no heist label ---
licit_idx = df_classes[df_classes["is_illicit"] == 0].index
df_classes.loc[licit_idx, "input_wallet"] = [gen_wallet() for _ in range(n_licit)]
# heist_label remains None for licit rows

# ─────────────────────────────────────────────
# Step 4 — Generate a synthetic output_wallet for ALL rows
# ─────────────────────────────────────────────
df_classes["output_wallet"] = [gen_wallet() for _ in range(len(df_classes))]

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
real_wallets      = df_classes["input_wallet"][illicit_idx]
synthetic_wallets = df_classes["input_wallet"][licit_idx]

print("=" * 50)
print("SUB-TASK 3 — Wallet Addresses Assigned")
print("=" * 50)
print(f"  Rows with REAL input wallets (illicit)     : {n_illicit:,}")
print(f"  Rows with SYNTHETIC input wallets (licit)  : {n_licit:,}")
print(f"\n  Sample REAL wallet    : {real_wallets.iloc[0]}")
print(f"  Sample SYNTHETIC wallet: {synthetic_wallets.iloc[0]}")
print(f"\n  Unique heist labels used: {df_classes['heist_label'].dropna().unique()}")
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 4 — Assign pattern_type Column
# ═══════════════════════════════════════════════════════

# Initialize pattern_type column
df_classes["pattern_type"] = "normal"

# 1. Illicit rows with a heist label -> "ransomware"
ransomware_mask = (df_classes["is_illicit"] == 1) & (df_classes["heist_label"].notna())
df_classes.loc[ransomware_mask, "pattern_type"] = "ransomware"

# 2. Illicit rows without a heist label -> random assignment (layering: 50%, mixing: 30%, chain_hop: 20%)
unlabeled_illicit_mask = (df_classes["is_illicit"] == 1) & (df_classes["heist_label"].isna())
n_unlabeled = int(unlabeled_illicit_mask.sum())

if n_unlabeled > 0:
    patterns = ["layering", "mixing", "chain_hop"]
    probs = [0.5, 0.3, 0.2]
    assigned_patterns = np.random.choice(patterns, size=n_unlabeled, p=probs)
    df_classes.loc[unlabeled_illicit_mask, "pattern_type"] = assigned_patterns

# 3. Drop heist_label column
df_classes.drop(columns=["heist_label"], inplace=True)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 4 — pattern_type Assigned")
print("=" * 50)
print("pattern_type distribution:")
print(df_classes["pattern_type"].value_counts().to_string())
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 5 — Generate Synthetic Financial Columns
# ═══════════════════════════════════════════════════════

n_rows = len(df_classes)

# 1. amount_btc: lognormal distribution (mean=-2.0, sigma=1.5), clipped at 0.00000001, rounded to 8 decimal places
raw_amounts = np.random.lognormal(mean=-2.0, sigma=1.5, size=n_rows)
df_classes["amount_btc"] = np.clip(raw_amounts, 0.00000001, None).round(8)

# 2. fee_btc: uniform distribution (0.00001 to 0.0005), rounded to 8 decimal places
raw_fees = np.random.uniform(0.00001, 0.0005, size=n_rows)
df_classes["fee_btc"] = raw_fees.round(8)

# 3. script_type: random choice with exact weights
scripts = ["P2PKH", "P2SH", "P2WPKH", "P2WSH"]
script_probs = [0.45, 0.25, 0.25, 0.05]
df_classes["script_type"] = np.random.choice(scripts, size=n_rows, p=script_probs)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 5 — Financial Columns Generated")
print("=" * 50)
print(f"  amount_btc Mean: {df_classes['amount_btc'].mean():.8f} BTC")
print(f"  amount_btc Max : {df_classes['amount_btc'].max():.8f} BTC")
print(f"  amount_btc Min : {df_classes['amount_btc'].min():.8f} BTC")
print(f"  fee_btc Mean   : {df_classes['fee_btc'].mean():.8f} BTC")
print("\nscript_type distribution:")
print(df_classes["script_type"].value_counts().to_string())
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 6 — Add 25,000 Additional Illicit Heist Rows
# ═══════════════════════════════════════════════════════

# 1. Load BitcoinHeistData with required columns
heist_extra_path = os.path.join(RAW_DIR, "BitcoinHeistData.csv")
df_heist_extra = pd.read_csv(heist_extra_path, usecols=["address", "year", "day", "label"])

# Filter for actual heist (illicit) rows
df_heist_extra = df_heist_extra[df_heist_extra["label"] != "white"].copy()

# 2. Remove any address already used as input_wallet in the main DataFrame
used_input_wallets = set(df_classes["input_wallet"].dropna())
df_heist_extra = df_heist_extra[~df_heist_extra["address"].isin(used_input_wallets)].copy()

# 3. Sample exactly 25,000 rows from what remains
n_extra = 25000
sampled_extra = df_heist_extra.sample(n=n_extra, random_state=42).reset_index(drop=True)

# 4. Build new DataFrame rows
# Construct datetime from year and day of year (%Y-%j) + random hours (0-23)
base_dates = pd.to_datetime(
    sampled_extra["year"].astype(str) + "-" + sampled_extra["day"].astype(str),
    format="%Y-%j"
)
random_hours = pd.to_timedelta(np.random.randint(0, 24, size=n_extra), unit="h")
timestamps = base_dates + random_hours

# Financial distributions matching Sub-task 5
extra_amounts = np.clip(np.random.lognormal(mean=-2.0, sigma=1.5, size=n_extra), 0.00000001, None).round(8)
extra_fees = np.random.uniform(0.00001, 0.0005, size=n_extra).round(8)
extra_scripts = np.random.choice(["P2PKH", "P2SH", "P2WPKH", "P2WSH"], size=n_extra, p=[0.45, 0.25, 0.25, 0.05])

df_extra = pd.DataFrame({
    "txid": np.arange(999000001, 999000001 + n_extra, dtype=np.int64),
    "is_illicit": np.ones(n_extra, dtype=int),
    "timestamp": timestamps,
    "input_wallet": sampled_extra["address"].values,
    "output_wallet": [gen_wallet() for _ in range(n_extra)],
    "pattern_type": "ransomware",
    "amount_btc": extra_amounts,
    "fee_btc": extra_fees,
    "script_type": extra_scripts
})

# 5. Append new rows to main DataFrame
df_classes = pd.concat([df_classes, df_extra], ignore_index=True)

# 6. Shuffle the entire combined DataFrame and reset index
df_classes = df_classes.sample(frac=1.0, random_state=42).reset_index(drop=True)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("=" * 50)
print("SUB-TASK 6 — 25,000 Heist Rows Added & Dataset Balanced")
print("=" * 50)
print(f"  Final total row count: {len(df_classes):,}")
print("\nis_illicit distribution:")
print(df_classes["is_illicit"].value_counts().to_string())
print("\npattern_type distribution:")
print(df_classes["pattern_type"].value_counts().to_string())
print("=" * 50)

# ═══════════════════════════════════════════════════════
# SUB-TASK 7 — Save Final blockchain_transactions.csv
# ═══════════════════════════════════════════════════════

# 1. Ensure output directory exists
os.makedirs(PROC_DIR, exist_ok=True)

# 2. Reorder columns into exact required order
final_columns = [
    "txid",
    "timestamp",
    "input_wallet",
    "output_wallet",
    "amount_btc",
    "fee_btc",
    "script_type",
    "is_illicit",
    "pattern_type"
]
df_final = df_classes[final_columns].copy()

# 3. Save to data/processed/blockchain_transactions.csv
output_file_path = os.path.join(PROC_DIR, "blockchain_transactions.csv")
df_final.to_csv(output_file_path, index=False)

# 4. Print completion summary
print("=" * 50)
print("SUB-TASK 7 — Pipeline Complete & File Saved")
print("=" * 50)
print(f"  File saved to       : {output_file_path}")
print(f"  Total rows saved    : {len(df_final):,}")
print(f"  Total columns saved : {len(df_final.columns)}")
print(f"  Columns list        : {df_final.columns.tolist()}")

print("\nis_illicit distribution (%):")
print((df_final["is_illicit"].value_counts(normalize=True) * 100).round(2).to_string())

print("\npattern_type distribution (%):")
print((df_final["pattern_type"].value_counts(normalize=True) * 100).round(2).to_string())
print("=" * 50)
print("🎉 All sub-tasks finished successfully!")
print("=" * 50)
