"""
generate_v5.py
==============
SIH 2026 — Bitcoin AML Dataset v5.0 Generation Pipeline

V5 Key Improvements over V4 (targeted at specific downstream feature shortcuts):
  1. HARMONIZED input/output count distributions:
     - All typologies + licit share a BROAD overlapping pool of n_inputs/n_outputs
       distributions, with per-typology weights that create real but subtle
       distributional differences (not deterministic separation).
     - This directly affects: mean_num_inputs, mean_num_outputs, io_count_ratio,
       fanin_ratio, fanout_ratio, edge_to_node_ratio.
  2. CATEGORICAL OVERLAP fix:
     - Licit scenarios now include bulletproof_host (rare but present, ~3-5%).
     - Illicit scenarios use mobile infrastructure more (15-25%).
     - This fixes Gate H (node_type overlap) from V4's 83.3% to >90%.
  3. ADDRESS REUSE DECOUPLING:
     - Both licit and illicit scenarios sample from overlapping address reuse
       strategies (some high-reuse, some low-reuse in both classes).
     - This breaks the address_reuse_ratio single-feature shortcut.
  4. STRUCTURAL DIVERSITY within typologies:
     - Each typology has 4-5 archetypes with genuinely different structural
       signatures, creating within-class variance that prevents rigid templating.
  5. FULLY STANDALONE:
     - Does not depend on external Elliptic/BitcoinHeist CSVs.
     - Generates all data synthetically with realistic calibration.

Usage:
    conda activate ml
    python data_pipeline/generate_v5.py
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
SEED = 2026_02  # V5.1 attempt 2
SPLIT_RATIO = 0.2  # 20% test

# Scenario counts — calibrated to produce ~80k total rows
N_LICIT_SCENARIOS    = 3200   # Includes ~40 exchange hard-negatives
N_RANSOMWARE_TARGET  = 28000  # Total ransomware transactions
N_PEELING_SCENARIOS  = 260
N_LAYERING_SCENARIOS = 260
N_MIXING_SCENARIOS   = 320
N_EXCHANGE_WALLETS   = 40

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    length = random.randint(25, 33)
    return "1" + "".join(random.choices(BASE58_ALPHABET, k=length))

def gen_unique_wallet(existing: set) -> str:
    while True:
        w = gen_wallet()
        if w not in existing:
            existing.add(w)
            return w

def make_txid(counter: int, salt: str = "sih2026v5") -> int:
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
    if n == 1:
        return [round(total, 8)]
    fracs = rng.dirichlet(np.ones(n))
    parts = [round(total * float(f), 8) for f in fracs]
    residual = round(total - sum(parts[:-1]), 8)
    if residual <= 0:
        parts[0] = round(parts[0] + residual - 1e-8, 8)
        residual = 1e-8
    parts[-1] = max(residual, 1e-8)
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

def fix_accounting(in_amts, out_amts, fee):
    """Ensure exact accounting: sum(in) = sum(out) + fee."""
    res = round(sum(in_amts) - sum(out_amts) - fee, 8)
    if res != 0:
        out_amts[-1] = round(out_amts[-1] + res, 8)
    return out_amts

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED INPUT/OUTPUT COUNT SAMPLERS
# ═══════════════════════════════════════════════════════════════════════════════
# V5.2: Overlapping distributions for I/O counts, but without extreme noise.
# The real structural confusion happens at the MACRO level in the phases below.

def sample_n_inputs(context: str = "default") -> int:
    if context == "licit_normal":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.40, 0.28, 0.16, 0.08, 0.05, 0.03]))
    elif context == "licit_exchange":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.25, 0.25, 0.18, 0.10, 0.07]))
    elif context == "ransomware":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.35, 0.25, 0.18, 0.12, 0.06, 0.04]))
    elif context == "peeling":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.40, 0.25, 0.16, 0.10, 0.05, 0.04]))
    elif context == "layering":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.30, 0.25, 0.20, 0.13, 0.07, 0.05]))
    elif context == "mixing":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.20, 0.22, 0.22, 0.18, 0.10, 0.08]))
    else:
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.30, 0.26, 0.19, 0.12, 0.08, 0.05]))

def sample_n_outputs(context: str = "default") -> int:
    if context == "licit_normal":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.22, 0.30, 0.20, 0.14, 0.08, 0.06]))
    elif context == "licit_exchange":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.10, 0.20, 0.25, 0.22, 0.13, 0.10]))
    elif context == "ransomware":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.22, 0.28, 0.22, 0.14, 0.08, 0.06]))
    elif context == "peeling":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.18, 0.30, 0.24, 0.14, 0.08, 0.06]))
    elif context == "layering":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.22, 0.24, 0.18, 0.12, 0.09]))
    elif context == "mixing":
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.12, 0.18, 0.22, 0.20, 0.15, 0.13]))
    else:
        return int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.18, 0.26, 0.23, 0.16, 0.10, 0.07]))


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED NODE_TYPE SAMPLER (V5.2: Overlapping distributions for Gate B)
# ═══════════════════════════════════════════════════════════════════════════════
ALL_NODE_TYPES = ["residential", "datacenter", "vpn_proxy", "tor_exit_node", "bulletproof_host", "mobile"]

def sample_node_type(context: str = "default") -> str:
    """All node types available to BOTH licit and illicit with MUCH closer weights.
    V5.2: Narrowed the gap so suspicious_infra_ratio distributions overlap substantially.
    Licit: ~35% suspicious (vpn+tor+bp), Illicit: ~42% suspicious.
    """
    if context == "licit":
        # suspicious = vpn_proxy(0.15) + tor_exit_node(0.12) + bulletproof_host(0.05) = 0.32
        return str(rng.choice(ALL_NODE_TYPES,
            p=[0.28, 0.22, 0.15, 0.12, 0.05, 0.18]))
    elif context == "illicit":
        # suspicious = vpn_proxy(0.16) + tor_exit_node(0.14) + bulletproof_host(0.10) = 0.40
        return str(rng.choice(ALL_NODE_TYPES,
            p=[0.25, 0.18, 0.16, 0.14, 0.10, 0.17]))
    else:
        return str(rng.choice(ALL_NODE_TYPES,
            p=[0.26, 0.20, 0.16, 0.13, 0.08, 0.17]))

# ═══════════════════════════════════════════════════════════════════════════════
# ADDRESS REUSE STRATEGY SAMPLER
# ═══════════════════════════════════════════════════════════════════════════════

def get_address_reuse_prob(context: str = "default") -> float:
    """
    Sample an address reuse probability for a SCENARIO.
    V5.2: Licit and illicit draw from IDENTICAL distributions to eliminate address_reuse_ratio shortcut.
    """
    return float(rng.choice([0.0, 0.05, 0.10, 0.20, 0.35, 0.50],
        p=[0.15, 0.20, 0.25, 0.20, 0.12, 0.08]))


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL NETWORK METADATA REGISTRY (same as V4)
# ═══════════════════════════════════════════════════════════════════════════════
GLOBAL_ASNS = [
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
    {"asn": "AS16509", "isp": "Amazon.com, Inc.",             "country": "US", "infra": "datacenter"},
    {"asn": "AS15169", "isp": "Google LLC",                  "country": "US", "infra": "datacenter"},
    {"asn": "AS13335", "isp": "Cloudflare, Inc.",             "country": "US", "infra": "datacenter"},
    {"asn": "AS24940", "isp": "Hetzner Online GmbH",          "country": "DE", "infra": "datacenter"},
    {"asn": "AS16276", "isp": "OVH SAS",                     "country": "FR", "infra": "datacenter"},
    {"asn": "AS60781", "isp": "Leaseweb Netherlands B.V.",    "country": "NL", "infra": "datacenter"},
    {"asn": "AS45102", "isp": "Alibaba Cloud LLC",            "country": "SG", "infra": "datacenter"},
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
    "/Satoshi:22.0.0/", "/Satoshi:21.1.0/",
    "/Satoshi:0.20.1/", "/btcd:0.22.0/",
]
USER_AGENT_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

def gen_ipv4_for_asn(asn_seed: int) -> str:
    p1 = 12 + (asn_seed * 19) % 180
    p2 = 10 + (asn_seed * 37) % 230
    p3 = random.randint(1, 254)
    p4 = random.randint(1, 254)
    return f"{p1}.{p2}.{p3}.{p4}"


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC TRANSACTION BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

all_wallets = set()
txid_counter = 0

def make_tx_record(
    in_addrs, in_amts, out_addrs, out_amts, fee,
    timestamp, is_illicit, pattern_type, scenario_id,
    node_type_ctx, sc_ips, sc_asns, source_tag
):
    """Build a single transaction record with accounting guarantee."""
    global txid_counter
    txid_counter += 1

    # Fix accounting
    out_amts = fix_accounting(in_amts, out_amts, fee)

    ip_choice = random.choice(sc_ips)
    asn_choice = random.choice(sc_asns) if isinstance(sc_asns[0], dict) else sc_asns[random.randint(0, len(sc_asns)-1)]

    return {
        "txid_counter": txid_counter,
        "timestamp": timestamp,
        "input_addresses": json.dumps(in_addrs),
        "output_addresses": json.dumps(out_addrs),
        "input_amounts": json.dumps(in_amts),
        "output_amounts": json.dumps(out_amts),
        "fee_btc": fee,
        "script_type": sample_script_type(),
        "is_illicit": is_illicit,
        "pattern_type": pattern_type,
        "scenario_id": scenario_id,
        "relay_ip": ip_choice,
        "node_type": sample_node_type(node_type_ctx),
        "asn": asn_choice["asn"] if isinstance(asn_choice, dict) else asn_choice,
        "isp": asn_choice["isp"] if isinstance(asn_choice, dict) else "Unknown ISP",
        "country_code": asn_choice["country"] if isinstance(asn_choice, dict) else "US",
        "_source": source_tag,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: LICIT (NORMAL) SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 1 — Generating Licit (Normal) scenarios")
print("=" * 70)

licit_records = []
# Target total: ~48k licit rows (excluding exchange)
licit_target_rows = 42000

scenario_num = 0
while len(licit_records) < licit_target_rows:
    scenario_num += 1
    sc_id = f"licit_{scenario_num:05d}"

    # Scenario archetype (same as V4 but with broader structural variation)
    archetype = rng.choice([1, 2, 3, 4, 5], p=[0.35, 0.35, 0.18, 0.09, 0.03])
    if archetype == 1:
        sc_size = int(rng.integers(1, 4))
        target_dur_hrs = float(rng.uniform(0.08, 4.0))
    elif archetype == 2:
        sc_size = int(rng.integers(4, 11))
        target_dur_hrs = float(rng.uniform(2.0, 48.0))
    elif archetype == 3:
        sc_size = int(rng.integers(11, 26))
        target_dur_hrs = float(rng.uniform(48.0, 336.0))
    elif archetype == 4:
        sc_size = int(rng.integers(26, 61))
        target_dur_hrs = float(rng.uniform(168.0, 1080.0))
    else:
        sc_size = int(rng.integers(61, 151))
        target_dur_hrs = float(rng.uniform(336.0, 2160.0))

    remaining = licit_target_rows - len(licit_records)
    sc_size = min(sc_size, remaining)
    if sc_size <= 0:
        break

    sc_base_ts = random_timestamp_in_range(2012, 2018)
    if sc_size == 1:
        time_offsets_s = [0.0]
    else:
        raw_offsets = rng.uniform(0, target_dur_hrs * 3600.0, size=sc_size)
        raw_offsets.sort()
        raw_offsets[0] = 0.0
        time_offsets_s = raw_offsets.tolist()

    # Scenario network pool
    n_ips = 1 if sc_size <= 2 else (2 if sc_size <= 10 else random.randint(2, 4))
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True))
    sc_ips = [gen_ipv4_for_asn(scenario_num * 3 + i) for i in range(n_ips)]

    # V5: Address reuse probability for this scenario (overlapping with illicit)
    addr_reuse_p = get_address_reuse_prob("licit")
    sc_internal_wallets = [gen_unique_wallet(all_wallets) for _ in range(max(2, sc_size // 3))]

    for t in range(sc_size):
        fee = sample_fee()
        tx_ts = sc_base_ts + pd.Timedelta(seconds=time_offsets_s[t])

        # V5: Use shared input/output sampler
        n_in = sample_n_inputs("licit_normal")
        n_out = sample_n_outputs("licit_normal")

        # Wallets with V5 overlapping reuse strategy
        input_addrs = []
        for j in range(n_in):
            if random.random() < addr_reuse_p and sc_internal_wallets:
                input_addrs.append(random.choice(sc_internal_wallets))
            else:
                input_addrs.append(gen_unique_wallet(all_wallets))

        total_amount = sample_amount()
        input_total = round(total_amount + fee, 8)
        input_amounts = distribute_amount(input_total, n_in)
        output_amounts = distribute_amount(total_amount, n_out)

        output_addrs = []
        for k in range(n_out):
            if random.random() < addr_reuse_p * 0.5 and sc_internal_wallets:
                output_addrs.append(random.choice(sc_internal_wallets))
            else:
                output_addrs.append(gen_unique_wallet(all_wallets))

        licit_records.append(make_tx_record(
            input_addrs, input_amounts, output_addrs, output_amounts, fee,
            tx_ts, 0, "normal", sc_id, "licit", sc_ips, sc_asns_list,
            "licit_normal"
        ))

n_licit_scenarios = scenario_num
print(f"  Generated {len(licit_records):,} licit transactions across {n_licit_scenarios:,} scenarios")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: HARD-NEGATIVE EXCHANGE WALLETS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 2 — Hard-Negative Exchange Scenarios")
print("=" * 70)

exchange_records = []
for ex_idx in range(N_EXCHANGE_WALLETS):
    sc_id = f"exchange_{ex_idx + 1:03d}"
    ex_wallet = gen_unique_wallet(all_wallets)
    n_txns = random.randint(60, 260)

    op_days = float(rng.uniform(2.0, 30.0))
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    time_offsets_s = np.sort(rng.uniform(0, op_days * 86400.0, size=n_txns))
    time_offsets_s[0] = 0.0

    ex_asns = list(rng.choice([a for a in GLOBAL_ASNS if a["country"] in ["US", "DE", "JP", "FR", "NL", "SG"]], size=2))
    ex_ips = [gen_ipv4_for_asn(ex_idx * 10 + i) for i in range(3)]

    for t in range(n_txns):
        fee = sample_fee()
        tx_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[t]))

        if random.random() < 0.6:
            # Fan-out withdrawal
            n_out = sample_n_outputs("licit_exchange")
            total_amount = sample_amount() * float(rng.uniform(2.0, 6.0))
            out_amounts = distribute_amount(round(total_amount, 8), n_out)
            in_amount = round(total_amount + fee, 8)
            in_addrs = [ex_wallet]
            in_amounts = [in_amount]
            out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
        else:
            # Fan-in deposit
            n_in = sample_n_inputs("licit_exchange")
            total_amount = sample_amount() * float(rng.uniform(1.5, 4.0))
            in_amounts = distribute_amount(round(total_amount + fee, 8), n_in)
            out_amount = round(total_amount, 8)
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
            out_addrs = [ex_wallet]
            out_amounts = [out_amount]

        exchange_records.append(make_tx_record(
            in_addrs, in_amounts, out_addrs, out_amounts, fee,
            tx_ts, 0, "normal", sc_id, "licit", ex_ips, ex_asns,
            "hard_negative_exchange"
        ))

print(f"  Generated {len(exchange_records):,} exchange transactions across {N_EXCHANGE_WALLETS} exchanges")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: RANSOMWARE CAMPAIGNS (MACRO-STRUCTURAL HYBRIDS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 3 — Ransomware Campaigns (Macro-Structural Hybrids)")
print("=" * 70)

ransom_records = []
ransom_sc_counter = 0

while len(ransom_records) < N_RANSOMWARE_TARGET:
    ransom_sc_counter += 1
    sc_id = f"ransom_{ransom_sc_counter:04d}"

    scale_arch = rng.choice([1, 2, 3, 4], p=[0.30, 0.40, 0.22, 0.08])
    if scale_arch == 1:
        camp_size = int(rng.integers(2, 5))
        camp_dur_hrs = float(rng.uniform(0.1, 8.0))
    elif scale_arch == 2:
        camp_size = int(rng.integers(5, 16))
        camp_dur_hrs = float(rng.uniform(4.0, 72.0))
    elif scale_arch == 3:
        camp_size = int(rng.integers(16, 36))
        camp_dur_hrs = float(rng.uniform(48.0, 360.0))
    else:
        camp_size = int(rng.integers(36, 76))
        camp_dur_hrs = float(rng.uniform(120.0, 800.0))

    remaining_r = N_RANSOMWARE_TARGET - len(ransom_records)
    camp_size = min(camp_size, remaining_r)

    sc_base_ts = random_timestamp_in_range(2013, 2018)
    offsets_s = np.sort(rng.uniform(0, camp_dur_hrs * 3600.0, size=camp_size))
    offsets_s[0] = 0.0

    n_ips = 1 if camp_size <= 2 else random.randint(2, min(5, camp_size))
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True))
    sc_ips = [gen_ipv4_for_asn(ransom_sc_counter * 7 + i) for i in range(n_ips)]

    addr_reuse_p = get_address_reuse_prob("illicit")
    primary_syndicate = gen_unique_wallet(all_wallets)

    # V5.2: MACRO-STRUCTURAL ARCHETYPES
    op_arch = rng.choice(["classic_star", "layered_fanout", "peeling_consolidation"], p=[0.50, 0.25, 0.25])

    if op_arch == "classic_star":
        # Classic: Victims send to primary, primary occasionally cashes out
        for t in range(camp_size):
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            if random.random() < 0.8: # Victim pays
                n_in = sample_n_inputs("ransomware")
                in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
                total_amt = sample_amount()
                in_amts = distribute_amount(round(total_amt + fee, 8), n_in)
                out_addrs = [primary_syndicate]
                out_amts = [total_amt]
            else: # Cash out
                in_addrs = [primary_syndicate]
                total_amt = sample_amount() * 3
                in_amts = [round(total_amt + fee, 8)]
                n_out = sample_n_outputs("ransomware")
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                out_amts = distribute_amount(total_amt, n_out)

            ransom_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))

    elif op_arch == "layered_fanout":
        # Layered: Victim pays large sum to primary, primary fans it out to multiple intermediaries (layering-like)
        victims_paid = 0
        for t in range(camp_size):
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            if t % 3 == 0: # Victim pays large amount
                in_addrs = [gen_unique_wallet(all_wallets)]
                total_amt = sample_amount() * 5
                in_amts = [round(total_amt + fee, 8)]
                out_addrs = [primary_syndicate]
                out_amts = [total_amt]
                victims_paid += 1
            else: # Primary fans out the money to 5-10 nodes
                in_addrs = [primary_syndicate]
                total_amt = sample_amount() * 4
                in_amts = [round(total_amt + fee, 8)]
                n_out = random.randint(5, 12) # High fanout
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                out_amts = distribute_amount(total_amt, n_out)

            ransom_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))

    elif op_arch == "peeling_consolidation":
        # Peeling: Victims pay unique wallets, operator sweeps them via a chain (peeling-like)
        victim_wallets = []
        for t in range(camp_size // 2 + 1):
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            vw = gen_unique_wallet(all_wallets)
            victim_wallets.append(vw)
            in_addrs = [gen_unique_wallet(all_wallets)]
            total_amt = sample_amount()
            in_amts = [round(total_amt + fee, 8)]
            out_addrs = [vw]
            out_amts = [total_amt]
            ransom_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))
        
        # Now sweep them in a chain (peeling)
        chain_wallet = gen_unique_wallet(all_wallets)
        for i, vw in enumerate(victim_wallets):
            t = (camp_size // 2 + 1) + i
            if t >= camp_size: break
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            in_addrs = [vw] if i == 0 else [chain_wallet, vw]
            total_amt = sample_amount() * 2
            in_amts = distribute_amount(round(total_amt + fee, 8), len(in_addrs))
            next_chain = gen_unique_wallet(all_wallets)
            out_addrs = [next_chain]
            out_amts = [total_amt]
            chain_wallet = next_chain
            ransom_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))

print(f"  Generated {len(ransom_records):,} ransomware txns across {ransom_sc_counter:,} campaigns")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: PEELING CHAINS (MACRO-STRUCTURAL HYBRIDS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 4 — {N_PEELING_SCENARIOS} Structurally Diverse Peeling Chains")
print("=" * 70)

peeling_records = []
for sc_idx in range(N_PEELING_SCENARIOS):
    sc_id = f"peel_{sc_idx + 1:04d}"
    
    n_hops = int(rng.integers(5, 25))
    total_dur_hrs = float(rng.uniform(2.0, 150.0))
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    time_offsets_s = np.sort(rng.uniform(0, total_dur_hrs * 3600.0, size=n_hops))
    time_offsets_s[0] = 0.0

    n_ips = random.randint(1, 3)
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True))
    sc_ips = [gen_ipv4_for_asn(sc_idx * 13 + i) for i in range(n_ips)]
    addr_reuse_p = get_address_reuse_prob("illicit")

    initial_amount = max(round(float(rng.lognormal(0.5, 1.2)), 8), 0.1)
    
    # V5.2: MACRO-STRUCTURAL ARCHETYPES
    op_arch = rng.choice(["classic_peel", "branching_peel"], p=[0.70, 0.30])
    
    current_wallet = gen_unique_wallet(all_wallets)
    remaining = initial_amount

    if op_arch == "classic_peel":
        for hop in range(n_hops):
            fee = sample_fee()
            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))
            in_addrs = [current_wallet]
            in_amts = [remaining]
            
            n_out = sample_n_outputs("peeling")
            if n_out == 1: n_out = 2
            
            peel_total = 0
            out_addrs = []
            out_amts = []
            for k in range(n_out - 1):
                peel_amt = round(remaining * float(rng.uniform(0.02, 0.15)), 8)
                peel_total += peel_amt
                out_addrs.append(gen_unique_wallet(all_wallets))
                out_amts.append(peel_amt)
                
            pass_amt = round(remaining - peel_total - fee, 8)
            if pass_amt <= 1e-6: break
            
            next_w = gen_unique_wallet(all_wallets) if random.random() > addr_reuse_p else current_wallet
            out_addrs.append(next_w)
            out_amts.append(pass_amt)
            
            peeling_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                hop_ts, 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peeling_chain"
            ))
            current_wallet = next_w
            remaining = pass_amt
            
    elif op_arch == "branching_peel":
        # At each hop, the peeled amounts also form mini-chains (layering-like branching)
        active_chains = [(current_wallet, remaining)]
        for hop in range(n_hops):
            if not active_chains: break
            fee = sample_fee()
            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))
            
            cw, cramt = active_chains.pop(0)
            in_addrs = [cw]
            in_amts = [cramt]
            
            n_out = random.randint(3, 6) # High fanout for branching
            out_addrs = []
            out_amts = []
            for k in range(n_out):
                out_addrs.append(gen_unique_wallet(all_wallets))
            
            out_amts = distribute_amount(round(cramt - fee, 8), n_out)
            
            peeling_records.append(make_tx_record(
                in_addrs, in_amts, out_addrs, out_amts, fee,
                hop_ts, 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peeling_chain"
            ))
            
            # Keep the 2 largest outputs to continue as chains
            largest = sorted(zip(out_addrs, out_amts), key=lambda x: x[1], reverse=True)
            active_chains.extend(largest[:2])

print(f"  Planted {len(peeling_records):,} peeling txns across {N_PEELING_SCENARIOS} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: LAYERING CLUSTERS (MACRO-STRUCTURAL HYBRIDS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 5 — {N_LAYERING_SCENARIOS} Structurally Diverse Layering Clusters")
print("=" * 70)

layering_records = []
for sc_idx in range(N_LAYERING_SCENARIOS):
    sc_id = f"layer_{sc_idx + 1:04d}"

    op_arch = rng.choice(["classic_layer", "deep_layer", "dense_layer"], p=[0.50, 0.30, 0.20])

    total_dur_hrs = float(rng.uniform(8.0, 150.0))
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    n_ips = random.randint(2, 4)
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True))
    sc_ips = [gen_ipv4_for_asn(sc_idx * 17 + i) for i in range(n_ips)]
    
    total_amount = max(round(float(rng.lognormal(0.5, 1.4)), 8), 0.15)
    
    if op_arch == "classic_layer":
        # 1. Fan out
        n_fanout = random.randint(5, 15)
        fee1 = sample_fee()
        in_addrs = [gen_unique_wallet(all_wallets)]
        in_amts = [round(total_amount + fee1, 8)]
        intermediate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
        out_amts = distribute_amount(total_amount, n_fanout)
        layering_records.append(make_tx_record(
            in_addrs, in_amts, intermediate_wallets, out_amts, fee1,
            sc_base_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
        ))
        # 2. Hops
        next_stage_wallets = []
        for idx, (iw, ia) in enumerate(zip(intermediate_wallets, out_amts)):
            fee_hop = sample_fee()
            hop_amt = round(ia - fee_hop, 8)
            if hop_amt > 1e-6:
                nw = gen_unique_wallet(all_wallets)
                next_stage_wallets.append((nw, hop_amt))
                hop_ts = sc_base_ts + pd.Timedelta(minutes=random.randint(60, 600))
                layering_records.append(make_tx_record(
                    [iw], [ia], [nw], [hop_amt], fee_hop,
                    hop_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
                ))
        # 3. Fan in
        if next_stage_wallets:
            fee_in = sample_fee()
            chunk_in_addrs = [w for w, _ in next_stage_wallets]
            chunk_in_amts = [a for _, a in next_stage_wallets]
            tot_out = round(sum(chunk_in_amts) - fee_in, 8)
            if tot_out > 1e-6:
                fanin_ts = sc_base_ts + pd.Timedelta(hours=total_dur_hrs * 0.9)
                layering_records.append(make_tx_record(
                    chunk_in_addrs, chunk_in_amts, [gen_unique_wallet(all_wallets)], [tot_out], fee_in,
                    fanin_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
                ))
                
    elif op_arch == "deep_layer":
        # Peeling-like layering: Fan out to 3, then each does a chain of 5-10
        n_fanout = 3
        fee1 = sample_fee()
        in_addrs = [gen_unique_wallet(all_wallets)]
        in_amts = [round(total_amount + fee1, 8)]
        branch_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
        branch_amts = distribute_amount(total_amount, n_fanout)
        layering_records.append(make_tx_record(
            in_addrs, in_amts, branch_wallets, branch_amts, fee1,
            sc_base_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
        ))
        for bw, bamt in zip(branch_wallets, branch_amts):
            cw, camt = bw, bamt
            for hop in range(random.randint(5, 10)):
                fee = sample_fee()
                if camt - fee <= 1e-6: break
                nw = gen_unique_wallet(all_wallets)
                hop_ts = sc_base_ts + pd.Timedelta(minutes=random.randint(60, 600) * (hop+1))
                layering_records.append(make_tx_record(
                    [cw], [camt], [nw], [round(camt - fee, 8)], fee,
                    hop_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
                ))
                cw, camt = nw, round(camt - fee, 8)
                
    elif op_arch == "dense_layer":
        # Mixing-like layering: Dense inter-transfers
        nodes = [gen_unique_wallet(all_wallets) for _ in range(5)]
        balances = {w: 0.0 for w in nodes}
        balances[nodes[0]] = total_amount
        for hop in range(15):
            valid_senders = [n for n in nodes if balances[n] > 0.05]
            if not valid_senders: break
            sender = random.choice(valid_senders)
            receivers = random.sample([n for n in nodes if n != sender], 2)
            fee = sample_fee()
            amt_to_send = round(balances[sender] * float(rng.uniform(0.3, 0.8)), 8)
            if amt_to_send - fee <= 1e-6: continue
            balances[sender] = round(balances[sender] - amt_to_send, 8)
            out_amts = distribute_amount(round(amt_to_send - fee, 8), 2)
            for r, a in zip(receivers, out_amts): balances[r] = round(balances[r] + a, 8)
            hop_ts = sc_base_ts + pd.Timedelta(minutes=random.randint(60, 600) * (hop+1))
            layering_records.append(make_tx_record(
                [sender], [amt_to_send], receivers, out_amts, fee,
                hop_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
            ))

print(f"  Planted {len(layering_records):,} layering txns across {N_LAYERING_SCENARIOS} scenarios")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: MIXING CLUSTERS (MACRO-STRUCTURAL HYBRIDS)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"PHASE 6 — {N_MIXING_SCENARIOS} Structurally Diverse Mixing Clusters")
print("=" * 70)

mixing_records = []
for sc_idx in range(N_MIXING_SCENARIOS):
    sc_id = f"mix_{sc_idx + 1:04d}"
    
    op_arch = rng.choice(["classic_mix", "sequential_mix", "self_mix"], p=[0.50, 0.25, 0.25])
    
    total_dur_hrs = float(rng.uniform(6.0, 100.0))
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    n_ips = random.randint(3, 5)
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 3), replace=True))
    sc_ips = [gen_ipv4_for_asn(sc_idx * 23 + i) for i in range(n_ips)]
    
    base_denom = max(round(float(rng.lognormal(-0.8, 0.9)), 8), 0.05)
    
    if op_arch == "classic_mix":
        # Classic CoinJoin: N participants, M rounds
        n_p = random.randint(3, 8)
        n_rounds = random.randint(2, 5)
        current_in = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        for rnd in range(n_rounds):
            fee = sample_fee()
            round_ts = sc_base_ts + pd.Timedelta(hours=rnd * 2)
            in_amts = [base_denom] * n_p
            tot_in = round(sum(in_amts), 8)
            tot_out = round(tot_in - fee, 8)
            new_out = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
            out_amts = [round(tot_out / n_p, 8)] * n_p
            mixing_records.append(make_tx_record(
                current_in, in_amts, new_out, out_amts, fee,
                round_ts, 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
            ))
            current_in = new_out
            base_denom = round(tot_out / n_p, 8)
            
    elif op_arch == "sequential_mix":
        # Peeling-like mixing: 2 participants, many rounds (looks like a 2-chain)
        n_p = 2
        n_rounds = random.randint(6, 12)
        current_in = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        for rnd in range(n_rounds):
            fee = sample_fee()
            round_ts = sc_base_ts + pd.Timedelta(hours=rnd * 2)
            in_amts = [base_denom] * n_p
            tot_in = round(sum(in_amts), 8)
            tot_out = round(tot_in - fee, 8)
            new_out = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
            out_amts = [round(tot_out / n_p, 8)] * n_p
            mixing_records.append(make_tx_record(
                current_in, in_amts, new_out, out_amts, fee,
                round_ts, 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
            ))
            current_in = new_out
            base_denom = round(tot_out / n_p, 8)
            
    elif op_arch == "self_mix":
        # Layering-like mixing: 1 participant splits into 5, mixes, consolidates
        w_start = gen_unique_wallet(all_wallets)
        fee1 = sample_fee()
        n_split = 5
        tot_start = round(base_denom * n_split + fee1, 8)
        splits = [gen_unique_wallet(all_wallets) for _ in range(n_split)]
        mixing_records.append(make_tx_record(
            [w_start], [tot_start], splits, [base_denom]*n_split, fee1,
            sc_base_ts, 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
        ))
        
        # 1 mix round
        fee2 = sample_fee()
        mix_out = [gen_unique_wallet(all_wallets) for _ in range(n_split)]
        tot_out = round((base_denom * n_split) - fee2, 8)
        out_amts = distribute_amount(tot_out, n_split)
        mixing_records.append(make_tx_record(
            splits, [base_denom]*n_split, mix_out, out_amts, fee2,
            sc_base_ts + pd.Timedelta(hours=2), 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
        ))
        
        # Consolidate
        fee3 = sample_fee()
        w_end = gen_unique_wallet(all_wallets)
        mixing_records.append(make_tx_record(
            mix_out, out_amts, [w_end], [round(tot_out - fee3, 8)], fee3,
            sc_base_ts + pd.Timedelta(hours=4), 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
        ))

print(f"  Planted {len(mixing_records):,} mixing txns across {N_MIXING_SCENARIOS} scenarios")


# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6B: LICIT STRUCTURAL EQUIVALENTS (To break structural separability)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 6B — Licit Structural Equivalents")
print("=" * 70)

# 1. Licit Peeling (Exchange UTXO Consolidation)
for sc_idx in range(400):
    sc_id = f"licit_peel_{sc_idx:04d}"
    n_hops = random.randint(5, 20)
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    time_offsets_s = np.sort(rng.uniform(0, 50.0 * 3600.0, size=n_hops))
    time_offsets_s[0] = 0.0
    sc_ips = [gen_ipv4_for_asn(sc_idx * 11 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    current_wallet = gen_unique_wallet(all_wallets)
    remaining = max(round(float(rng.lognormal(1.0, 1.2)), 8), 0.5)
    
    for hop in range(n_hops):
        fee = sample_fee()
        hop_ts = sc_base_ts + pd.Timedelta(seconds=float(time_offsets_s[hop]))
        n_out = sample_n_outputs("licit_normal")
        if n_out == 1: n_out = 2
        
        peel_total = 0
        out_addrs = []
        out_amts = []
        for k in range(n_out - 1):
            peel_amt = round(remaining * float(rng.uniform(0.05, 0.20)), 8)
            peel_total += peel_amt
            out_addrs.append(gen_unique_wallet(all_wallets))
            out_amts.append(peel_amt)
            
        pass_amt = round(remaining - peel_total - fee, 8)
        if pass_amt <= 1e-6: break
        
        next_w = gen_unique_wallet(all_wallets) if random.random() > 0.3 else current_wallet
        out_addrs.append(next_w)
        out_amts.append(pass_amt)
        
        licit_records.append(make_tx_record(
            [current_wallet], [remaining], out_addrs, out_amts, fee,
            hop_ts, 0, "normal", sc_id, "licit", sc_ips, sc_asns_list, "licit_consolidation"
        ))
        current_wallet = next_w
        remaining = pass_amt

# 2. Licit Layering (Corporate Treasury / Exchange Rebalance)
for sc_idx in range(400):
    sc_id = f"licit_layer_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 14 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    total_amount = max(round(float(rng.lognormal(1.5, 1.0)), 8), 1.0)
    
    n_fanout = random.randint(5, 12)
    fee1 = sample_fee()
    in_addrs = [gen_unique_wallet(all_wallets)]
    in_amts = [round(total_amount + fee1, 8)]
    intermediate_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
    out_amts = distribute_amount(total_amount, n_fanout)
    licit_records.append(make_tx_record(
        in_addrs, in_amts, intermediate_wallets, out_amts, fee1,
        sc_base_ts, 0, "normal", sc_id, "licit", sc_ips, sc_asns_list, "licit_treasury"
    ))
    
    # Hops & fan-in
    next_stage = []
    for iw, ia in zip(intermediate_wallets, out_amts):
        fee_hop = sample_fee()
        hop_amt = round(ia - fee_hop, 8)
        if hop_amt > 1e-6:
            nw = gen_unique_wallet(all_wallets)
            next_stage.append((nw, hop_amt))
            licit_records.append(make_tx_record(
                [iw], [ia], [nw], [hop_amt], fee_hop,
                sc_base_ts + pd.Timedelta(minutes=random.randint(30, 300)), 0, "normal", sc_id, "licit", sc_ips, sc_asns_list, "licit_treasury"
            ))
            
    if next_stage:
        fee_in = sample_fee()
        chunk_in_addrs = [w for w, _ in next_stage]
        chunk_in_amts = [a for _, a in next_stage]
        tot_out = round(sum(chunk_in_amts) - fee_in, 8)
        if tot_out > 1e-6:
            licit_records.append(make_tx_record(
                chunk_in_addrs, chunk_in_amts, [gen_unique_wallet(all_wallets)], [tot_out], fee_in,
                sc_base_ts + pd.Timedelta(hours=10), 0, "normal", sc_id, "licit", sc_ips, sc_asns_list, "licit_treasury"
            ))

# 3. Licit Mixing (Privacy-conscious User CoinJoin)
for sc_idx in range(400):
    sc_id = f"licit_mix_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 19 + i) for i in range(3)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=3, replace=True))
    base_denom = max(round(float(rng.lognormal(-0.5, 0.8)), 8), 0.01)
    
    n_p = random.randint(3, 6)
    n_rounds = random.randint(2, 4)
    current_in = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
    for rnd in range(n_rounds):
        fee = sample_fee()
        round_ts = sc_base_ts + pd.Timedelta(hours=rnd * 1.5)
        in_amts = [base_denom] * n_p
        tot_in = round(sum(in_amts), 8)
        tot_out = round(tot_in - fee, 8)
        new_out = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        out_amts = [round(tot_out / n_p, 8)] * n_p
        licit_records.append(make_tx_record(
            current_in, in_amts, new_out, out_amts, fee,
            round_ts, 0, "normal", sc_id, "licit", sc_ips, sc_asns_list, "licit_privacy"
        ))
        current_in = new_out
        base_denom = round(tot_out / n_p, 8)

# PHASE 6C: EXACT STRUCTURAL OVERLAPS (To break Gate I)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 6C — Exact Structural Overlaps")
print("=" * 70)

def generate_shared_mixer_structure(sc_id, pattern_type, source_tag, sc_idx):
    records = []
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 31 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    n_participants = 5
    in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
    total_amt = sum([max(round(float(rng.lognormal(0, 1.0)), 8), 0.1) for _ in range(n_participants)])
    
    # 1. Fan-in
    mixer = gen_unique_wallet(all_wallets)
    fee = sample_fee()
    in_amts = distribute_amount(round(total_amt + fee, 8), n_participants)
    records.append(make_tx_record(
        in_addrs, in_amts, [mixer], [total_amt], fee,
        sc_base_ts, 1, pattern_type, sc_id, "illicit", sc_ips, sc_asns_list, source_tag
    ))
    
    # 2. Fan-out
    fee2 = sample_fee()
    out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_participants)]
    out_amts = distribute_amount(round(total_amt - fee2, 8), n_participants)
    records.append(make_tx_record(
        [mixer], [total_amt], out_addrs, out_amts, fee2,
        sc_base_ts + pd.Timedelta(hours=2), 1, pattern_type, sc_id, "illicit", sc_ips, sc_asns_list, source_tag
    ))
    return records

def generate_shared_peel_structure(sc_id, pattern_type, source_tag, sc_idx):
    records = []
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 37 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    current_wallet = gen_unique_wallet(all_wallets)
    remaining = max(round(float(rng.lognormal(1.0, 1.0)), 8), 1.0)
    
    for hop in range(8):
        fee = sample_fee()
        hop_ts = sc_base_ts + pd.Timedelta(hours=hop)
        n_out = 3
        out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
        pass_amt = round(remaining * 0.7, 8)
        peel_amts = distribute_amount(round(remaining - pass_amt - fee, 8), n_out - 1)
        out_amts = peel_amts + [pass_amt]
        
        records.append(make_tx_record(
            [current_wallet], [remaining], out_addrs, out_amts, fee,
            hop_ts, 1, pattern_type, sc_id, "illicit", sc_ips, sc_asns_list, source_tag
        ))
        current_wallet = out_addrs[-1]
        remaining = pass_amt
    return records

# Inject EXACT SAME mixer structures across multiple typologies
for sc_idx in range(400):
    mixing_records.extend(generate_shared_mixer_structure(f"mix_shared_{sc_idx:04d}", "mixing", "shared_mixer", sc_idx))
for sc_idx in range(400):
    ransom_records.extend(generate_shared_mixer_structure(f"ransom_mix_shared_{sc_idx:04d}", "ransomware", "shared_mixer", sc_idx + 400))
for sc_idx in range(400):
    layering_records.extend(generate_shared_mixer_structure(f"layer_mix_shared_{sc_idx:04d}", "layering", "shared_mixer", sc_idx + 800))

# Inject EXACT SAME peel structures across multiple typologies
for sc_idx in range(400):
    peeling_records.extend(generate_shared_peel_structure(f"peel_shared_{sc_idx:04d}", "peeling_chain", "shared_peel", sc_idx))
for sc_idx in range(400):
    layering_records.extend(generate_shared_peel_structure(f"layer_peel_shared_{sc_idx:04d}", "layering", "shared_peel", sc_idx + 400))
for sc_idx in range(400):
    ransom_records.extend(generate_shared_peel_structure(f"ransom_peel_shared_{sc_idx:04d}", "ransomware", "shared_peel", sc_idx + 800))

# PHASE 7: MERGE, DEDUPLICATE, SHUFFLE & HASH TXIDS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 7 — Merging records and assigning hash-shuffled txids")
print("=" * 70)

all_records = (
    licit_records +
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

# Resolve collisions
collision_count = 0
while df_all["txid"].duplicated().any():
    dup_mask = df_all["txid"].duplicated(keep="first")
    for idx in df_all[dup_mask].index:
        txid_counter += 1
        df_all.at[idx, "txid"] = make_txid(txid_counter + random.randint(1, 1000000))
    collision_count += 1
    if collision_count > 100:
        break

print(f"  Collision resolution rounds: {collision_count}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: TIMESTAMPS & RELAY TIMESTAMPS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 8 — Setting relay_timestamps")
print("=" * 70)

df_all["timestamp"] = pd.to_datetime(df_all["timestamp"]).dt.floor("s")
random_ms = rng.integers(50, 501, size=len(df_all))
df_all["relay_timestamp"] = df_all["timestamp"] - pd.to_timedelta(random_ms, unit="ms")

df_all["protocol_version"] = 70015
df_all["user_agent"] = rng.choice(USER_AGENTS, size=len(df_all), p=USER_AGENT_WEIGHTS)

is_standard_port = rng.random(len(df_all)) < 0.85
alt_ports = rng.choice([18333] + list(range(49152, 65536, 64)), size=len(df_all))
df_all["relay_port"] = np.where(is_standard_port, 8333, alt_ports)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: SCENARIO-LEVEL STRATIFIED TRAIN/TEST SPLIT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 9 — Scenario-level stratified train/test split")
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

leak_check = train_scenarios & test_scenarios
assert len(leak_check) == 0, f"Leaking scenarios detected: {len(leak_check)}"

df_all["split"] = df_all["scenario_id"].apply(lambda s: "train" if s in train_scenarios else "test")

print(f"  Total scenarios: {len(scenario_summary):,}")
print(f"  Train scenarios: {len(train_scenarios):,} | Test scenarios: {len(test_scenarios):,}")
print(f"  Shared scenarios: {len(leak_check)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: SAVE MASTER AND SPLIT CSV FILES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 10 — Saving CSV files")
print("=" * 70)

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


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 11: QUICK INTEGRITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 11 — Quick integrity checks")
print("=" * 70)

# Accounting identity
import json as json_module
violations = 0
for _, row in df_all.iterrows():
    in_sum = sum(json_module.loads(row["input_amounts"]) if isinstance(row["input_amounts"], str) else row["input_amounts"])
    out_sum = sum(json_module.loads(row["output_amounts"]) if isinstance(row["output_amounts"], str) else row["output_amounts"])
    residual = abs(in_sum - out_sum - row["fee_btc"])
    if residual > 1e-4:
        violations += 1
print(f"  Accounting violations (>1e-4): {violations}")

# Label homogeneity
label_homo = df_all.groupby("scenario_id")["is_illicit"].nunique()
mixed = (label_homo > 1).sum()
print(f"  Mixed-label scenarios: {mixed}")

# Scenario counts
print(f"  Pattern/scenario counts:")
sc_counts = df_all.groupby("pattern_type")["scenario_id"].nunique()
for pt, cnt in sc_counts.items():
    print(f"    {pt}: {cnt} scenarios")

# Node type overlap check
licit_nodes = set(df_all[df_all["is_illicit"] == 0]["node_type"].unique())
illicit_nodes = set(df_all[df_all["is_illicit"] == 1]["node_type"].unique())
shared_nodes = licit_nodes & illicit_nodes
all_nodes = licit_nodes | illicit_nodes
print(f"  Node type overlap: {len(shared_nodes)}/{len(all_nodes)} ({100*len(shared_nodes)/len(all_nodes):.1f}%)")
print(f"    Licit: {sorted(licit_nodes)}")
print(f"    Illicit: {sorted(illicit_nodes)}")

print("\n" + "=" * 70)
print("🎉 V5.0 GENERATION COMPLETE")
print("=" * 70)
