"""
generate_v2.py
==============
SIH 2026 — Bitcoin AML Dataset v2.0 Generation Pipeline

Single-file pipeline that produces all v2.0 outputs, fixing all 7 identified
issues from v1.0:

  1. Multi-input / multi-output UTXO transactions (array columns)
  2. scenario_id grouping for leak-safe splitting
  3. Real typology sub-labels (peeling_chain, layering, mixing, ransomware)
  4. Hard negatives (exchange-like licit wallets)
  5. Decorrelated network metadata (overlapping pools)
  6. Txid range leak removed (shuffled IDs)
  7. Timestamp source leak reduced (licit rows extended to 2011–2016)

Plus: deterministic 80/20 scenario-level stratified train/test split.

Usage:
    python data_pipeline/generate_v2.py

Outputs (all in data/processed/):
    - blockchain_transactions.csv  (master, with split column)
    - network_metadata.csv         (master, with split column)
    - train_blockchain.csv / train_network.csv
    - test_blockchain.csv  / test_network.csv
"""

import hashlib
import json
import os
import random
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
SEED = 42
SPLIT_RATIO = 0.2  # 20% test

# Typology scenario counts
N_PEELING_CHAINS = 40
PEELING_HOPS_RANGE = (5, 10)

N_LAYERING_CLUSTERS = 25
LAYERING_FANOUT_RANGE = (5, 10)  # outputs in fan-out step

N_MIXING_CLUSTERS = 20
MIXING_ROUNDS_RANGE = (3, 6)
MIXING_PARTICIPANTS_RANGE = (3, 5)

# Hard negatives
N_EXCHANGE_WALLETS = 30
EXCHANGE_TXN_RANGE = (50, 500)

# Network metadata decorrelation
LICIT_SUSPICIOUS_FRACTION = 0.15   # 15% of licit txns get suspicious metadata
ILLICIT_NORMAL_FRACTION = 0.20     # 20% of illicit txns get normal metadata

# Timestamp extension
LICIT_BACKDATE_FRACTION = 0.20     # 20% of licit rows backdated to 2011–2016

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# RANDOM STATE
# ═══════════════════════════════════════════════════════════════════════════════
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(seed=SEED)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

_wallet_counter = 0

def gen_wallet() -> str:
    """Return a synthetic Base58-style Bitcoin address (26–34 chars, starts with '1')."""
    length = random.randint(25, 33)
    return "1" + "".join(random.choices(BASE58_ALPHABET, k=length))


def gen_unique_wallet(existing: set) -> str:
    """Generate a wallet address guaranteed not in `existing`. Adds it to the set."""
    while True:
        w = gen_wallet()
        if w not in existing:
            existing.add(w)
            return w


def make_txid(counter: int, salt: str = "sih2026v2") -> int:
    """Hash-based txid generation to avoid contiguous block leaks."""
    h = hashlib.sha256(f"{salt}:{counter}".encode()).hexdigest()
    # Take first 8 hex chars → 32-bit int, add offset to stay in realistic range
    raw = int(h[:8], 16)
    return 100_000_000 + (raw % 900_000_000)  # range [100M, 1B)


def sample_amount(low=0.001, high=10.0) -> float:
    """Log-normal amount, clipped."""
    val = np.random.lognormal(mean=-2.0, sigma=1.5)
    return round(max(val, 1e-8), 8)


def sample_fee() -> float:
    """Uniform fee."""
    return round(np.random.uniform(0.00001, 0.0005), 8)


def sample_script_type() -> str:
    return np.random.choice(
        ["P2PKH", "P2SH", "P2WPKH", "P2WSH"],
        p=[0.45, 0.25, 0.25, 0.05]
    )


def random_timestamp_in_range(start_year=2011, end_year=2018) -> pd.Timestamp:
    """Return a random timestamp between start_year-01-01 and end_year-12-31."""
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp(f"{end_year}-12-31 23:59:59")
    delta = (end - start).total_seconds()
    offset = random.random() * delta
    return start + pd.Timedelta(seconds=offset)


def distribute_amount(total: float, n: int) -> list:
    """Split `total` into `n` random positive parts that sum to total."""
    if n == 1:
        return [round(total, 8)]
    # Use Dirichlet distribution for random partition
    fracs = rng.dirichlet(np.ones(n))
    parts = [round(total * f, 8) for f in fracs]
    # Fix rounding residual on last element
    residual = round(total - sum(parts[:-1]), 8)
    parts[-1] = max(residual, 1e-8)
    return parts


# ═══════════════════════════════════════════════════════════════════════════════
# NETWORK METADATA POOLS
# ═══════════════════════════════════════════════════════════════════════════════
NORMAL_NODE_TYPES = ["residential", "datacenter", "mobile"]
NORMAL_NODE_WEIGHTS = [0.70, 0.25, 0.05]

SUSPICIOUS_NODE_TYPES = ["tor_exit_node", "vpn_proxy", "bulletproof_host", "residential"]
SUSPICIOUS_NODE_WEIGHTS = [0.45, 0.35, 0.15, 0.05]

NORMAL_ASNS = [
    {"asn": "AS15169", "isp": "Google LLC", "country": "US"},
    {"asn": "AS7922",  "isp": "Comcast Cable Communications", "country": "US"},
    {"asn": "AS3215",  "isp": "Orange S.A.", "country": "FR"},
    {"asn": "AS55836", "isp": "Reliance Jio Infocomm", "country": "IN"},
    {"asn": "AS16509", "isp": "Amazon.com, Inc.", "country": "US"},
    {"asn": "AS13335", "isp": "Cloudflare, Inc.", "country": "US"},
    {"asn": "AS6830",  "isp": "Liberty Global Operations", "country": "NL"},
    {"asn": "AS4713",  "isp": "NTT Communications", "country": "JP"},
]

SUSPICIOUS_ASNS = [
    {"asn": "AS9009",   "isp": "M247 Ltd", "country": "RO"},
    {"asn": "AS60068",  "isp": "Datacamp Limited", "country": "GB"},
    {"asn": "AS200052", "isp": "Tor-Relay-Network", "country": "DE"},
    {"asn": "AS44050",  "isp": "Petersburg Internet Network", "country": "RU"},
    {"asn": "AS204957", "isp": "Green Floid LLC (Bulletproof)", "country": "SC"},
    {"asn": "AS49870",  "isp": "Alentus Corporation (Darknet Proxy)", "country": "BZ"},
    {"asn": "AS210644", "isp": "AEZA International LTD", "country": "RU"},
]

USER_AGENTS = [
    "/Satoshi:22.0.0/",
    "/Satoshi:21.1.0/",
    "/Satoshi:0.20.1/",
    "/btcd:0.22.0/",
]
USER_AGENT_WEIGHTS = [0.55, 0.25, 0.15, 0.05]


def gen_ipv4() -> str:
    """Generate a plausible public IPv4 address."""
    o1 = random.choice([random.randint(11, 99), random.randint(101, 126), random.randint(128, 223)])
    return f"{o1}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: LOAD SOURCE DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 1 — Loading source data")
print("=" * 70)

# --- Elliptic classes ---
classes_path = os.path.join(RAW_DIR, "elliptic_txs_classes.csv")
df_classes = pd.read_csv(classes_path)
df_classes = df_classes[df_classes["class"] != "unknown"].copy()
df_classes["class"] = df_classes["class"].astype(int).replace({2: 0})
df_classes.rename(columns={"txId": "txid", "class": "is_illicit"}, inplace=True)
df_classes.reset_index(drop=True, inplace=True)

# --- Elliptic features (txid + time_step only) ---
features_path = os.path.join(RAW_DIR, "elliptic_txs_features.csv")
df_time = pd.read_csv(features_path, header=None, usecols=[0, 1], names=["txid", "time_step"])
df_classes = df_classes.merge(df_time, on="txid", how="left")

# --- Bitcoin Heist addresses ---
heist_path = os.path.join(RAW_DIR, "BitcoinHeistData.csv")
df_heist = pd.read_csv(heist_path, usecols=["address", "label", "year", "day"])
df_heist = df_heist[df_heist["label"] != "white"].copy()
df_heist.drop_duplicates(subset="address", keep="first", inplace=True)
df_heist.reset_index(drop=True, inplace=True)

print(f"  Elliptic labelled rows : {len(df_classes):,}")
print(f"  Elliptic licit         : {(df_classes['is_illicit'] == 0).sum():,}")
print(f"  Elliptic illicit       : {(df_classes['is_illicit'] == 1).sum():,}")
print(f"  Heist unique addresses : {len(df_heist):,}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: BUILD BASE ELLIPTIC TRANSACTIONS WITH MULTI-I/O
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 2 — Building base Elliptic transactions")
print("=" * 70)

all_wallets = set()  # track all wallets ever generated
utxo_pool = []       # (wallet_address, amount) — funded wallets available as inputs

# --- Timestamps for Elliptic rows ---
base_date = pd.Timestamp("2017-01-01")
step_offsets = pd.to_timedelta((df_classes["time_step"] - 1) * 14, unit="D")
jitter_seconds = rng.integers(0, 1_209_601, size=len(df_classes))
jitter_offsets = pd.to_timedelta(jitter_seconds, unit="s")
df_classes["timestamp"] = base_date + step_offsets + jitter_offsets
df_classes.drop(columns=["time_step"], inplace=True)

# --- Assign wallets for Elliptic rows ---
n_elliptic_illicit = int((df_classes["is_illicit"] == 1).sum())
n_elliptic_licit = int((df_classes["is_illicit"] == 0).sum())

# Sample heist addresses for illicit Elliptic rows
sampled_heist = df_heist.sample(
    n=n_elliptic_illicit,
    replace=(len(df_heist) < n_elliptic_illicit),
    random_state=SEED,
).reset_index(drop=True)

df_classes["heist_label"] = None
illicit_idx = df_classes[df_classes["is_illicit"] == 1].index
licit_idx = df_classes[df_classes["is_illicit"] == 0].index

# Build records list for the main Elliptic rows
print("  Building multi-I/O records for Elliptic rows...")
txid_counter = 0
records = []

# Sort by timestamp for realistic UTXO pool evolution
df_classes = df_classes.sort_values("timestamp").reset_index(drop=True)

for i, row in df_classes.iterrows():
    is_ill = int(row["is_illicit"])

    # Determine number of inputs and outputs
    n_in = max(1, int(rng.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.30, 0.20, 0.15, 0.15, 0.08, 0.06, 0.04, 0.02])))
    n_out = max(1, int(rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8],
                                   p=[0.15, 0.10, 0.20, 0.10, 0.15, 0.10, 0.08, 0.05, 0.04, 0.02, 0.01])))

    # --- Input addresses ---
    input_addrs = []
    if is_ill:
        # Primary input: real heist address
        heist_row_idx = (illicit_idx == i).argmax() if i in illicit_idx else 0
        # Find position of i within illicit_idx
        pos_in_illicit = np.searchsorted(illicit_idx, i)
        if pos_in_illicit < len(sampled_heist):
            primary_addr = sampled_heist.iloc[pos_in_illicit]["address"]
        else:
            primary_addr = gen_unique_wallet(all_wallets)
        input_addrs.append(primary_addr)
        all_wallets.add(primary_addr)
        # Additional inputs from UTXO pool or synthetic
        for _ in range(n_in - 1):
            if utxo_pool and random.random() < 0.3:
                w, _ = utxo_pool.pop(random.randint(0, len(utxo_pool) - 1))
                input_addrs.append(w)
            else:
                input_addrs.append(gen_unique_wallet(all_wallets))
    else:
        # Licit: synthetic wallets, some from UTXO pool
        for j in range(n_in):
            if j == 0:
                # Primary: fresh synthetic or UTXO pool
                if utxo_pool and random.random() < 0.3:
                    w, _ = utxo_pool.pop(random.randint(0, len(utxo_pool) - 1))
                    input_addrs.append(w)
                else:
                    input_addrs.append(gen_unique_wallet(all_wallets))
            else:
                if utxo_pool and random.random() < 0.25:
                    w, _ = utxo_pool.pop(random.randint(0, len(utxo_pool) - 1))
                    input_addrs.append(w)
                else:
                    input_addrs.append(gen_unique_wallet(all_wallets))

    # --- Amounts ---
    total_amount = sample_amount()
    fee = sample_fee()
    input_total = round(total_amount + fee, 8)
    input_amounts = distribute_amount(input_total, n_in)
    output_amounts = distribute_amount(total_amount, n_out)

    # --- Output addresses (with some reuse into UTXO pool) ---
    output_addrs = []
    for k in range(n_out):
        w = gen_unique_wallet(all_wallets)
        output_addrs.append(w)
        # Add to UTXO pool for future input reuse (cap pool size)
        if len(utxo_pool) < 50000:
            utxo_pool.append((w, output_amounts[k]))

    # --- Heist label for pattern assignment ---
    heist_lbl = None
    if is_ill:
        pos_in_illicit = np.searchsorted(illicit_idx, i)
        if pos_in_illicit < len(sampled_heist):
            heist_lbl = sampled_heist.iloc[pos_in_illicit]["label"]

    txid_counter += 1
    records.append({
        "txid_counter": txid_counter,
        "timestamp": row["timestamp"],
        "input_addresses": json.dumps(input_addrs),
        "output_addresses": json.dumps(output_addrs),
        "input_amounts": json.dumps(input_amounts),
        "output_amounts": json.dumps(output_amounts),
        "fee_btc": fee,
        "script_type": sample_script_type(),
        "is_illicit": is_ill,
        "pattern_type": "ransomware" if (is_ill and heist_lbl) else "normal",
        "scenario_id": None,  # assigned later
        "_source": "elliptic",
    })

    if (i + 1) % 10000 == 0:
        print(f"    Processed {i + 1:,} / {len(df_classes):,} Elliptic rows...")

df_main = pd.DataFrame(records)
print(f"  Built {len(df_main):,} base Elliptic records")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2b: ADD 25,000 HEIST-APPENDED ROWS (as in v1.0 Sub-task 6)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n  Adding 25,000 heist-appended rows...")

# Filter heist addresses not yet used
used_wallets_so_far = set()
for rec in records:
    for a in json.loads(rec["input_addresses"]):
        used_wallets_so_far.add(a)

df_heist_extra = df_heist[~df_heist["address"].isin(used_wallets_so_far)].copy()
n_extra = 25000
sampled_extra = df_heist_extra.sample(
    n=n_extra,
    replace=(len(df_heist_extra) < n_extra),
    random_state=SEED,
).reset_index(drop=True)

# Timestamps from heist year+day
base_dates = pd.to_datetime(
    sampled_extra["year"].astype(str) + "-" + sampled_extra["day"].astype(str),
    format="%Y-%j",
)
random_hours = pd.to_timedelta(rng.integers(0, 24, size=n_extra), unit="h")
heist_timestamps = base_dates + random_hours

heist_records = []
for idx in range(n_extra):
    txid_counter += 1
    addr = sampled_extra.iloc[idx]["address"]
    all_wallets.add(addr)

    n_in = max(1, int(rng.choice([1, 1, 2], p=[0.6, 0.25, 0.15])))
    n_out = max(1, int(rng.choice([1, 2, 2, 3], p=[0.3, 0.3, 0.2, 0.2])))

    total_amount = sample_amount()
    fee = sample_fee()
    input_total = round(total_amount + fee, 8)
    input_amounts = distribute_amount(input_total, n_in)
    output_amounts = distribute_amount(total_amount, n_out)

    input_addrs = [addr]
    for _ in range(n_in - 1):
        input_addrs.append(gen_unique_wallet(all_wallets))

    output_addrs = []
    for k in range(n_out):
        w = gen_unique_wallet(all_wallets)
        output_addrs.append(w)
        if len(utxo_pool) < 50000:
            utxo_pool.append((w, output_amounts[k]))

    heist_records.append({
        "txid_counter": txid_counter,
        "timestamp": heist_timestamps.iloc[idx],
        "input_addresses": json.dumps(input_addrs),
        "output_addresses": json.dumps(output_addrs),
        "input_amounts": json.dumps(input_amounts),
        "output_amounts": json.dumps(output_amounts),
        "fee_btc": fee,
        "script_type": sample_script_type(),
        "is_illicit": 1,
        "pattern_type": "ransomware",
        "scenario_id": None,
        "_source": "heist_appended",
    })

df_heist_appended = pd.DataFrame(heist_records)
df_main = pd.concat([df_main, df_heist_appended], ignore_index=True)
print(f"  Total after heist append: {len(df_main):,}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: PLANT ILLICIT TYPOLOGY SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 3 — Planting illicit typology scenarios")
print("=" * 70)

scenario_records = []

# --- 3a. Peeling Chains ---
print(f"  Planting {N_PEELING_CHAINS} peeling chains...")
for sc_idx in range(N_PEELING_CHAINS):
    scenario_id = f"peel_{sc_idx + 1:03d}"
    n_hops = random.randint(*PEELING_HOPS_RANGE)
    base_ts = random_timestamp_in_range(2013, 2018)

    # Initial wallet
    current_wallet = gen_unique_wallet(all_wallets)
    initial_amount = round(rng.lognormal(-1.0, 1.0), 8)
    initial_amount = max(initial_amount, 0.01)

    remaining = initial_amount

    for hop in range(n_hops):
        txid_counter += 1
        fee = sample_fee()

        # Peel off a small amount, pass the rest to the next hop
        peel_fraction = round(rng.uniform(0.05, 0.25), 4)
        peel_amount = round(remaining * peel_fraction, 8)
        pass_amount = round(remaining - peel_amount - fee, 8)

        if pass_amount < 1e-8:
            break

        # Recipient (peeled off)
        peel_wallet = gen_unique_wallet(all_wallets)
        # Change / pass-through wallet (becomes next hop's input)
        next_wallet = gen_unique_wallet(all_wallets)

        hop_ts = base_ts + pd.Timedelta(minutes=random.randint(10, 120) * (hop + 1))

        scenario_records.append({
            "txid_counter": txid_counter,
            "timestamp": hop_ts,
            "input_addresses": json.dumps([current_wallet]),
            "output_addresses": json.dumps([peel_wallet, next_wallet]),
            "input_amounts": json.dumps([round(remaining, 8)]),
            "output_amounts": json.dumps([peel_amount, pass_amount]),
            "fee_btc": fee,
            "script_type": sample_script_type(),
            "is_illicit": 1,
            "pattern_type": "peeling_chain",
            "scenario_id": scenario_id,
            "_source": "typology_planted",
        })

        current_wallet = next_wallet
        remaining = pass_amount

# --- 3b. Fan-out / Fan-in Layering ---
print(f"  Planting {N_LAYERING_CLUSTERS} layering clusters...")
for sc_idx in range(N_LAYERING_CLUSTERS):
    scenario_id = f"layer_{sc_idx + 1:03d}"
    n_fanout = random.randint(*LAYERING_FANOUT_RANGE)
    base_ts = random_timestamp_in_range(2013, 2018)

    source_wallet = gen_unique_wallet(all_wallets)
    collector_wallet = gen_unique_wallet(all_wallets)
    total_amount = round(rng.lognormal(0.0, 1.5), 8)
    total_amount = max(total_amount, 0.1)

    # Fan-out: source → N intermediaries
    txid_counter += 1
    fee = sample_fee()
    intermediate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
    out_amounts = distribute_amount(round(total_amount - fee, 8), n_fanout)

    scenario_records.append({
        "txid_counter": txid_counter,
        "timestamp": base_ts,
        "input_addresses": json.dumps([source_wallet]),
        "output_addresses": json.dumps(intermediate_wallets),
        "input_amounts": json.dumps([total_amount]),
        "output_amounts": json.dumps(out_amounts),
        "fee_btc": fee,
        "script_type": sample_script_type(),
        "is_illicit": 1,
        "pattern_type": "layering",
        "scenario_id": scenario_id,
        "_source": "typology_planted",
    })

    # Optional middle hops: some intermediaries do a pass-through
    active_wallets = list(zip(intermediate_wallets, out_amounts))
    next_active = []
    for iw, ia in active_wallets:
        if random.random() < 0.4:  # 40% chance of extra hop
            txid_counter += 1
            fee2 = sample_fee()
            hop_wallet = gen_unique_wallet(all_wallets)
            hop_amount = round(ia - fee2, 8)
            if hop_amount < 1e-8:
                next_active.append((iw, ia))
                continue
            hop_ts = base_ts + pd.Timedelta(minutes=random.randint(30, 240))
            scenario_records.append({
                "txid_counter": txid_counter,
                "timestamp": hop_ts,
                "input_addresses": json.dumps([iw]),
                "output_addresses": json.dumps([hop_wallet]),
                "input_amounts": json.dumps([ia]),
                "output_amounts": json.dumps([hop_amount]),
                "fee_btc": fee2,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "layering",
                "scenario_id": scenario_id,
                "_source": "typology_planted",
            })
            next_active.append((hop_wallet, hop_amount))
        else:
            next_active.append((iw, ia))

    # Fan-in: all active intermediaries → collector
    txid_counter += 1
    fee3 = sample_fee()
    fan_in_wallets = [w for w, _ in next_active]
    fan_in_amounts = [a for _, a in next_active]
    total_collected = round(sum(fan_in_amounts) - fee3, 8)
    if total_collected < 1e-8:
        total_collected = 1e-8

    fanin_ts = base_ts + pd.Timedelta(hours=random.randint(4, 48))
    scenario_records.append({
        "txid_counter": txid_counter,
        "timestamp": fanin_ts,
        "input_addresses": json.dumps(fan_in_wallets),
        "output_addresses": json.dumps([collector_wallet]),
        "input_amounts": json.dumps(fan_in_amounts),
        "output_amounts": json.dumps([total_collected]),
        "fee_btc": fee3,
        "script_type": sample_script_type(),
        "is_illicit": 1,
        "pattern_type": "layering",
        "scenario_id": scenario_id,
        "_source": "typology_planted",
    })

# --- 3c. Mixing Clusters (CoinJoin-like) ---
print(f"  Planting {N_MIXING_CLUSTERS} mixing clusters...")
for sc_idx in range(N_MIXING_CLUSTERS):
    scenario_id = f"mix_{sc_idx + 1:03d}"
    n_rounds = random.randint(*MIXING_ROUNDS_RANGE)
    n_participants = random.randint(*MIXING_PARTICIPANTS_RANGE)
    base_ts = random_timestamp_in_range(2014, 2018)

    # Initial participant wallets
    participant_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
    per_participant_amount = round(rng.lognormal(-1.0, 1.0), 8)
    per_participant_amount = max(per_participant_amount, 0.01)

    for rnd in range(n_rounds):
        txid_counter += 1
        fee = sample_fee()

        # All participants contribute equal amounts
        input_addrs = participant_wallets.copy()
        input_amts = [per_participant_amount] * n_participants

        # Output: same number of outputs, equal amounts, new wallets (shuffled)
        total_in = round(sum(input_amts), 8)
        total_out = round(total_in - fee, 8)
        out_per = round(total_out / n_participants, 8)

        new_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
        output_amts = [out_per] * n_participants
        # Fix rounding
        output_amts[-1] = round(total_out - sum(output_amts[:-1]), 8)

        round_ts = base_ts + pd.Timedelta(minutes=random.randint(5, 60) * (rnd + 1))

        scenario_records.append({
            "txid_counter": txid_counter,
            "timestamp": round_ts,
            "input_addresses": json.dumps(input_addrs),
            "output_addresses": json.dumps(new_wallets),
            "input_amounts": json.dumps(input_amts),
            "output_amounts": json.dumps(output_amts),
            "fee_btc": fee,
            "script_type": sample_script_type(),
            "is_illicit": 1,
            "pattern_type": "mixing",
            "scenario_id": scenario_id,
            "_source": "typology_planted",
        })

        # Next round's inputs are this round's outputs
        participant_wallets = new_wallets
        per_participant_amount = out_per

df_scenarios = pd.DataFrame(scenario_records)
print(f"  Planted {len(df_scenarios):,} typology scenario transactions")
print(f"    Peeling chain txns : {(df_scenarios['pattern_type'] == 'peeling_chain').sum():,}")
print(f"    Layering txns      : {(df_scenarios['pattern_type'] == 'layering').sum():,}")
print(f"    Mixing txns        : {(df_scenarios['pattern_type'] == 'mixing').sum():,}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: PLANT HARD NEGATIVES (Exchange-like licit wallets)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 4 — Planting hard negatives (exchange-like licit wallets)")
print("=" * 70)

exchange_records = []
for ex_idx in range(N_EXCHANGE_WALLETS):
    scenario_id = f"exchange_{ex_idx + 1:03d}"
    exchange_wallet = gen_unique_wallet(all_wallets)
    n_txns = random.randint(*EXCHANGE_TXN_RANGE)
    base_ts = random_timestamp_in_range(2014, 2018)

    for t in range(n_txns):
        txid_counter += 1
        ts = base_ts + pd.Timedelta(minutes=random.randint(1, 60) * (t + 1))

        fee = sample_fee()

        if random.random() < 0.6:
            # Fan-out: exchange sends to multiple users
            n_out = random.randint(2, 8)
            total_amount = sample_amount() * 5  # exchanges move more
            total_amount = max(total_amount, 0.01)
            out_amounts = distribute_amount(round(total_amount, 8), n_out)
            in_amount = round(total_amount + fee, 8)

            output_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]

            exchange_records.append({
                "txid_counter": txid_counter,
                "timestamp": ts,
                "input_addresses": json.dumps([exchange_wallet]),
                "output_addresses": json.dumps(output_addrs),
                "input_amounts": json.dumps([in_amount]),
                "output_amounts": json.dumps(out_amounts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 0,
                "pattern_type": "normal",
                "scenario_id": scenario_id,
                "_source": "hard_negative",
            })
        else:
            # Fan-in: multiple users deposit to exchange
            n_in = random.randint(2, 5)
            total_amount = sample_amount() * 3
            total_amount = max(total_amount, 0.01)
            in_amounts = distribute_amount(round(total_amount + fee, 8), n_in)
            out_amount = round(total_amount, 8)

            input_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]

            exchange_records.append({
                "txid_counter": txid_counter,
                "timestamp": ts,
                "input_addresses": json.dumps(input_addrs),
                "output_addresses": json.dumps([exchange_wallet]),
                "input_amounts": json.dumps(in_amounts),
                "output_amounts": json.dumps([out_amount]),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 0,
                "pattern_type": "normal",
                "scenario_id": scenario_id,
                "_source": "hard_negative",
            })

df_exchanges = pd.DataFrame(exchange_records)
print(f"  Planted {len(df_exchanges):,} exchange txns across {N_EXCHANGE_WALLETS} wallets")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: ASSIGN SCENARIO_IDS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 5 — Assigning scenario_ids")
print("=" * 70)

# Ransomware scenarios: group by primary input wallet
ransomware_mask = (df_main["pattern_type"] == "ransomware")
ransomware_rows = df_main[ransomware_mask].copy()

# Extract primary input wallet for ransomware grouping
ransomware_rows["_primary_input"] = ransomware_rows["input_addresses"].apply(
    lambda x: json.loads(x)[0]
)
wallet_to_scenario = {}
scenario_counter = 0
for wallet in ransomware_rows["_primary_input"].unique():
    scenario_counter += 1
    wallet_to_scenario[wallet] = f"ransom_{scenario_counter:04d}"

ransomware_rows["scenario_id"] = ransomware_rows["_primary_input"].map(wallet_to_scenario)
ransomware_rows.drop(columns=["_primary_input"], inplace=True)
df_main.loc[ransomware_mask, "scenario_id"] = ransomware_rows["scenario_id"].values

# Normal (licit) Elliptic rows: group into background scenarios of 10-50 txns
normal_mask = (df_main["pattern_type"] == "normal") & (df_main["scenario_id"].isna())
normal_indices = df_main[normal_mask].index.tolist()
random.shuffle(normal_indices)

bg_counter = 0
i = 0
while i < len(normal_indices):
    bg_counter += 1
    chunk_size = random.randint(10, 50)
    chunk = normal_indices[i:i + chunk_size]
    df_main.loc[chunk, "scenario_id"] = f"bg_{bg_counter:04d}"
    i += chunk_size

print(f"  Ransomware scenarios : {scenario_counter:,}")
print(f"  Background scenarios : {bg_counter:,}")

# Merge all DataFrames
df_all = pd.concat([df_main, df_scenarios, df_exchanges], ignore_index=True)
print(f"  Total records before dedup: {len(df_all):,}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: FIX METADATA LEAKS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 6 — Fixing metadata leaks")
print("=" * 70)

# --- 6a. Txid assignment (hash-based, no contiguous blocks) ---
print("  Assigning shuffled txids...")
# Shuffle order first, then assign hash-based IDs
shuffle_order = rng.permutation(len(df_all))
txid_map = {}
for new_pos, old_pos in enumerate(shuffle_order):
    counter_val = df_all.iloc[old_pos]["txid_counter"]
    txid_map[counter_val] = make_txid(new_pos)

df_all["txid"] = df_all["txid_counter"].map(txid_map)

# Check for collisions and resolve
while df_all["txid"].duplicated().any():
    dup_mask = df_all["txid"].duplicated(keep="first")
    n_dups = dup_mask.sum()
    print(f"    Resolving {n_dups} txid collisions...")
    for idx in df_all[dup_mask].index:
        txid_counter += 1
        df_all.at[idx, "txid"] = make_txid(txid_counter + random.randint(0, 1000000))

print(f"  Unique txids: {df_all['txid'].nunique():,} / {len(df_all):,}")

# --- 6b. Timestamp extension for licit rows ---
print("  Extending licit timestamps to 2011–2016...")
licit_mask = (df_all["is_illicit"] == 0)
n_licit = int(licit_mask.sum())
n_backdate = int(n_licit * LICIT_BACKDATE_FRACTION)

# Pick random licit rows to backdate
licit_indices = df_all[licit_mask].index.tolist()
backdate_indices = rng.choice(licit_indices, size=n_backdate, replace=False)

for idx in backdate_indices:
    df_all.at[idx, "timestamp"] = random_timestamp_in_range(2011, 2016)

print(f"  Backdated {n_backdate:,} licit rows to 2011–2016")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: GENERATE NETWORK METADATA (decorrelated)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 7 — Generating decorrelated network metadata")
print("=" * 70)

n_total = len(df_all)

# --- relay_timestamp ---
random_ms = rng.integers(50, 501, size=n_total)
df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])
df_all["relay_timestamp"] = df_all["timestamp"] - pd.to_timedelta(random_ms, unit="ms")

# --- Decorrelated node_type and ASN assignment ---
licit_mask = (df_all["is_illicit"] == 0).values
illicit_mask = (df_all["is_illicit"] == 1).values
n_licit = int(licit_mask.sum())
n_illicit = int(illicit_mask.sum())

# For licit: 85% normal pool, 15% suspicious pool
licit_use_suspicious = rng.random(n_licit) < LICIT_SUSPICIOUS_FRACTION
# For illicit: 80% suspicious pool, 20% normal pool
illicit_use_normal = rng.random(n_illicit) < ILLICIT_NORMAL_FRACTION

# Assign node_type
node_types = np.empty(n_total, dtype=object)

# Licit - normal pool
n_licit_normal = int((~licit_use_suspicious).sum())
n_licit_suspicious = int(licit_use_suspicious.sum())
node_types[licit_mask] = np.where(
    licit_use_suspicious,
    rng.choice(SUSPICIOUS_NODE_TYPES, size=n_licit, p=SUSPICIOUS_NODE_WEIGHTS),
    rng.choice(NORMAL_NODE_TYPES, size=n_licit, p=NORMAL_NODE_WEIGHTS),
)

# Illicit
n_illicit_normal = int(illicit_use_normal.sum())
n_illicit_suspicious = int((~illicit_use_normal).sum())
node_types[illicit_mask] = np.where(
    illicit_use_normal,
    rng.choice(NORMAL_NODE_TYPES, size=n_illicit, p=NORMAL_NODE_WEIGHTS),
    rng.choice(SUSPICIOUS_NODE_TYPES, size=n_illicit, p=SUSPICIOUS_NODE_WEIGHTS),
)

df_all["node_type"] = node_types

# Assign ASN/ISP/country (correlated with node_type pool choice)
asn_col = np.empty(n_total, dtype=object)
isp_col = np.empty(n_total, dtype=object)
country_col = np.empty(n_total, dtype=object)

# Licit rows
licit_asn_choices_normal = rng.choice(len(NORMAL_ASNS), size=n_licit)
licit_asn_choices_suspicious = rng.choice(len(SUSPICIOUS_ASNS), size=n_licit)

licit_positions = np.where(licit_mask)[0]
for i_pos, (pos, use_susp) in enumerate(zip(licit_positions, licit_use_suspicious)):
    if use_susp:
        entry = SUSPICIOUS_ASNS[licit_asn_choices_suspicious[i_pos]]
    else:
        entry = NORMAL_ASNS[licit_asn_choices_normal[i_pos]]
    asn_col[pos] = entry["asn"]
    isp_col[pos] = entry["isp"]
    country_col[pos] = entry["country"]

# Illicit rows
illicit_asn_choices_normal = rng.choice(len(NORMAL_ASNS), size=n_illicit)
illicit_asn_choices_suspicious = rng.choice(len(SUSPICIOUS_ASNS), size=n_illicit)

illicit_positions = np.where(illicit_mask)[0]
for i_pos, (pos, use_norm) in enumerate(zip(illicit_positions, illicit_use_normal)):
    if use_norm:
        entry = NORMAL_ASNS[illicit_asn_choices_normal[i_pos]]
    else:
        entry = SUSPICIOUS_ASNS[illicit_asn_choices_suspicious[i_pos]]
    asn_col[pos] = entry["asn"]
    isp_col[pos] = entry["isp"]
    country_col[pos] = entry["country"]

df_all["asn"] = asn_col
df_all["isp"] = isp_col
df_all["country_code"] = country_col

# --- relay_ip ---
df_all["relay_ip"] = [gen_ipv4() for _ in range(n_total)]

# --- relay_port ---
is_standard_port = rng.random(n_total) < 0.85
alt_ports = rng.choice([18333] + list(range(49152, 65536, 64)), size=n_total)
df_all["relay_port"] = np.where(is_standard_port, 8333, alt_ports)

# --- protocol_version and user_agent ---
df_all["protocol_version"] = 70015
df_all["user_agent"] = rng.choice(USER_AGENTS, size=n_total, p=USER_AGENT_WEIGHTS)

print(f"  Network metadata generated for {n_total:,} rows")
print(f"  Licit rows with suspicious metadata: {n_licit_suspicious:,} / {n_licit:,} ({100*n_licit_suspicious/max(n_licit,1):.1f}%)")
print(f"  Illicit rows with normal metadata: {n_illicit_normal:,} / {n_illicit:,} ({100*n_illicit_normal/max(n_illicit,1):.1f}%)")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: TRAIN/TEST SPLIT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 8 — Scenario-level stratified train/test split")
print("=" * 70)

# Build per-scenario summary for stratified splitting
scenario_summary = df_all.groupby("scenario_id").agg(
    is_illicit=("is_illicit", "first"),
    pattern_type=("pattern_type", "first"),
    n_txns=("txid", "count"),
).reset_index()

# Stratification key
scenario_summary["strat_key"] = scenario_summary["is_illicit"].astype(str) + "_" + scenario_summary["pattern_type"]

# Group-level split
from sklearn.model_selection import StratifiedShuffleSplit

splitter = StratifiedShuffleSplit(n_splits=1, test_size=SPLIT_RATIO, random_state=SEED)
train_sc_idx, test_sc_idx = next(splitter.split(scenario_summary, scenario_summary["strat_key"]))

train_scenarios = set(scenario_summary.iloc[train_sc_idx]["scenario_id"])
test_scenarios = set(scenario_summary.iloc[test_sc_idx]["scenario_id"])

df_all["split"] = df_all["scenario_id"].apply(lambda s: "train" if s in train_scenarios else "test")

n_train = (df_all["split"] == "train").sum()
n_test = (df_all["split"] == "test").sum()
train_illicit_pct = (df_all[df_all["split"] == "train"]["is_illicit"].mean()) * 100
test_illicit_pct = (df_all[df_all["split"] == "test"]["is_illicit"].mean()) * 100

print(f"  Train: {n_train:,} rows ({train_illicit_pct:.1f}% illicit)")
print(f"  Test : {n_test:,} rows ({test_illicit_pct:.1f}% illicit)")
print(f"  Scenarios in train: {len(train_scenarios):,}")
print(f"  Scenarios in test : {len(test_scenarios):,}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: SAVE OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 9 — Saving output files")
print("=" * 70)

# Final shuffle for good measure
df_all = df_all.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

# Format timestamp columns
df_all["timestamp"] = df_all["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
df_all["relay_timestamp"] = df_all["relay_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]

# --- Blockchain transactions ---
blockchain_cols = [
    "txid", "timestamp", "input_addresses", "output_addresses",
    "input_amounts", "output_amounts", "fee_btc", "script_type",
    "is_illicit", "pattern_type", "scenario_id", "split",
]
df_blockchain = df_all[blockchain_cols].copy()

# --- Network metadata ---
network_cols = [
    "txid", "relay_timestamp", "relay_ip", "relay_port", "node_type",
    "country_code", "asn", "isp", "protocol_version", "user_agent",
    "scenario_id", "split",
]
df_network = df_all[network_cols].copy()

# Save master files
blockchain_path = os.path.join(PROC_DIR, "blockchain_transactions.csv")
network_path = os.path.join(PROC_DIR, "network_metadata.csv")
df_blockchain.to_csv(blockchain_path, index=False)
df_network.to_csv(network_path, index=False)
print(f"  Saved {blockchain_path} ({len(df_blockchain):,} rows)")
print(f"  Saved {network_path} ({len(df_network):,} rows)")

# Save train/test splits
for split_name in ["train", "test"]:
    mask = df_all["split"] == split_name
    df_blockchain[mask].to_csv(os.path.join(PROC_DIR, f"{split_name}_blockchain.csv"), index=False)
    df_network[mask].to_csv(os.path.join(PROC_DIR, f"{split_name}_network.csv"), index=False)
    print(f"  Saved {split_name}_blockchain.csv and {split_name}_network.csv ({mask.sum():,} rows)")

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("🎉 v2.0 PIPELINE COMPLETE")
print("=" * 70)
print(f"  Total transactions    : {len(df_all):,}")
print(f"  Unique txids          : {df_all['txid'].nunique():,}")
print(f"  Unique scenario_ids   : {df_all['scenario_id'].nunique():,}")
print(f"\nis_illicit distribution:")
print(df_all["is_illicit"].value_counts().to_string())
print(f"\npattern_type distribution:")
print(df_all["pattern_type"].value_counts().to_string())
print(f"\nsplit distribution:")
print(df_all["split"].value_counts().to_string())
print(f"\nTimestamp range: {df_all['timestamp'].min()} → {df_all['timestamp'].max()}")
print("=" * 70)
