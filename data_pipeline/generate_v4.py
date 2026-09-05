"""
generate_v3.py
==============
SIH 2026 — Bitcoin AML Dataset v3.0 Generation Pipeline

Major v3.0 Enhancements:
  1. Eliminates the artificial duration / scenario-size gap:
     - Licit scenarios range from micro-sessions (hours) to prolonged activities (weeks/months).
     - Illicit scenarios range from fast bursts (hours) to patient campaigns (weeks/months).
     - Full distribution overlap in: time_span_hours, num_txns, unique_ip_count,
       unique_input_addrs, unique_asn_count, velocity, inter-transaction timing,
       total amount, graph density.
  2. Structural diversity for rare typologies:
     - Peeling chains: variable lengths (3-30 hops), branching trees, multi-input/output peels,
       variable pacing (minutes to days).
     - Layering: 1-to-N and M-to-N fan-outs, multi-tier hops, split collectors, varying delays.
     - Mixing: variable rounds (2-8), variable participants (3-8), equal/unequal denominations,
       cascading mixing.
  3. Scaled up rare typologies:
     - peeling_chain: ~2,500+ rows across ~250+ scenarios
     - layering: ~2,500+ rows across ~200+ scenarios
     - mixing: ~2,500+ rows across ~200+ scenarios
  4. Realistic Network Telemetry Coherence:
     - Expanded global ASN/Country registry (25+ ASNs across 16 countries).
     - Entity IP/ASN persistence within scenarios (breaks unique_ip == num_txns proxy).
     - Full country and node_type overlap between licit and illicit.
  5. Accounting and Schema Preservation:
     - 100% strict accounting: sum(inputs) = sum(outputs) + fee (exact to 8 decimals).
     - Valid JSON array columns for multi-input / multi-output UTXO transactions.
     - Hash-shuffled txids to eliminate ID sequence leakage.
     - Scenario-level stratified 80/20 train/test split with 0 leaking scenarios.

Usage:
    python data_pipeline/generate_v3.py
"""

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
SEED = 42
SPLIT_RATIO = 0.2  # 20% test

# Rare typology scenario targets
N_PEELING_SCENARIOS = 260
N_LAYERING_SCENARIOS = 260
N_MIXING_SCENARIOS = 320

# Hard negative licit exchange wallets
N_EXCHANGE_WALLETS = 40

# Network decorrelation
# Probabilistic overlap: licit uses privacy/VPN/datacenter 25%, illicit uses residential/mobile/datacenter 45%
LICIT_PRIVACY_FRACTION = 0.25
ILLICIT_NORMAL_FRACTION = 0.45

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# Random State
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(seed=SEED)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def gen_wallet() -> str:
    """Synthetic Base58-style Bitcoin address (26-34 chars, starts with '1')."""
    length = random.randint(25, 33)
    return "1" + "".join(random.choices(BASE58_ALPHABET, k=length))

def gen_unique_wallet(existing: set) -> str:
    while True:
        w = gen_wallet()
        if w not in existing:
            existing.add(w)
            return w

def make_txid(counter: int, salt: str = "sih2026v3") -> int:
    h = hashlib.sha256(f"{salt}:{counter}".encode()).hexdigest()
    raw = int(h[:8], 16)
    return 100_000_000 + (raw % 900_000_000)

def sample_fee() -> float:
    return round(float(rng.uniform(0.00001, 0.00045)), 8)

def sample_amount(low=0.001, high=10.0) -> float:
    val = float(rng.lognormal(mean=-1.8, sigma=1.4))
    return round(max(val, 1e-6), 8)

def sample_script_type() -> str:
    return str(rng.choice(
        ["P2PKH", "P2SH", "P2WPKH", "P2WSH"],
        p=[0.45, 0.25, 0.25, 0.05]
    ))

def distribute_amount(total: float, n: int) -> list:
    """Split `total` into `n` random positive parts summing strictly to total."""
    if n == 1:
        return [round(total, 8)]
    fracs = rng.dirichlet(np.ones(n))
    parts = [round(total * float(f), 8) for f in fracs]
    # Adjust last element to absorb rounding error
    residual = round(total - sum(parts[:-1]), 8)
    if residual <= 0:
        parts[0] = round(parts[0] + residual - 1e-8, 8)
        residual = 1e-8
    parts[-1] = max(residual, 1e-8)
    # Double check exact match
    diff = round(total - sum(parts), 8)
    if diff != 0:
        parts[-1] = round(parts[-1] + diff, 8)
    return parts

def random_timestamp_in_range(start_year=2012, end_year=2018) -> pd.Timestamp:
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp(f"{end_year}-12-31 23:59:59")
    delta_s = (end - start).total_seconds()
    offset_s = float(rng.uniform(0, delta_s))
    return start + pd.Timedelta(seconds=offset_s)

# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDED GLOBAL NETWORK METADATA REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════
# Shared comprehensive pools covering 16 countries and 24 ASNs
GLOBAL_ASNS = [
    # Consumer ISPs (US, DE, GB, FR, IN, JP, RU, BR, CA, AU)
    {"asn": "AS7922",  "isp": "Comcast Cable Communications", "country": "US", "infra": "residential"},
    {"asn": "AS7018",  "isp": "AT&T Services, Inc.",          "country": "US", "infra": "residential"},
    {"asn": "AS3320",  "isp": "Deutsche Telekom AG",          "country": "DE", "infra": "residential"},
    {"asn": "AS2856",  "isp": "British Telecommunications",   "country": "GB", "infra": "residential"},
    {"asn": "AS3215",  "isp": "Orange S.A.",                  "country": "FR", "infra": "residential"},
    {"asn": "AS55836", "isp": "Reliance Jio Infocomm",        "country": "IN", "infra": "mobile"},
    {"asn": "AS9498",  "isp": "Bharti Airtel Ltd",            "country": "IN", "infra": "residential"},
    {"asn": "AS4713",  "isp": "NTT Communications Corp",      "country": "JP", "infra": "residential"},
    {"asn": "AS12389", "isp": "Rostelecom PJSC",              "country": "RU", "infra": "residential"},
    {"asn": "AS28573", "isp": "Claro Brasil",                 "country": "BR", "infra": "mobile"},
    {"asn": "AS812",   "isp": "Rogers Communications",        "country": "CA", "infra": "residential"},
    {"asn": "AS1221",  "isp": "Telstra Corporation",          "country": "AU", "infra": "residential"},

    # Datacenter & Cloud Providers (US, DE, FR, NL, SG, JP)
    {"asn": "AS16509", "isp": "Amazon.com, Inc.",             "country": "US", "infra": "datacenter"},
    {"asn": "AS15169", "isp": "Google LLC",                  "country": "US", "infra": "datacenter"},
    {"asn": "AS13335", "isp": "Cloudflare, Inc.",             "country": "US", "infra": "datacenter"},
    {"asn": "AS24940", "isp": "Hetzner Online GmbH",          "country": "DE", "infra": "datacenter"},
    {"asn": "AS16276", "isp": "OVH SAS",                     "country": "FR", "infra": "datacenter"},
    {"asn": "AS60781", "isp": "Leaseweb Netherlands B.V.",    "country": "NL", "infra": "datacenter"},
    {"asn": "AS45102", "isp": "Alibaba Cloud LLC",            "country": "SG", "infra": "datacenter"},

    # Privacy / VPN / Proxy / Specialized Hosts (DE, GB, RO, RU, CH, BZ, SC, NL)
    {"asn": "AS200052", "isp": "Tor-Relay-Network",           "country": "DE", "infra": "tor_exit_node"},
    {"asn": "AS60068",  "isp": "Datacamp Limited",             "country": "GB", "infra": "vpn_proxy"},
    {"asn": "AS9009",   "isp": "M247 Ltd",                    "country": "RO", "infra": "vpn_proxy"},
    {"asn": "AS44050",  "isp": "Petersburg Internet Network",  "country": "RU", "infra": "bulletproof_host"},
    {"asn": "AS210644", "isp": "AEZA International LTD",      "country": "RU", "infra": "bulletproof_host"},
    {"asn": "AS51852",  "isp": "Proton AG (VPN Services)",     "country": "CH", "infra": "vpn_proxy"},
    {"asn": "AS49870",  "isp": "Alentus Corp (Proxy Gateway)", "country": "BZ", "infra": "vpn_proxy"},
    {"asn": "AS204957", "isp": "Green Floid LLC",             "country": "SC", "infra": "bulletproof_host"},
]

USER_AGENTS = [
    "/Satoshi:22.0.0/",
    "/Satoshi:21.1.0/",
    "/Satoshi:0.20.1/",
    "/btcd:0.22.0/",
]
USER_AGENT_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

def gen_ipv4_for_asn(asn_seed: int) -> str:
    """Generate deterministic subnet prefix based on ASN seed + random host."""
    p1 = 12 + (asn_seed * 19) % 180
    p2 = 10 + (asn_seed * 37) % 230
    p3 = random.randint(1, 254)
    p4 = random.randint(1, 254)
    return f"{p1}.{p2}.{p3}.{p4}"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: LOAD SOURCE DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 1 — Loading source Elliptic and Heist data")
print("=" * 70)

classes_path = os.path.join(RAW_DIR, "elliptic_txs_classes.csv")
df_classes = pd.read_csv(classes_path)
df_classes = df_classes[df_classes["class"] != "unknown"].copy()
df_classes["class"] = df_classes["class"].astype(int).replace({2: 0})
df_classes.rename(columns={"txId": "txid", "class": "is_illicit"}, inplace=True)
df_classes.reset_index(drop=True, inplace=True)

# Time step from features
features_path = os.path.join(RAW_DIR, "elliptic_txs_features.csv")
df_time = pd.read_csv(features_path, header=None, usecols=[0, 1], names=["txid", "time_step"])
df_classes = df_classes.merge(df_time, on="txid", how="left")

# Heist
heist_path = os.path.join(RAW_DIR, "BitcoinHeistData.csv")
df_heist = pd.read_csv(heist_path, usecols=["address", "label", "year", "day"])
df_heist = df_heist[df_heist["label"] != "white"].copy()
df_heist.drop_duplicates(subset="address", keep="first", inplace=True)
df_heist.reset_index(drop=True, inplace=True)

print(f"  Elliptic total: {len(df_classes):,} (Licit: {(df_classes['is_illicit'] == 0).sum():,}, Illicit: {(df_classes['is_illicit'] == 1).sum():,})")
print(f"  Heist unique addresses: {len(df_heist):,}")

all_wallets = set()
utxo_pool = []
txid_counter = 0

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: CONSTRUCT LICIT (NORMAL) BEHAVIORAL SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 2 — Structuring Licit (Normal) scenarios with realistic durations")
print("=" * 70)

# Extract licit Elliptic rows
licit_elliptic = df_classes[df_classes["is_illicit"] == 0].copy().reset_index(drop=True)
n_licit_total = len(licit_elliptic)

# Assign each licit transaction to a realistic behavioral scenario
# Scenario archetypes for licit:
#   1. Micro-sessions / P2P payments: 1-3 txns, duration: 5 mins to 4 hours
#   2. Short-lived active sessions: 4-10 txns, duration: 2 hours to 48 hours
#   3. Medium regular activity: 11-25 txns, duration: 2 days to 14 days
#   4. Prolonged commercial activity: 26-60 txns, duration: 7 days to 45 days
#   5. High-volume business flows: 61-150 txns, duration: 14 days to 90 days

licit_scenarios_records = []
licit_idx = 0
scenario_num = 0

while licit_idx < n_licit_total:
    scenario_num += 1
    sc_id = f"licit_{scenario_num:05d}"

    # Pick scenario size archetype probabilistically
    archetype = rng.choice([1, 2, 3, 4, 5], p=[0.35, 0.35, 0.18, 0.09, 0.03])
    if archetype == 1:
        sc_size = int(rng.integers(1, 4))
        target_duration_hrs = float(rng.uniform(0.08, 4.0))  # 5 mins to 4 hrs
    elif archetype == 2:
        sc_size = int(rng.integers(4, 11))
        target_duration_hrs = float(rng.uniform(2.0, 48.0))  # 2 to 48 hrs
    elif archetype == 3:
        sc_size = int(rng.integers(11, 26))
        target_duration_hrs = float(rng.uniform(48.0, 336.0)) # 2 to 14 days
    elif archetype == 4:
        sc_size = int(rng.integers(26, 61))
        target_duration_hrs = float(rng.uniform(168.0, 1080.0)) # 7 to 45 days
    else:
        sc_size = int(rng.integers(61, 151))
        target_duration_hrs = float(rng.uniform(336.0, 2160.0)) # 14 to 90 days

    sc_size = min(sc_size, n_licit_total - licit_idx)

    # Base timestamp: span realistically across 2012 to 2018
    sc_base_ts = random_timestamp_in_range(2012, 2018)

    # Intra-scenario timing: generate offsets within [0, target_duration_hrs]
    if sc_size == 1:
        time_offsets_s = [0.0]
    else:
        # Uniform or clustered offsets
        raw_offsets = rng.uniform(0, target_duration_hrs * 3600.0, size=sc_size)
        raw_offsets.sort()
        raw_offsets[0] = 0.0
        time_offsets_s = raw_offsets.tolist()

    # Scenario IP/ASN pool (1 to 3 IPs across 1-2 ASNs)
    n_ips_in_sc = 1 if sc_size <= 2 else (2 if sc_size <= 10 else random.randint(2, 4))
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips_in_sc, 2), replace=True)
    sc_ips = [gen_ipv4_for_asn(i + scenario_num) for i in range(n_ips_in_sc)]

    # Wallet reuse within licit scenario (sender/recipient relationships)
    sc_internal_wallets = [gen_unique_wallet(all_wallets) for _ in range(max(2, sc_size // 3))]

    for t in range(sc_size):
        txid_counter += 1
        tx_ts = sc_base_ts + pd.Timedelta(seconds=time_offsets_s[t])

        # Inputs/Outputs
        n_in = int(rng.choice([1, 1, 1, 2, 2, 3, 4], p=[0.40, 0.25, 0.15, 0.10, 0.05, 0.03, 0.02]))
        n_out = int(rng.choice([1, 1, 2, 2, 3, 4, 5], p=[0.20, 0.20, 0.25, 0.15, 0.10, 0.06, 0.04]))

        # Wallets
        input_addrs = []
        for j in range(n_in):
            if utxo_pool and random.random() < 0.25:
                w, _ = utxo_pool.pop(random.randint(0, len(utxo_pool) - 1))
                input_addrs.append(w)
            elif random.random() < 0.4 and sc_internal_wallets:
                input_addrs.append(random.choice(sc_internal_wallets))
            else:
                input_addrs.append(gen_unique_wallet(all_wallets))

        total_amount = sample_amount()
        fee = sample_fee()
        input_total = round(total_amount + fee, 8)
        input_amounts = distribute_amount(input_total, n_in)
        output_amounts = distribute_amount(total_amount, n_out)

        output_addrs = []
        for k in range(n_out):
            w = gen_unique_wallet(all_wallets)
            output_addrs.append(w)
            if len(utxo_pool) < 60000:
                utxo_pool.append((w, output_amounts[k]))

        # Network assignment from scenario pool
        ip_idx = random.randint(0, len(sc_ips) - 1)
        asn_choice = sc_asns[ip_idx % len(sc_asns)]
        ip_addr = sc_ips[ip_idx]

        # Probabilistic node_type: 75% residential/mobile/datacenter, 25% VPN/proxy for privacy
        if random.random() < LICIT_PRIVACY_FRACTION:
            node_type = random.choice(["vpn_proxy", "tor_exit_node", "datacenter"])
        else:
            node_type = asn_choice["infra"] if asn_choice["infra"] != "bulletproof_host" else "residential"

        licit_scenarios_records.append({
            "txid_counter": txid_counter,
            "timestamp": tx_ts,
            "input_addresses": json.dumps(input_addrs),
            "output_addresses": json.dumps(output_addrs),
            "input_amounts": json.dumps(input_amounts),
            "output_amounts": json.dumps(output_amounts),
            "fee_btc": fee,
            "script_type": sample_script_type(),
            "is_illicit": 0,
            "pattern_type": "normal",
            "scenario_id": sc_id,
            "relay_ip": ip_addr,
            "node_type": node_type,
            "asn": asn_choice["asn"],
            "isp": asn_choice["isp"],
            "country_code": asn_choice["country"],
            "_source": "elliptic_licit",
        })

    licit_idx += sc_size

print(f"  Generated {len(licit_scenarios_records):,} licit transactions across {scenario_num:,} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: CONSTRUCT HARD NEGATIVE (EXCHANGE) WALLETS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 3 — Constructing Hard Negative (Licit Exchange) Scenarios")
print("=" * 70)

exchange_records = []
for ex_idx in range(N_EXCHANGE_WALLETS):
    sc_id = f"exchange_{ex_idx + 1:03d}"
    ex_wallet = gen_unique_wallet(all_wallets)
    n_txns = random.randint(60, 260)

    # Exchange operating window: 2 days to 30 days
    op_days = float(rng.uniform(2.0, 30.0))
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    time_offsets_s = np.sort(rng.uniform(0, op_days * 86400.0, size=n_txns))
    time_offsets_s[0] = 0.0

    # Exchange server IP pool (2 to 4 IPs on cloud/datacenter/residential ASNs)
    ex_asns = rng.choice([a for a in GLOBAL_ASNS if a["country"] in ["US", "DE", "JP", "FR", "NL", "SG"]], size=2)
    ex_ips = [gen_ipv4_for_asn(ex_idx * 10 + i) for i in range(3)]

    for t in range(n_txns):
        txid_counter += 1
        tx_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[t]))
        fee = sample_fee()

        if random.random() < 0.6:
            # Fan-out: exchange withdrawal to users
            n_out = random.randint(2, 6)
            total_amount = sample_amount() * float(rng.uniform(2.0, 6.0))
            out_amounts = distribute_amount(round(total_amount, 8), n_out)
            in_amount = round(total_amount + fee, 8)
            output_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
            in_addrs = [ex_wallet]
            in_amounts = [in_amount]
        else:
            # Fan-in: users deposit to exchange
            n_in = random.randint(2, 5)
            total_amount = sample_amount() * float(rng.uniform(1.5, 4.0))
            in_amounts = distribute_amount(round(total_amount + fee, 8), n_in)
            out_amount = round(total_amount, 8)
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
            output_addrs = [ex_wallet]
            out_amounts = [out_amount]

        ip_choice = random.choice(ex_ips)
        asn_choice = random.choice(ex_asns)
        node_type = "datacenter" if random.random() < 0.7 else "residential"

        exchange_records.append({
            "txid_counter": txid_counter,
            "timestamp": tx_ts,
            "input_addresses": json.dumps(in_addrs),
            "output_addresses": json.dumps(output_addrs),
            "input_amounts": json.dumps(in_amounts),
            "output_amounts": json.dumps(out_amounts),
            "fee_btc": fee,
            "script_type": sample_script_type(),
            "is_illicit": 0,
            "pattern_type": "normal",
            "scenario_id": sc_id,
            "relay_ip": ip_choice,
            "node_type": node_type,
            "asn": asn_choice["asn"],
            "isp": asn_choice["isp"],
            "country_code": asn_choice["country"],
            "_source": "hard_negative_exchange",
        })

print(f"  Generated {len(exchange_records):,} exchange transactions across {N_EXCHANGE_WALLETS} exchanges")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: CONSTRUCT RANSOMWARE CAMPAIGNS (MULTI-ARCHETYPE, REALISTIC STRUCTURAL DIVERSITY)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 4 — Structuring Ransomware Campaigns with diverse operational archetypes")
print("=" * 70)

# Total target for ransomware: ~28,000 transactions
n_ransom_target = 28000
ransom_records = []
ransom_sc_counter = 0

# Sample heist addresses with labels
heist_pool = df_heist.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
heist_idx = 0

while len(ransom_records) < n_ransom_target:
    ransom_sc_counter += 1
    sc_id = f"ransom_{ransom_sc_counter:04d}"

    # Campaign scale archetype
    scale_arch = rng.choice([1, 2, 3, 4], p=[0.30, 0.40, 0.22, 0.08])
    if scale_arch == 1:
        camp_size = int(rng.integers(1, 5))
        camp_duration_hrs = float(rng.uniform(0.1, 8.0))   # 6 mins to 8 hrs
    elif scale_arch == 2:
        camp_size = int(rng.integers(5, 16))
        camp_duration_hrs = float(rng.uniform(4.0, 72.0))  # 4 to 72 hrs
    elif scale_arch == 3:
        camp_size = int(rng.integers(16, 36))
        camp_duration_hrs = float(rng.uniform(48.0, 360.0)) # 2 to 15 days
    else:
        camp_size = int(rng.integers(36, 76))
        camp_duration_hrs = float(rng.uniform(120.0, 800.0)) # 5 to 33 days

    remaining_ransom = n_ransom_target - len(ransom_records)
    camp_size = min(camp_size, remaining_ransom)

    # Base timestamp & timing offsets
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    if camp_size == 1:
        offsets_s = [0.0]
    else:
        offsets_s = np.sort(rng.uniform(0, camp_duration_hrs * 3600.0, size=camp_size))
        offsets_s[0] = 0.0

    # Campaign IP / ASN pool
    n_ips = 1 if camp_size <= 2 else random.randint(2, min(5, camp_size))
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True)
    sc_ips = [gen_ipv4_for_asn(ransom_sc_counter * 7 + i) for i in range(n_ips)]

    # Operational structure archetype:
    # 1. Unique Per-Victim HD Wallets + Tree Sweeps/Consolidation (35%) [Breaks static hub star]
    # 2. Static Campaign Wallet (Legacy WannaCry style) (25%)
    # 3. Affiliate Profit-Sharing Split (RaaS LockBit style) (25%)
    # 4. Rotating Syndicate Wallets + Direct Peels (15%)
    op_archetype = rng.choice([1, 2, 3, 4], p=[0.35, 0.25, 0.25, 0.15])

    # Core syndicate identity
    if heist_idx < len(heist_pool):
        primary_syndicate = heist_pool.iloc[heist_idx]["address"]
        heist_idx += 1
    else:
        primary_syndicate = gen_unique_wallet(all_wallets)

    if op_archetype == 1:
        # Per-victim unique addresses + sweep consolidation (overlaps with mixing reconvergence)
        n_victims = max(1, camp_size // 2)
        victim_deposit_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_victims)]
        unconsolidated = []

        for t in range(camp_size):
            txid_counter += 1
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            fee = sample_fee()

            if (t < n_victims) or (random.random() < 0.55 and unconsolidated == []):
                # Victim payout into assigned victim address, sometimes with multiple inputs (mimics normal user behavior)
                v_addr = victim_deposit_addrs[t % len(victim_deposit_addrs)]
                n_in = int(rng.choice([1, 2, 3, 4], p=[0.60, 0.25, 0.10, 0.05]))
                n_out = int(rng.choice([1, 2, 3], p=[0.5, 0.4, 0.1]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
                out_addrs = [v_addr] + [gen_unique_wallet(all_wallets) for _ in range(n_out - 1)]
                unconsolidated.append((v_addr, out_amts[0]))
            elif len(unconsolidated) >= 2 and random.random() < 0.7:
                # Sweep consolidation from 2-8 victim addresses (overlaps with mixing fan-in)
                n_sweep = min(len(unconsolidated), random.randint(2, 8))
                sweep_items = [unconsolidated.pop(0) for _ in range(n_sweep)]
                in_addrs = [w for w, _ in sweep_items]
                in_amts = [a for _, a in sweep_items]
                tot_in = round(sum(in_amts), 8)
                tot_out = round(tot_in - fee, 8)
                if tot_out <= 1e-6:
                    tot_out = 1e-6
                n_out = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
                out_amts = distribute_amount(tot_out, n_out)
                out_addrs = [primary_syndicate] + [gen_unique_wallet(all_wallets) for _ in range(n_out - 1)]
            else:
                # Operator movement / split from syndicate holding (overlaps with layering fan-out)
                n_in = int(rng.choice([1, 2], p=[0.8, 0.2]))
                n_out = int(rng.choice([1, 2, 3, 4, 5], p=[0.2, 0.3, 0.25, 0.15, 0.1]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [primary_syndicate] + [gen_unique_wallet(all_wallets) for _ in range(n_in - 1)]
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_idx = random.randint(0, len(sc_ips) - 1)
            asn_choice = sc_asns[ip_idx % len(sc_asns)]
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "bulletproof_host", "residential", "datacenter"])

            ransom_records.append({
                "txid_counter": txid_counter,
                "timestamp": tx_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "ransomware",
                "scenario_id": sc_id,
                "relay_ip": sc_ips[ip_idx],
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "ransomware_campaign",
            })

    elif op_archetype == 2:
        # Static Campaign Wallet (Legacy star-hub pattern) with occasional address reuse
        for t in range(camp_size):
            txid_counter += 1
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            fee = sample_fee()

            if random.random() < 0.65:
                # Victim paying ransom
                n_in = int(rng.choice([1, 2, 3, 4], p=[0.5, 0.3, 0.15, 0.05]))
                n_out = 1 if random.random() < 0.70 else 2
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
                out_addrs = [primary_syndicate]
                if n_out > 1:
                    # Occasional reuse of victim address for change
                    if random.random() < 0.3:
                        out_addrs.append(in_addrs[0])
                    else:
                        out_addrs.append(gen_unique_wallet(all_wallets))
            else:
                # Operator distributing funds
                n_in = int(rng.choice([1, 2], p=[0.7, 0.3]))
                n_out = int(rng.choice([1, 2, 3, 4], p=[0.3, 0.3, 0.2, 0.2]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [primary_syndicate] + [gen_unique_wallet(all_wallets) for _ in range(n_in - 1)]
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_idx = random.randint(0, len(sc_ips) - 1)
            asn_choice = sc_asns[ip_idx % len(sc_asns)]
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "bulletproof_host", "residential"])

            ransom_records.append({
                "txid_counter": txid_counter,
                "timestamp": tx_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "ransomware",
                "scenario_id": sc_id,
                "relay_ip": sc_ips[ip_idx],
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "ransomware_campaign",
            })

    elif op_archetype == 3:
        # Affiliate Profit-Sharing Model (overlaps with layering fan-out)
        n_affiliates = random.randint(1, 4)
        affiliate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_affiliates)]
        core_operator = primary_syndicate

        for t in range(camp_size):
            txid_counter += 1
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            fee = sample_fee()

            if random.random() < 0.60:
                # Victim payment split to multiple affiliates & core
                n_in = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                
                n_out_aff = random.randint(1, n_affiliates)
                active_affs = random.sample(affiliate_wallets, n_out_aff)
                
                p_affiliate_total = round(tot_amt * float(rng.uniform(0.60, 0.85)), 8)
                p_core = round(tot_amt - p_affiliate_total, 8)
                
                aff_amts = distribute_amount(p_affiliate_total, n_out_aff)
                
                out_addrs = active_affs + [core_operator]
                out_amts = aff_amts + [p_core]
                in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
            elif random.random() < 0.50:
                # Affiliate moves / hops their share (resembling layering)
                n_in = 1
                n_out = int(rng.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = [in_amt]
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [random.choice(affiliate_wallets)]
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
            else:
                # Core moves / hops their share
                n_in = int(rng.choice([1, 2], p=[0.8, 0.2]))
                n_out = int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [core_operator] + [gen_unique_wallet(all_wallets) for _ in range(n_in - 1)]
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_idx = random.randint(0, len(sc_ips) - 1)
            asn_choice = sc_asns[ip_idx % len(sc_asns)]
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "bulletproof_host", "datacenter", "residential"])

            ransom_records.append({
                "txid_counter": txid_counter,
                "timestamp": tx_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "ransomware",
                "scenario_id": sc_id,
                "relay_ip": sc_ips[ip_idx],
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "ransomware_campaign",
            })

    else:
        # Rotating Syndicate Wallets + Direct Peeling (overlaps with peeling chains)
        syndicate_wallets = [primary_syndicate] + [gen_unique_wallet(all_wallets) for _ in range(random.randint(2, 6))]
        for t in range(camp_size):
            txid_counter += 1
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            fee = sample_fee()
            target_syn = syndicate_wallets[t % len(syndicate_wallets)]

            if random.random() < 0.55:
                # Victim payout
                n_in = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
                n_out = int(rng.choice([1, 2, 3], p=[0.5, 0.4, 0.1]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
                out_addrs = [target_syn] + [gen_unique_wallet(all_wallets) for _ in range(n_out - 1)]
            else:
                # Direct peel / transfer from rotated wallet, occasionally sweeping multiple rotated wallets
                n_in = int(rng.choice([1, 2, 3], p=[0.7, 0.2, 0.1]))
                n_out = int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2]))
                tot_amt = sample_amount()
                in_amt = round(tot_amt + fee, 8)
                in_amts = distribute_amount(in_amt, n_in)
                out_amts = distribute_amount(tot_amt, n_out)
                in_addrs = [target_syn] + random.sample(syndicate_wallets, min(len(syndicate_wallets)-1, n_in - 1))
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            if random.random() < 0.35:
                for _ in range(random.randint(1, 6)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.3 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_idx = random.randint(0, len(sc_ips) - 1)
            asn_choice = sc_asns[ip_idx % len(sc_asns)]
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "bulletproof_host", "residential"])

            ransom_records.append({
                "txid_counter": txid_counter,
                "timestamp": tx_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "ransomware",
                "scenario_id": sc_id,
                "relay_ip": sc_ips[ip_idx],
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "ransomware_campaign",
            })

print(f"  Generated {len(ransom_records):,} ransomware transactions across {ransom_sc_counter:,} campaigns")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: PLANT STRUCTURALLY DIVERSE PEELING CHAINS (~2,500+ ROWS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 5 — Planting {N_PEELING_SCENARIOS} Structurally Diverse Peeling Chains")
print("=" * 70)

peeling_records = []

for sc_idx in range(N_PEELING_SCENARIOS):
    sc_id = f"peel_{sc_idx + 1:04d}"

    # Chain length diversity: short (4-8), medium (9-16), long (17-30)
    length_type = rng.choice([1, 2, 3], p=[0.40, 0.40, 0.20])
    if length_type == 1:
        n_hops = int(rng.integers(4, 9))
    elif length_type == 2:
        n_hops = int(rng.integers(9, 17))
    else:
        n_hops = int(rng.integers(17, 31))

    # Pacing: rapid automated (0.5 - 6 hrs), standard (6 - 36 hrs), slow stealth (36 - 280 hrs)
    pacing_type = rng.choice([1, 2, 3], p=[0.30, 0.45, 0.25])
    if pacing_type == 1:
        total_duration_hrs = float(rng.uniform(0.5, 6.0))
    elif pacing_type == 2:
        total_duration_hrs = float(rng.uniform(6.0, 36.0))
    else:
        total_duration_hrs = float(rng.uniform(36.0, 280.0))

    sc_base_ts = random_timestamp_in_range(2013, 2018)
    time_offsets_s = np.sort(rng.uniform(0, total_duration_hrs * 3600.0, size=n_hops))
    time_offsets_s[0] = 0.0

    # Scenario IP/ASN pool (1 to 3 IPs)
    n_ips = random.randint(1, 3)
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 13 + i) for i in range(n_ips)]

    # Peeling archetype:
    # 1. Classic Peeling with Direct Transfers & Multi-Outputs (35%) [breaks fanout_ratio==1.0]
    # 2. Bifurcated / Tree Peeling (25%) [splits into concurrent peeling sub-chains]
    # 3. Consolidated Peeling with Change Sweeps (25%) [breaks fanin_ratio==0.0]
    # 4. Rapid Variable-Peel Chains (15%)
    peel_arch = rng.choice([1, 2, 3, 4], p=[0.35, 0.25, 0.25, 0.15])

    initial_amount = round(float(rng.lognormal(-0.5, 1.2)), 8)
    initial_amount = max(initial_amount, 0.05)
    remaining = initial_amount
    current_wallet = gen_unique_wallet(all_wallets)

    if peel_arch == 2 and n_hops >= 8:
        # Bifurcated / Tree Peeling: forks at midpoint
        mid = n_hops // 2
        chain1_wallet = current_wallet
        chain1_remaining = remaining
        chain2_wallet = None
        chain2_remaining = 0.0

        for hop in range(n_hops):
            txid_counter += 1
            fee = sample_fee()
            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))

            if hop < mid:
                # Pre-split hops: regular peeling with occasional 1-to-1 transfer
                if random.random() < 0.25:
                    # 1-to-1 direct transfer
                    next_w = gen_unique_wallet(all_wallets)
                    pass_amt = round(chain1_remaining - fee, 8)
                    in_addrs = [chain1_wallet]
                    in_amts = [chain1_remaining]
                    out_addrs = [next_w]
                    out_amts = [pass_amt]
                    chain1_wallet = next_w
                    chain1_remaining = pass_amt
                else:
                    # 1-to-2 peel
                    peel_frac = float(rng.uniform(0.05, 0.20))
                    peel_amt = round(chain1_remaining * peel_frac, 8)
                    pass_amt = round(chain1_remaining - peel_amt - fee, 8)
                    if pass_amt <= 1e-6: break
                    peel_w = gen_unique_wallet(all_wallets)
                    next_w = gen_unique_wallet(all_wallets)
                    in_addrs = [chain1_wallet]
                    in_amts = [chain1_remaining]
                    out_addrs = [peel_w, next_w]
                    out_amts = [peel_amt, pass_amt]
                    chain1_wallet = next_w
                    chain1_remaining = pass_amt

            elif hop == mid:
                # Bifurcation fork transaction: 1 input -> 2 main branch outputs
                p1 = round((chain1_remaining - fee) * 0.55, 8)
                p2 = round(chain1_remaining - fee - p1, 8)
                w1 = gen_unique_wallet(all_wallets)
                w2 = gen_unique_wallet(all_wallets)
                in_addrs = [chain1_wallet]
                in_amts = [chain1_remaining]
                out_addrs = [w1, w2]
                out_amts = [p1, p2]
                chain1_wallet = w1
                chain1_remaining = p1
                chain2_wallet = w2
                chain2_remaining = p2

            else:
                # Alternating peels on branch 1 and branch 2
                active_b = 1 if (hop % 2 == 0) else 2
                cur_w = chain1_wallet if active_b == 1 else chain2_wallet
                cur_rem = chain1_remaining if active_b == 1 else chain2_remaining

                if cur_rem <= 2e-5:
                    continue

                if random.random() < 0.25:
                    next_w = gen_unique_wallet(all_wallets)
                    pass_amt = round(cur_rem - fee, 8)
                    in_addrs = [cur_w]
                    in_amts = [cur_rem]
                    out_addrs = [next_w]
                    out_amts = [pass_amt]
                    if active_b == 1:
                        chain1_wallet, chain1_remaining = next_w, pass_amt
                    else:
                        chain2_wallet, chain2_remaining = next_w, pass_amt
                else:
                    peel_frac = float(rng.uniform(0.08, 0.25))
                    peel_amt = round(cur_rem * peel_frac, 8)
                    pass_amt = round(cur_rem - peel_amt - fee, 8)
                    if pass_amt <= 1e-6: continue
                    peel_w = gen_unique_wallet(all_wallets)
                    next_w = gen_unique_wallet(all_wallets)
                    in_addrs = [cur_w]
                    in_amts = [cur_rem]
                    out_addrs = [peel_w, next_w]
                    out_amts = [peel_amt, pass_amt]
                    if active_b == 1:
                        chain1_wallet, chain1_remaining = next_w, pass_amt
                    else:
                        chain2_wallet, chain2_remaining = next_w, pass_amt



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.4:
                for _ in range(random.randint(1, 4)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.7 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            if random.random() < 0.2:
                for _ in range(random.randint(1, 2)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_choice = random.choice(sc_ips)
            asn_choice = random.choice(sc_asns)
            node_type = random.choice(["vpn_proxy", "tor_exit_node", "residential", "datacenter"])

            peeling_records.append({
                "txid_counter": txid_counter,
                "timestamp": hop_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "peeling_chain",
                "scenario_id": sc_id,
                "relay_ip": ip_choice,
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "planted_peeling_chain",
            })

    else:
        # Archetype 1, 3, 4: Sequential Peeling with variable multi-in/multi-out, change sweeps, and 1-to-1 hops
        peeled_wallets_pool = []
        for hop in range(n_hops):
            txid_counter += 1
            fee = sample_fee()
            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))

            # Multi-input sweep probability: sweep previously peeled change or external UTXO
            is_multi_in = (peel_arch == 3 and random.random() < 0.45) or (random.random() < 0.20)

            if is_multi_in:
                extra_ins = random.randint(1, 3)
                in_addrs = [current_wallet]
                in_amts = [remaining]
                total_in = remaining
                for _ in range(extra_ins):
                    if peeled_wallets_pool and random.random() < 0.60:
                        extra_w, extra_amt = peeled_wallets_pool.pop(random.randint(0, len(peeled_wallets_pool) - 1))
                    else:
                        extra_w = gen_unique_wallet(all_wallets)
                        extra_amt = round(float(rng.uniform(0.01, 0.10)), 8)
                    in_addrs.append(extra_w)
                    in_amts.append(extra_amt)
                    total_in = round(total_in + extra_amt, 8)
            else:
                in_addrs = [current_wallet]
                in_amts = [remaining]
                total_in = remaining

            # Hop structure:
            # 20% 1-to-1 direct hop (no peel, breaks fanout_ratio == 1.0)
            # 50% 1-to-2 standard peel
            # 20% 1-to-3 multi-output peel
            # 10% 1-to-4 or 1-to-5 large fanout peel
            hop_shape = rng.choice([1, 2, 3, 4], p=[0.20, 0.50, 0.20, 0.10])

            # Address reuse for change (decreses unique_output_addrs, decouples metrics)
            if random.random() < 0.15:
                next_w = current_wallet
            else:
                next_w = gen_unique_wallet(all_wallets)

            if hop_shape == 1:
                # 1-to-1 direct transfer
                pass_amt = round(total_in - fee, 8)
                if pass_amt <= 1e-6: break
                out_addrs = [next_w]
                out_amts = [pass_amt]
            elif hop_shape == 2:
                # 1-to-2 standard peel
                peel_frac = float(rng.uniform(0.04, 0.28))
                peel_amt = round(total_in * peel_frac, 8)
                pass_amt = round(total_in - peel_amt - fee, 8)
                if pass_amt <= 1e-6: break
                peel_w = gen_unique_wallet(all_wallets)
                out_addrs = [peel_w, next_w]
                out_amts = [peel_amt, pass_amt]
                peeled_wallets_pool.append((peel_w, peel_amt))
            elif hop_shape == 3:
                # 1-to-3 double peel
                peel_frac1 = float(rng.uniform(0.03, 0.15))
                peel_frac2 = float(rng.uniform(0.03, 0.15))
                peel_amt1 = round(total_in * peel_frac1, 8)
                peel_amt2 = round(total_in * peel_frac2, 8)
                pass_amt = round(total_in - peel_amt1 - peel_amt2 - fee, 8)
                if pass_amt <= 1e-6: break
                p_w1 = gen_unique_wallet(all_wallets)
                p_w2 = gen_unique_wallet(all_wallets)
                out_addrs = [p_w1, p_w2, next_w]
                out_amts = [peel_amt1, peel_amt2, pass_amt]
                peeled_wallets_pool.append((p_w1, peel_amt1))
                peeled_wallets_pool.append((p_w2, peel_amt2))
            else:
                # 1-to-4 or 1-to-5 large fanout peel
                n_peels = random.randint(3, 4)
                out_addrs = []
                out_amts = []
                for _ in range(n_peels):
                    p_w = gen_unique_wallet(all_wallets)
                    p_amt = round(total_in * float(rng.uniform(0.02, 0.08)), 8)
                    out_addrs.append(p_w)
                    out_amts.append(p_amt)
                    peeled_wallets_pool.append((p_w, p_amt))
                pass_amt = round(total_in - sum(out_amts) - fee, 8)
                if pass_amt <= 1e-6: break
                out_addrs.append(next_w)
                out_amts.append(pass_amt)



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.4:
                for _ in range(random.randint(1, 4)):
                    if len(out_amts) > 0 and out_amts[-1] > 0.05:
                        split_amt = round(out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        out_amts[-1] = round(out_amts[-1] - split_amt, 8)
                        out_addrs.append(random.choice(in_addrs) if random.random() < 0.7 else gen_unique_wallet(all_wallets))
                        out_amts.append(split_amt)
            if random.random() < 0.2:
                for _ in range(random.randint(1, 2)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    in_addrs.append(gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            # --------------------------
            res = round(sum(in_amts) - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            ip_choice = random.choice(sc_ips)
            asn_choice = random.choice(sc_asns)
            node_type = random.choice(["vpn_proxy", "tor_exit_node", "residential", "datacenter"])

            peeling_records.append({
                "txid_counter": txid_counter,
                "timestamp": hop_ts,
                "input_addresses": json.dumps(in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "peeling_chain",
                "scenario_id": sc_id,
                "relay_ip": ip_choice,
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "planted_peeling_chain",
            })

            current_wallet = next_w
            remaining = out_amts[-1]

print(f"  Planted {len(peeling_records):,} peeling chain transactions across {N_PEELING_SCENARIOS} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: PLANT STRUCTURALLY DIVERSE LAYERING CLUSTERS (~2,500+ ROWS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 6 — Planting {N_LAYERING_SCENARIOS} Structurally Diverse Layering Clusters")
print("=" * 70)

layering_records = []

for sc_idx in range(N_LAYERING_SCENARIOS):
    sc_id = f"layer_{sc_idx + 1:04d}"

    # Structural Archetype:
    # 1. Pure Fan-Out Dispersion (No Reconvergence) (30%) [breaks mandatory edge_to_node_ratio > 1.0]
    # 2. Multi-Tier Split-and-Merge / Criss-Cross (30%)
    # 3. Partial Reconvergence & Secondary Dispersion (25%)
    # 4. Daisy-Chain Relay Layering (15%)
    layer_arch = rng.choice([1, 2, 3, 4], p=[0.30, 0.30, 0.25, 0.15])

    n_fanout = int(rng.integers(3, 13))
    n_sources = int(rng.choice([1, 2, 3, 4], p=[0.40, 0.35, 0.15, 0.10]))

    pacing_arch = rng.choice([1, 2, 3], p=[0.25, 0.50, 0.25])
    if pacing_arch == 1:
        total_duration_hrs = float(rng.uniform(1.0, 8.0))
    elif pacing_arch == 2:
        total_duration_hrs = float(rng.uniform(8.0, 48.0))
    else:
        total_duration_hrs = float(rng.uniform(48.0, 350.0))

    sc_base_ts = random_timestamp_in_range(2013, 2018)

    # Network pool (1 to 4 IPs across 1-2 ASNs)
    n_ips = random.randint(2, 4)
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 17 + i) for i in range(n_ips)]

    # Source wallets and initial amount
    source_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_sources)]
    total_amount = round(float(rng.lognormal(0.2, 1.4)), 8)
    total_amount = max(total_amount, 0.15)

    # 1. INITIAL FAN-OUT TRANSACTION
    txid_counter += 1
    fee1 = sample_fee()
    in_amts = distribute_amount(round(total_amount + fee1, 8), n_sources)
    intermediate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
    out_amts = distribute_amount(total_amount, n_fanout)

    layering_records.append({
        "txid_counter": txid_counter,
        "timestamp": sc_base_ts,
        "input_addresses": json.dumps(source_wallets),
        "output_addresses": json.dumps(intermediate_wallets),
        "input_amounts": json.dumps(in_amts),
        "output_amounts": json.dumps(out_amts),
        "fee_btc": fee1,
        "script_type": sample_script_type(),
        "is_illicit": 1,
        "pattern_type": "layering",
        "scenario_id": sc_id,
        "relay_ip": random.choice(sc_ips),
        "node_type": random.choice(["vpn_proxy", "tor_exit_node", "bulletproof_host", "datacenter"]),
        "asn": random.choice(sc_asns)["asn"],
        "isp": random.choice(sc_asns)["isp"],
        "country_code": random.choice(sc_asns)["country"],
        "_source": "planted_layering",
    })

    # 2. INTERMEDIARY HOPS
    active_wallets = list(zip(intermediate_wallets, out_amts))
    next_stage_wallets = []
    stage1_duration = total_duration_hrs * 0.45
    intermediate_offsets_s = np.sort(rng.uniform(300.0, stage1_duration * 3600.0, size=n_fanout))

    for idx, (iw, ia) in enumerate(active_wallets):
        if random.random() < 0.70:
            txid_counter += 1
            fee_hop = min(sample_fee(), round(ia * 0.05, 8))
            fee_hop = max(fee_hop, 1e-8)
            hop_amt = round(ia - fee_hop, 8)
            if hop_amt <= 1e-6:
                next_stage_wallets.append((iw, ia))
                continue

            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(intermediate_offsets_s[idx]))

            # Sub-split (1-to-2) or 1-to-1 pass-through
            if random.random() < 0.40:
                if random.random() < 0.15:
                    w1 = random.choice(source_wallets)
                else:
                    w1 = gen_unique_wallet(all_wallets)
                w2 = gen_unique_wallet(all_wallets)
                parts = distribute_amount(hop_amt, 2)
                hop_out_addrs = [w1, w2]
                hop_out_amts = parts
                next_stage_wallets.append((w1, parts[0]))
                next_stage_wallets.append((w2, parts[1]))
            else:
                if random.random() < 0.15:
                    w1 = random.choice(source_wallets)
                else:
                    w1 = gen_unique_wallet(all_wallets)
                hop_out_addrs = [w1]
                hop_out_amts = [hop_amt]
                next_stage_wallets.append((w1, hop_amt))

            res = round(ia - sum(hop_out_amts) - fee_hop, 8)
            if res != 0:
                hop_out_amts[-1] = round(hop_out_amts[-1] + res, 8)

            layering_records.append({
                "txid_counter": txid_counter,
                "timestamp": hop_ts,
                "input_addresses": json.dumps([iw]),
                "output_addresses": json.dumps(hop_out_addrs),
                "input_amounts": json.dumps([ia]),
                "output_amounts": json.dumps(hop_out_amts),
                "fee_btc": fee_hop,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "layering",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["vpn_proxy", "tor_exit_node", "residential", "mobile"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_layering",
            })
        else:
            next_stage_wallets.append((iw, ia))

    # 3. CONSOLIDATION / DISPERSION STAGE
    if layer_arch == 1:
        # Pure Dispersion: intermediaries deposit directly to separate exit endpoints (NO reconvergence!)
        for w_item, a_item in next_stage_wallets:
            if random.random() < 0.50:
                txid_counter += 1
                fee_exit = min(sample_fee(), round(a_item * 0.05, 8))
                fee_exit = max(fee_exit, 1e-8)
                exit_amt = round(a_item - fee_exit, 8)
                if exit_amt <= 1e-6: continue
                exit_w = gen_unique_wallet(all_wallets)
                exit_ts = sc_base_ts + pd.Timedelta(hours=float(rng.uniform(stage1_duration, total_duration_hrs)))
                layering_records.append({
                    "txid_counter": txid_counter,
                    "timestamp": exit_ts,
                    "input_addresses": json.dumps([w_item]),
                    "output_addresses": json.dumps([exit_w]),
                    "input_amounts": json.dumps([a_item]),
                    "output_amounts": json.dumps([exit_amt]),
                    "fee_btc": fee_exit,
                    "script_type": sample_script_type(),
                    "is_illicit": 1,
                    "pattern_type": "layering",
                    "scenario_id": sc_id,
                    "relay_ip": random.choice(sc_ips),
                    "node_type": random.choice(["vpn_proxy", "tor_exit_node", "datacenter"]),
                    "asn": random.choice(sc_asns)["asn"],
                    "isp": random.choice(sc_asns)["isp"],
                    "country_code": random.choice(sc_asns)["country"],
                    "_source": "planted_layering",
                })

    elif layer_arch == 3:
        # Partial Reconvergence: 50% reconverge to collector, 50% exit independently
        n_recon = max(1, len(next_stage_wallets) // 2)
        recon_wallets = next_stage_wallets[:n_recon]
        exit_wallets = next_stage_wallets[n_recon:]

        # Fan-in recon_wallets
        collector_w = gen_unique_wallet(all_wallets)
        chunk_size = random.randint(2, 8)
        fanin_chunks = [recon_wallets[i:i + chunk_size] for i in range(0, len(recon_wallets), chunk_size)]
        fanin_ts_base = sc_base_ts + pd.Timedelta(hours=total_duration_hrs * 0.8)

        for c_idx, chunk in enumerate(fanin_chunks):
            txid_counter += 1
            chunk_in_addrs = [w for w, _ in chunk]
            chunk_in_amts = [a for _, a in chunk]
            tot_in = round(sum(chunk_in_amts), 8)
            fee_in = min(sample_fee(), round(tot_in * 0.05, 8))
            fee_in = max(fee_in, 1e-8)
            tot_out = round(tot_in - fee_in, 8)
            if tot_out <= 1e-6: continue
            fanin_ts = fanin_ts_base + pd.Timedelta(minutes=(c_idx + 1) * 20)

            layering_records.append({
                "txid_counter": txid_counter,
                "timestamp": fanin_ts,
                "input_addresses": json.dumps(chunk_in_addrs),
                "output_addresses": json.dumps([collector_w]),
                "input_amounts": json.dumps(chunk_in_amts),
                "output_amounts": json.dumps([tot_out]),
                "fee_btc": fee_in,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "layering",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["vpn_proxy", "tor_exit_node", "datacenter"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_layering",
            })

    else:
        # Full / Standard Fan-In Consolidation
        n_collectors = 1 if random.random() < 0.70 else 2
        collector_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_collectors)]
        chunk_size = random.randint(3, 10)
        fanin_chunks = [next_stage_wallets[i:i + chunk_size] for i in range(0, len(next_stage_wallets), chunk_size)]
        fanin_ts_base = sc_base_ts + pd.Timedelta(hours=total_duration_hrs * 0.8)

        for c_idx, chunk in enumerate(fanin_chunks):
            txid_counter += 1
            chunk_in_addrs = [w for w, _ in chunk]
            chunk_in_amts = [a for _, a in chunk]
            tot_in = round(sum(chunk_in_amts), 8)
            fee_in = min(sample_fee(), round(tot_in * 0.05, 8))
            fee_in = max(fee_in, 1e-8)
            tot_out = round(tot_in - fee_in, 8)
            if tot_out <= 1e-6: continue
            chunk_out_addrs = collector_wallets if n_collectors <= len(collector_wallets) else [collector_wallets[0]]
            chunk_out_amts = distribute_amount(tot_out, len(chunk_out_addrs))
            fanin_ts = fanin_ts_base + pd.Timedelta(minutes=(c_idx + 1) * 30)



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.3:
                for _ in range(random.randint(1, 3)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    chunk_in_addrs.append(random.choice(chunk_in_addrs) if random.random() < 0.4 else gen_unique_wallet(all_wallets))
                    chunk_in_amts.append(dust)
                    if len(chunk_out_amts) > 0: chunk_out_amts[0] = round(chunk_out_amts[0] + dust, 8)
            if random.random() < 0.3:
                for _ in range(random.randint(1, 3)):
                    if len(chunk_out_amts) > 0 and chunk_out_amts[-1] > 0.05:
                        split_amt = round(chunk_out_amts[-1] * float(rng.uniform(0.1, 0.4)), 8)
                        chunk_out_amts[-1] = round(chunk_out_amts[-1] - split_amt, 8)
                        chunk_out_addrs.append(random.choice(chunk_in_addrs) if random.random() < 0.4 else gen_unique_wallet(all_wallets))
                        chunk_out_amts.append(split_amt)
            # --------------------------
            res = round(tot_in - sum(chunk_out_amts) - fee_in, 8)
            if res != 0:
                chunk_out_amts[-1] = round(chunk_out_amts[-1] + res, 8)

            layering_records.append({
                "txid_counter": txid_counter,
                "timestamp": fanin_ts,
                "input_addresses": json.dumps(chunk_in_addrs),
                "output_addresses": json.dumps(chunk_out_addrs),
                "input_amounts": json.dumps(chunk_in_amts),
                "output_amounts": json.dumps(chunk_out_amts),
                "fee_btc": fee_in,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "layering",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["vpn_proxy", "tor_exit_node", "residential", "datacenter"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_layering",
            })

print(f"  Planted {len(layering_records):,} layering transactions across {N_LAYERING_SCENARIOS} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: PLANT STRUCTURALLY DIVERSE MIXING CLUSTERS (~2,500+ ROWS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 7 — Planting {N_MIXING_SCENARIOS} Structurally Diverse Mixing Clusters")
print("=" * 70)

mixing_records = []

for sc_idx in range(N_MIXING_SCENARIOS):
    sc_id = f"mix_{sc_idx + 1:04d}"

    # Structural Archetype:
    # 1. Tiered & Multi-Denomination CoinJoin (Wasabi / Whirlpool style) (35%)
    # 2. Whirlpool-style Fixed Pools with Churn & Exits (30%)
    # 3. JoinMarket-style Maker/Taker Asymmetric Mix (20%)
    # 4. Decentralized Multi-Round P2P Mini-Mixes (15%)
    mix_arch = rng.choice([1, 2, 3, 4], p=[0.35, 0.30, 0.20, 0.15])

    n_rounds = int(rng.integers(2, 7))
    n_participants = int(rng.integers(3, 8))

    pacing_arch = rng.choice([1, 2, 3], p=[0.30, 0.45, 0.25])
    if pacing_arch == 1:
        total_duration_hrs = float(rng.uniform(1.0, 6.0))
    elif pacing_arch == 2:
        total_duration_hrs = float(rng.uniform(6.0, 36.0))
    else:
        total_duration_hrs = float(rng.uniform(36.0, 200.0))

    sc_base_ts = random_timestamp_in_range(2013, 2018)
    round_offsets_s = np.sort(rng.uniform(0, total_duration_hrs * 3600.0, size=n_rounds))
    round_offsets_s[0] = 0.0

    # Participants bring their own IPs
    n_ips = min(n_participants, random.randint(3, 5))
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 23 + i) for i in range(n_ips)]

    # Initial participant wallets
    participant_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
    base_denom = round(float(rng.lognormal(-0.8, 0.9)), 8)
    base_denom = max(base_denom, 0.02)

    current_in_wallets = participant_wallets.copy()
    current_amount_per_p = base_denom

    # Pre-mix split or relay hops (Tx0)
    n_premix = random.randint(1, 2)
    for p_idx in range(n_premix):
        txid_counter += 1
        fee_pre = sample_fee()
        pre_ts = sc_base_ts - pd.Timedelta(minutes=random.randint(10, 120))
        n_pre_ins = random.randint(1, 3)
        pre_in_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_pre_ins)]

        if random.random() < 0.40:
            # Pre-mix relay transfer (multiple inputs to 1 output)
            raw_deposit = round(base_denom + fee_pre, 8)
            pre_in_amts = distribute_amount(raw_deposit, n_pre_ins)
            mixing_records.append({
                "txid_counter": txid_counter,
                "timestamp": pre_ts,
                "input_addresses": json.dumps(pre_in_wallets),
                "output_addresses": json.dumps([current_in_wallets[p_idx]]),
                "input_amounts": json.dumps(pre_in_amts),
                "output_amounts": json.dumps([base_denom]),
                "fee_btc": fee_pre,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "mixing",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["tor_exit_node", "vpn_proxy", "residential"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_mixing",
            })
        else:
            # Pre-mix split + change (multiple inputs to 2 outputs)
            raw_deposit = round(base_denom * float(rng.uniform(1.2, 1.8)) + fee_pre, 8)
            pre_in_amts = distribute_amount(raw_deposit, n_pre_ins)
            pre_change = gen_unique_wallet(all_wallets)
            mixing_records.append({
                "txid_counter": txid_counter,
                "timestamp": pre_ts,
                "input_addresses": json.dumps(pre_in_wallets),
                "output_addresses": json.dumps([current_in_wallets[p_idx], pre_change]),
                "input_amounts": json.dumps(pre_in_amts),
                "output_amounts": json.dumps([base_denom, round(raw_deposit - base_denom - fee_pre, 8)]),
                "fee_btc": fee_pre,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "mixing",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["tor_exit_node", "vpn_proxy", "residential"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_mixing",
            })

    if mix_arch == 3:
        # JoinMarket-style Maker/Taker Asymmetric Mix
        # 1 Taker brings 2 inputs, pays fee to N-1 Makers (1 input each)
        for rnd in range(n_rounds):
            txid_counter += 1
            fee = sample_fee()
            round_ts = sc_base_ts + pd.Timedelta(seconds=float(round_offsets_s[rnd]))

            taker_extra_in = gen_unique_wallet(all_wallets)
            taker_inputs = [current_in_wallets[0], taker_extra_in]
            maker_inputs = current_in_wallets[1:]
            round_in_addrs = taker_inputs + maker_inputs

            maker_amt = base_denom
            taker_amt1 = round(base_denom * 0.7, 8)
            taker_amt2 = round(base_denom * 0.5, 8)
            round_in_amts = [taker_amt1, taker_amt2] + [maker_amt] * len(maker_inputs)
            total_in = round(sum(round_in_amts), 8)

            # Equal mixed output + maker reward + taker change
            mixed_output_amt = base_denom
            maker_reward = round(base_denom * 0.002, 8)
            total_makers = len(maker_inputs)
            taker_change = round(total_in - (mixed_output_amt * n_participants) - (maker_reward * total_makers) - fee, 8)
            if taker_change <= 1e-6: taker_change = 1e-6

            new_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
            taker_change_wallet = gen_unique_wallet(all_wallets)
            maker_fee_wallets = [gen_unique_wallet(all_wallets) for _ in range(total_makers)]

            round_out_addrs = new_wallets + [taker_change_wallet] + maker_fee_wallets
            round_out_amts = [mixed_output_amt] * n_participants + [taker_change] + [maker_reward] * total_makers



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.2:
                for _ in range(random.randint(1, 2)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    round_in_addrs.append(gen_unique_wallet(all_wallets))
                    round_in_amts.append(dust)
                    if len(round_out_amts) > 0: round_out_amts[0] = round(round_out_amts[0] + dust, 8)
            if random.random() < 0.3 and len(round_out_addrs) > 0:
                for _ in range(max(1, len(round_out_addrs)//3)):
                    idx = random.randint(0, len(round_out_addrs)-1)
                    round_out_addrs[idx] = random.choice(round_in_addrs) if random.random() < 0.6 else gen_unique_wallet(all_wallets)
            # --------------------------
            res = round(total_in - sum(round_out_amts) - fee, 8)
            if res != 0:
                round_out_amts[-1] = round(round_out_amts[-1] + res, 8)

            ip_choice = random.choice(sc_ips)
            asn_choice = random.choice(sc_asns)
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "residential"])

            mixing_records.append({
                "txid_counter": txid_counter,
                "timestamp": round_ts,
                "input_addresses": json.dumps(round_in_addrs),
                "output_addresses": json.dumps(round_out_addrs),
                "input_amounts": json.dumps(round_in_amts),
                "output_amounts": json.dumps(round_out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "mixing",
                "scenario_id": sc_id,
                "relay_ip": ip_choice,
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "planted_mixing",
            })
            current_in_wallets = new_wallets

    else:
        # Archetypes 1, 2, 4: CoinJoin with Tiered Denominations, Churn & Change
        for rnd in range(n_rounds):
            txid_counter += 1
            fee = sample_fee()
            round_ts = sc_base_ts + pd.Timedelta(seconds=float(round_offsets_s[rnd]))

            # In Archetype 2 (churn), only a subset continues to later rounds
            if mix_arch == 2 and rnd >= 1:
                active_p_count = max(3, n_participants - rnd)
                churn_in_wallets = current_in_wallets[:active_p_count]
                # External liquidity joins
                new_externals = [gen_unique_wallet(all_wallets) for _ in range(n_participants - active_p_count)]
                round_in_addrs = churn_in_wallets + new_externals
            else:
                round_in_addrs = current_in_wallets.copy()

            total_in = round(current_amount_per_p * len(round_in_addrs), 8)
            total_out = round(total_in - fee, 8)
            out_per_p = round(total_out / len(round_in_addrs), 8)
            new_wallets = [gen_unique_wallet(all_wallets) for _ in range(len(round_in_addrs))]

            # Multi-denomination change or unequal outputs (Wasabi style, 45% of rounds)
            if mix_arch == 1 and random.random() < 0.60:
                change_wallets = [gen_unique_wallet(all_wallets) for _ in range(len(round_in_addrs))]
                denom_amt = round(out_per_p * float(rng.uniform(0.70, 0.90)), 8)
                change_amt = round((total_out - (denom_amt * len(round_in_addrs))) / len(round_in_addrs), 8)
                out_addrs = new_wallets + change_wallets
                out_amts = [denom_amt] * len(round_in_addrs) + [change_amt] * len(round_in_addrs)
                current_amount_per_p = denom_amt
            else:
                out_addrs = new_wallets
                out_amts = [out_per_p] * len(round_in_addrs)
                current_amount_per_p = out_per_p



            # --- V4 NOISE INJECTION ---
            if random.random() < 0.2:
                for _ in range(random.randint(1, 2)):
                    dust = round(float(rng.uniform(0.001, 0.02)), 8)
                    round_in_addrs.append(gen_unique_wallet(all_wallets))
                    in_amts.append(dust)
                    if len(out_amts) > 0: out_amts[0] = round(out_amts[0] + dust, 8)
            if random.random() < 0.3 and len(out_addrs) > 0:
                for _ in range(max(1, len(out_addrs)//3)):
                    idx = random.randint(0, len(out_addrs)-1)
                    out_addrs[idx] = random.choice(round_in_addrs) if random.random() < 0.6 else gen_unique_wallet(all_wallets)
            # --------------------------
            res = round(total_in - sum(out_amts) - fee, 8)
            if res != 0:
                out_amts[-1] = round(out_amts[-1] + res, 8)

            in_amts = distribute_amount(round(total_in, 8), len(round_in_addrs))

            ip_choice = random.choice(sc_ips)
            asn_choice = random.choice(sc_asns)
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "residential", "datacenter"])

            mixing_records.append({
                "txid_counter": txid_counter,
                "timestamp": round_ts,
                "input_addresses": json.dumps(round_in_addrs),
                "output_addresses": json.dumps(out_addrs),
                "input_amounts": json.dumps(in_amts),
                "output_amounts": json.dumps(out_amts),
                "fee_btc": fee,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "mixing",
                "scenario_id": sc_id,
                "relay_ip": ip_choice,
                "node_type": node_type,
                "asn": asn_choice["asn"],
                "isp": asn_choice["isp"],
                "country_code": asn_choice["country"],
                "_source": "planted_mixing",
            })
            current_in_wallets = new_wallets

    # Post-mix consolidation / payout
    if random.random() < 0.35 and len(current_in_wallets) >= 2:
        # Consolidation exit (mimics layering fan-in)
        txid_counter += 1
        fee_post = sample_fee()
        n_cons = random.randint(2, len(current_in_wallets))
        cons_in_wallets = current_in_wallets[:n_cons]
        post_in_amts = [round(current_amount_per_p, 8) for _ in range(n_cons)]
        tot_post_in = round(sum(post_in_amts), 8)
        tot_post_out = round(tot_post_in - fee_post, 8)
        if tot_post_out > 1e-6:
            cold_wallet = gen_unique_wallet(all_wallets)
            post_ts = sc_base_ts + pd.Timedelta(seconds=float(round_offsets_s[-1])) + pd.Timedelta(minutes=random.randint(15, 180))
            mixing_records.append({
                "txid_counter": txid_counter,
                "timestamp": post_ts,
                "input_addresses": json.dumps(cons_in_wallets),
                "output_addresses": json.dumps([cold_wallet]),
                "input_amounts": json.dumps(post_in_amts),
                "output_amounts": json.dumps([tot_post_out]),
                "fee_btc": fee_post,
                "script_type": sample_script_type(),
                "is_illicit": 1,
                "pattern_type": "mixing",
                "scenario_id": sc_id,
                "relay_ip": random.choice(sc_ips),
                "node_type": random.choice(["tor_exit_node", "vpn_proxy", "residential"]),
                "asn": random.choice(sc_asns)["asn"],
                "isp": random.choice(sc_asns)["isp"],
                "country_code": random.choice(sc_asns)["country"],
                "_source": "planted_mixing",
            })
    else:
        # Individual exits
        n_postmix = random.randint(1, 2)
        for p_idx in range(n_postmix):
            if p_idx < len(current_in_wallets):
                txid_counter += 1
                fee_post = sample_fee()
                post_in_amt = round(current_amount_per_p, 8)
                post_out_amt = round(post_in_amt - fee_post, 8)
                if post_out_amt > 1e-6:
                    cold_wallet = gen_unique_wallet(all_wallets)
                    post_ts = sc_base_ts + pd.Timedelta(seconds=float(round_offsets_s[-1])) + pd.Timedelta(minutes=random.randint(15, 180))
                    mixing_records.append({
                        "txid_counter": txid_counter,
                        "timestamp": post_ts,
                        "input_addresses": json.dumps([current_in_wallets[p_idx]]),
                        "output_addresses": json.dumps([cold_wallet]),
                        "input_amounts": json.dumps([post_in_amt]),
                        "output_amounts": json.dumps([post_out_amt]),
                        "fee_btc": fee_post,
                        "script_type": sample_script_type(),
                        "is_illicit": 1,
                        "pattern_type": "mixing",
                        "scenario_id": sc_id,
                        "relay_ip": random.choice(sc_ips),
                        "node_type": random.choice(["tor_exit_node", "vpn_proxy", "residential"]),
                        "asn": random.choice(sc_asns)["asn"],
                        "isp": random.choice(sc_asns)["isp"],
                        "country_code": random.choice(sc_asns)["country"],
                        "_source": "planted_mixing",
                    })

print(f"  Planted {len(mixing_records):,} mixing transactions across {N_MIXING_SCENARIOS} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: MERGE, DEDUPLICATE, SHUFFLE & HASH TXIDS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 8 — Merging records and assigning hash-shuffled txids")
print("=" * 70)

all_records = (
    licit_scenarios_records +
    exchange_records +
    ransom_records +
    peeling_records +
    layering_records +
    mixing_records
)

df_all = pd.DataFrame(all_records)
print(f"  Total records generated: {len(df_all):,}")
print(df_all["pattern_type"].value_counts().to_string())

# Assign hash-shuffled txids
print("  Assigning shuffled txids...")
shuffle_order = rng.permutation(len(df_all))
txid_map = {}
for new_pos, old_pos in enumerate(shuffle_order):
    counter_val = df_all.iloc[old_pos]["txid_counter"]
    txid_map[counter_val] = make_txid(new_pos)

df_all["txid"] = df_all["txid_counter"].map(txid_map)

# Resolve collisions if any
while df_all["txid"].duplicated().any():
    dup_mask = df_all["txid"].duplicated(keep="first")
    for idx in df_all[dup_mask].index:
        txid_counter += 1
        df_all.at[idx, "txid"] = make_txid(txid_counter + random.randint(1, 1000000))

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: TIMESTAMPS & RELAY TIMESTAMPS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 9 — Setting relay_timestamps (50-500 ms before block timestamp)")
print("=" * 70)

df_all["timestamp"] = pd.to_datetime(df_all["timestamp"]).dt.floor("s")
random_ms = rng.integers(50, 501, size=len(df_all))
df_all["relay_timestamp"] = df_all["timestamp"] - pd.to_timedelta(random_ms, unit="ms")

# Other network fields
df_all["protocol_version"] = 70015
df_all["user_agent"] = rng.choice(USER_AGENTS, size=len(df_all), p=USER_AGENT_WEIGHTS)

# Standard vs dynamic ports (85% port 8333, 15% dynamic/alt)
is_standard_port = rng.random(len(df_all)) < 0.85
alt_ports = rng.choice([18333] + list(range(49152, 65536, 64)), size=len(df_all))
df_all["relay_port"] = np.where(is_standard_port, 8333, alt_ports)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: SCENARIO-LEVEL STRATIFIED TRAIN/TEST SPLIT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 10 — Scenario-level stratified train/test split")
print("=" * 70)

scenario_summary = df_all.groupby("scenario_id").agg(
    is_illicit=("is_illicit", "first"),
    pattern_type=("pattern_type", "first"),
    n_txns=("txid", "count"),
).reset_index()

scenario_summary["strat_key"] = (
    scenario_summary["is_illicit"].astype(str) + "_" + scenario_summary["pattern_type"]
)

splitter = StratifiedShuffleSplit(n_splits=1, test_size=SPLIT_RATIO, random_state=SEED)
train_sc_idx, test_sc_idx = next(splitter.split(scenario_summary, scenario_summary["strat_key"]))

train_scenarios = set(scenario_summary.iloc[train_sc_idx]["scenario_id"])
test_scenarios = set(scenario_summary.iloc[test_sc_idx]["scenario_id"])

# Strict verification of zero leak
leak_check = train_scenarios & test_scenarios
assert len(leak_check) == 0, f"Leaking scenarios detected: {len(leak_check)}"

df_all["split"] = df_all["scenario_id"].apply(lambda s: "train" if s in train_scenarios else "test")

print(f"  Total scenarios: {len(scenario_summary):,}")
print(f"  Train scenarios: {len(train_scenarios):,} | Test scenarios: {len(test_scenarios):,}")
print(f"  Shared scenarios: {len(leak_check)}")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 11: SAVE MASTER AND SPLIT CSV FILES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 11 — Formatting and saving 6 CSV files")
print("=" * 70)

# Format timestamp strings
df_all["timestamp_str"] = df_all["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
df_all["relay_timestamp_str"] = df_all["relay_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]

blockchain_cols = [
    "txid", "timestamp", "input_addresses", "output_addresses",
    "input_amounts", "output_amounts", "fee_btc", "script_type",
    "is_illicit", "pattern_type", "scenario_id", "split",
]
df_blockchain = df_all[blockchain_cols].copy()
df_blockchain["timestamp"] = df_all["timestamp_str"]

network_cols = [
    "txid", "relay_timestamp", "relay_ip", "relay_port", "node_type",
    "country_code", "asn", "isp", "protocol_version", "user_agent",
    "scenario_id", "split",
]
df_network = df_all[network_cols].copy()
df_network["relay_timestamp"] = df_all["relay_timestamp_str"]

# Save masters
blockchain_path = os.path.join(PROC_DIR, "blockchain_transactions.csv")
network_path = os.path.join(PROC_DIR, "network_metadata.csv")
df_blockchain.to_csv(blockchain_path, index=False)
df_network.to_csv(network_path, index=False)
print(f"  Saved {blockchain_path} ({len(df_blockchain):,} rows)")
print(f"  Saved {network_path} ({len(df_network):,} rows)")

# Save split files
for split_name in ["train", "test"]:
    mask = df_all["split"] == split_name
    b_split = df_blockchain[mask]
    n_split = df_network[mask]
    b_split.to_csv(os.path.join(PROC_DIR, f"{split_name}_blockchain.csv"), index=False)
    n_split.to_csv(os.path.join(PROC_DIR, f"{split_name}_network.csv"), index=False)
    print(f"  Saved {split_name}_blockchain.csv and {split_name}_network.csv ({len(b_split):,} rows)")

print("\n" + "=" * 70)
print("🎉 v3.0 GENERATION COMPLETE")
print("=" * 70)
