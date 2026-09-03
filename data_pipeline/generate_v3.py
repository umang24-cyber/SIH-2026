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
# PHASE 4: CONSTRUCT RANSOMWARE CAMPAIGNS (MULTI-TRANSACTION, REALISTIC DURATION)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 4 — Structuring Ransomware Campaigns with realistic durations & sizes")
print("=" * 70)

# Total illicit Elliptic rows + Heist data
# Total target for ransomware: ~28,000 transactions
# Grouped into campaigns with sizes from 1 to 70 transactions, durations from 1 hour to 30 days!

n_ransom_target = 28000
ransom_records = []
ransom_sc_counter = 0

# Sample heist addresses with labels
heist_pool = df_heist.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
heist_idx = 0

while len(ransom_records) < n_ransom_target:
    ransom_sc_counter += 1
    sc_id = f"ransom_{ransom_sc_counter:04d}"

    # Campaign archetype
    arch = rng.choice([1, 2, 3, 4], p=[0.30, 0.40, 0.22, 0.08])
    if arch == 1:
        camp_size = int(rng.integers(1, 4))
        camp_duration_hrs = float(rng.uniform(0.1, 8.0)) # 6 mins to 8 hrs
    elif arch == 2:
        camp_size = int(rng.integers(4, 15))
        camp_duration_hrs = float(rng.uniform(4.0, 72.0)) # 4 to 72 hrs
    elif arch == 3:
        camp_size = int(rng.integers(15, 35))
        camp_duration_hrs = float(rng.uniform(48.0, 360.0)) # 2 to 15 days
    else:
        camp_size = int(rng.integers(35, 75))
        camp_duration_hrs = float(rng.uniform(120.0, 800.0)) # 5 to 33 days

    remaining_ransom = n_ransom_target - len(ransom_records)
    camp_size = min(camp_size, remaining_ransom)

    # Base timestamp
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    if camp_size == 1:
        offsets_s = [0.0]
    else:
        offsets_s = np.sort(rng.uniform(0, camp_duration_hrs * 3600.0, size=camp_size))
        offsets_s[0] = 0.0

    # Campaign IP / ASN pool (victims + syndicate servers)
    n_ips = 1 if camp_size <= 2 else random.randint(2, min(5, camp_size))
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True)
    sc_ips = [gen_ipv4_for_asn(ransom_sc_counter * 7 + i) for i in range(n_ips)]

    # Primary syndicate wallet for this campaign
    if heist_idx < len(heist_pool):
        syndicate_wallet = heist_pool.iloc[heist_idx]["address"]
        heist_idx += 1
    else:
        syndicate_wallet = gen_unique_wallet(all_wallets)

    for t in range(camp_size):
        txid_counter += 1
        tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
        fee = sample_fee()

        # Some transactions are victim payments (fan-in to ransom wallet)
        # Some are distribution / consolidation hops
        if random.random() < 0.7:
            # Victim paying ransom
            n_in = int(rng.choice([1, 1, 2], p=[0.6, 0.3, 0.1]))
            n_out = 1 if random.random() < 0.7 else 2
            total_amount = sample_amount()
            in_amount = round(total_amount + fee, 8)
            in_amounts = distribute_amount(in_amount, n_in)
            out_amounts = distribute_amount(total_amount, n_out)

            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
            out_addrs = [syndicate_wallet]
            if n_out > 1:
                out_addrs.append(gen_unique_wallet(all_wallets))
        else:
            # Ransomware operator moving funds
            n_in = 1
            n_out = int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2]))
            total_amount = sample_amount()
            in_amount = round(total_amount + fee, 8)
            in_amounts = [in_amount]
            out_amounts = distribute_amount(total_amount, n_out)
            in_addrs = [syndicate_wallet]
            out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]

        # Network assignment
        ip_idx = random.randint(0, len(sc_ips) - 1)
        ip_choice = sc_ips[ip_idx]
        asn_choice = sc_asns[ip_idx % len(sc_asns)]

        # Node type: 55% suspicious (VPN/Tor/Bulletproof), 45% normal (victim residential/mobile/cloud)
        if random.random() < (1.0 - ILLICIT_NORMAL_FRACTION):
            node_type = random.choice(["tor_exit_node", "vpn_proxy", "bulletproof_host"])
        else:
            node_type = asn_choice["infra"] if asn_choice["infra"] in ["residential", "mobile", "datacenter"] else "residential"

        ransom_records.append({
            "txid_counter": txid_counter,
            "timestamp": tx_ts,
            "input_addresses": json.dumps(in_addrs),
            "output_addresses": json.dumps(out_addrs),
            "input_amounts": json.dumps(in_amounts),
            "output_amounts": json.dumps(out_amounts),
            "fee_btc": fee,
            "script_type": sample_script_type(),
            "is_illicit": 1,
            "pattern_type": "ransomware",
            "scenario_id": sc_id,
            "relay_ip": ip_choice,
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

    # Structural diversity in peeling chains:
    # 1. Chain length: short (4-8 hops), medium (9-16 hops), long (17-28 hops)
    length_type = rng.choice([1, 2, 3], p=[0.40, 0.40, 0.20])
    if length_type == 1:
        n_hops = int(rng.integers(4, 9))
    elif length_type == 2:
        n_hops = int(rng.integers(9, 17))
    else:
        n_hops = int(rng.integers(17, 29))

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

    # Branching probability: 20% of peeling chains fork into 2 sub-chains at midpoint
    does_branch = (random.random() < 0.20) and (n_hops >= 8)

    # Multi-input peel probability: 25% of peeling chains use 2 inputs at initial or intermediate hops
    uses_multi_in = (random.random() < 0.25)

    # Scenario IP/ASN pool (1 to 3 IPs)
    n_ips = random.randint(1, 3)
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 13 + i) for i in range(n_ips)]

    # Initial funds
    initial_amount = round(float(rng.lognormal(-0.5, 1.2)), 8)
    initial_amount = max(initial_amount, 0.05)
    remaining = initial_amount
    current_wallet = gen_unique_wallet(all_wallets)

    for hop in range(n_hops):
        txid_counter += 1
        fee = sample_fee()
        hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))

        # Inputs
        if hop == 0 and uses_multi_in:
            in_wallet2 = gen_unique_wallet(all_wallets)
            in_addrs = [current_wallet, in_wallet2]
            p1 = round(remaining * 0.65, 8)
            p2 = round(remaining - p1, 8)
            in_amts = [p1, p2]
        else:
            in_addrs = [current_wallet]
            in_amts = [remaining]

        # Outputs
        peel_frac = round(float(rng.uniform(0.04, 0.25)), 4)
        peel_amt = round(remaining * peel_frac, 8)
        pass_amt = round(remaining - peel_amt - fee, 8)

        if pass_amt < 1e-6:
            break

        peel_wallet = gen_unique_wallet(all_wallets)
        next_wallet = gen_unique_wallet(all_wallets)

        # Multi-output peel (peeling to 2 distinct recipients at once)
        if random.random() < 0.20 and peel_amt > 2e-6:
            peel_amt1 = round(peel_amt * 0.5, 8)
            peel_amt2 = round(peel_amt - peel_amt1, 8)
            peel_wallet2 = gen_unique_wallet(all_wallets)
            out_addrs = [peel_wallet, peel_wallet2, next_wallet]
            out_amts = [peel_amt1, peel_amt2, pass_amt]
        else:
            out_addrs = [peel_wallet, next_wallet]
            out_amts = [peel_amt, pass_amt]

        # Adjust residual
        total_in = round(sum(in_amts), 8)
        total_out = round(sum(out_amts), 8)
        residual = round(total_in - total_out - fee, 8)
        if residual != 0:
            out_amts[-1] = round(out_amts[-1] + residual, 8)

        # Network assignment
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

        current_wallet = next_wallet
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

    # Structural diversity:
    # Fan-out width: 3 to 12 intermediaries
    n_fanout = int(rng.integers(3, 13))

    # Multi-source: 1 to 3 sources
    n_sources = int(rng.choice([1, 2, 3], p=[0.60, 0.30, 0.10]))

    # Pacing: fast (1-8 hrs), medium (8-48 hrs), slow/multi-week (48-350 hrs)
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

    # 1. FAN-OUT TRANSACTION
    txid_counter += 1
    fee1 = sample_fee()
    in_amts = distribute_amount(round(total_amount + fee1, 8), n_sources)
    intermediate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
    out_amts = distribute_amount(total_amount, n_fanout)

    ip_choice = random.choice(sc_ips)
    asn_choice = random.choice(sc_asns)
    node_type = random.choice(["vpn_proxy", "tor_exit_node", "bulletproof_host", "datacenter"])

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
        "relay_ip": ip_choice,
        "node_type": node_type,
        "asn": asn_choice["asn"],
        "isp": asn_choice["isp"],
        "country_code": asn_choice["country"],
        "_source": "planted_layering",
    })

    # 2. INTERMEDIARY HOPS (Pass-throughs / multi-tier criss-cross)
    # Some intermediaries pass through directly, some split further
    active_wallets = list(zip(intermediate_wallets, out_amts))
    next_stage_wallets = []

    stage1_duration = total_duration_hrs * 0.4
    intermediate_offsets_s = np.sort(rng.uniform(300.0, stage1_duration * 3600.0, size=n_fanout))

    for idx, (iw, ia) in enumerate(active_wallets):
        # 60% chance of intermediary pass-through or sub-split hop
        if random.random() < 0.65:
            txid_counter += 1
            fee_hop = sample_fee()
            hop_amt = round(ia - fee_hop, 8)
            if hop_amt <= 1e-6:
                next_stage_wallets.append((iw, ia))
                continue

            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(intermediate_offsets_s[idx]))

            # Sub-split or single pass-through
            if random.random() < 0.35:
                # Sub-split into 2 intermediate wallets
                w1 = gen_unique_wallet(all_wallets)
                w2 = gen_unique_wallet(all_wallets)
                parts = distribute_amount(hop_amt, 2)
                hop_out_addrs = [w1, w2]
                hop_out_amts = parts
                next_stage_wallets.append((w1, parts[0]))
                next_stage_wallets.append((w2, parts[1]))
            else:
                w1 = gen_unique_wallet(all_wallets)
                hop_out_addrs = [w1]
                hop_out_amts = [hop_amt]
                next_stage_wallets.append((w1, hop_amt))

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

    # 3. FAN-IN CONSOLIDATION (Consolidate into 1 or 2 collectors)
    n_collectors = 1 if random.random() < 0.75 else 2
    collector_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_collectors)]

    # Group next_stage_wallets for consolidation
    # If too many inputs for single txn (max 8), chunk them
    chunk_size = 6
    fanin_chunks = [next_stage_wallets[i:i + chunk_size] for i in range(0, len(next_stage_wallets), chunk_size)]

    fanin_ts_base = sc_base_ts + pd.Timedelta(hours=total_duration_hrs * 0.8)

    for c_idx, chunk in enumerate(fanin_chunks):
        txid_counter += 1
        fee_in = sample_fee()
        chunk_in_addrs = [w for w, _ in chunk]
        chunk_in_amts = [a for _, a in chunk]
        chunk_total_in = round(sum(chunk_in_amts), 8)
        chunk_total_out = round(chunk_total_in - fee_in, 8)
        if chunk_total_out <= 1e-6:
            chunk_total_out = 1e-6

        chunk_out_addrs = collector_wallets if n_collectors <= len(collector_wallets) else [collector_wallets[0]]
        chunk_out_amts = distribute_amount(chunk_total_out, len(chunk_out_addrs))

        fanin_ts = fanin_ts_base + pd.Timedelta(minutes=(c_idx + 1) * 30)

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

    # Structural diversity:
    # 1. Rounds: 2 to 7 rounds
    n_rounds = int(rng.integers(2, 8))
    # 2. Participants: 3 to 7 participants
    n_participants = int(rng.integers(3, 8))

    # Pacing: quick CoinJoin (1 to 6 hrs), scheduled mix (6 to 36 hrs), slow batch mix (36 to 200 hrs)
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

    # Participants bring their own IPs (3 to 6 IPs across 2-3 ASNs)
    n_ips = min(n_participants, random.randint(3, 5))
    sc_asns = rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 23 + i) for i in range(n_ips)]

    # Denomination type:
    # 70% standard equal output denomination (classic CoinJoin)
    # 30% tiered or change-output CoinJoin
    has_change = (random.random() < 0.30)

    # Initial participant wallets
    participant_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
    base_denom = round(float(rng.lognormal(-0.8, 0.9)), 8)
    base_denom = max(base_denom, 0.02)

    current_in_wallets = participant_wallets
    current_amount_per_p = base_denom

    # Pre-mix split (Tx0): 1 or 2 participants split unequal deposit into standard mix denomination
    n_premix = random.randint(1, 2)
    for p_idx in range(n_premix):
        txid_counter += 1
        fee_pre = sample_fee()
        raw_deposit = round(base_denom * 1.35 + fee_pre, 8)
        pre_in_wallet = gen_unique_wallet(all_wallets)
        pre_change = gen_unique_wallet(all_wallets)
        
        pre_ts = sc_base_ts - pd.Timedelta(minutes=random.randint(10, 120))
        mixing_records.append({
            "txid_counter": txid_counter,
            "timestamp": pre_ts,
            "input_addresses": json.dumps([pre_in_wallet]),
            "output_addresses": json.dumps([participant_wallets[p_idx], pre_change]),
            "input_amounts": json.dumps([raw_deposit]),
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

    # CoinJoin Rounds
    for rnd in range(n_rounds):
        txid_counter += 1
        fee = sample_fee()
        round_ts = sc_base_ts + pd.Timedelta(seconds=float(round_offsets_s[rnd]))

        total_in = round(current_amount_per_p * n_participants, 8)
        total_out = round(total_in - fee, 8)
        out_per_p = round(total_out / n_participants, 8)

        new_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]

        if has_change and rnd == 0:
            # First round includes change outputs
            change_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
            # Equal denomination outputs + small change
            denom_amt = round(out_per_p * 0.85, 8)
            change_amt = round((total_out - (denom_amt * n_participants)) / n_participants, 8)
            out_addrs = new_wallets + change_wallets
            out_amts = [denom_amt] * n_participants + [change_amt] * n_participants
            # Fix residual
            residual = round(total_in - sum(out_amts) - fee, 8)
            out_amts[-1] = round(out_amts[-1] + residual, 8)
            current_amount_per_p = denom_amt
        else:
            out_addrs = new_wallets
            out_amts = [out_per_p] * n_participants
            residual = round(total_in - sum(out_amts) - fee, 8)
            out_amts[-1] = round(out_amts[-1] + residual, 8)
            current_amount_per_p = out_per_p

        in_addrs = current_in_wallets.copy()
        in_amts = distribute_amount(round(total_in, 8), n_participants)

        # Network assignment: Coordinator / peer relay
        ip_choice = random.choice(sc_ips)
        asn_choice = random.choice(sc_asns)
        node_type = random.choice(["tor_exit_node", "vpn_proxy", "residential", "datacenter"])

        mixing_records.append({
            "txid_counter": txid_counter,
            "timestamp": round_ts,
            "input_addresses": json.dumps(in_addrs),
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

    # Post-mix consolidation / payout: 1 or 2 participants transfer mixed funds to cold storage
    n_postmix = random.randint(1, 2)
    for p_idx in range(n_postmix):
        txid_counter += 1
        fee_post = sample_fee()
        post_in_amt = round(current_amount_per_p, 8)
        post_out_amt = round(post_in_amt - fee_post, 8)
        if post_out_amt > 1e-6:
            cold_wallet = gen_unique_wallet(all_wallets)
            post_ts = round_ts + pd.Timedelta(minutes=random.randint(15, 180))
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
