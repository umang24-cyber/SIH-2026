"""
generate_v7.py
==============
SIH 2026 — Bitcoin AML Dataset v7.0 Generation Pipeline

V7 Key Improvements over V6:
  1. HierarchicalSampler: BitcoinHeist macro + ORBITAAL micro profiles drive scenario sizing.
  2. Typology-specific sc_size multipliers (B1 fix): prevents num_txns collapse to a
     single point mass by applying per-typology floor/cap before the global limit.
  3. Ransomware fan_in input count (B5 fix): fan_in primitive uses 1-2 inputs for ransomware
     (victim-payment semantics: 1 victim → 1 attacker), not 3-8 (structural consolidation).

V5/V6 Key Improvements (inherited, for reference):
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
PROC_DIR = os.path.join(BASE_DIR, "data", "processed_v8")
os.makedirs(PROC_DIR, exist_ok=True)

SATOSHIS_PER_BTC = 100_000_000

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

def sample_fee_satoshis() -> int:
    return int(rng.uniform(1000, 45000))

def sample_amount_satoshis() -> int:
    val = float(rng.lognormal(mean=-1.8, sigma=1.4))
    return int(max(val * SATOSHIS_PER_BTC, 100))

def sample_script_type() -> str:
    return str(rng.choice(
        ["P2PKH", "P2SH", "P2WPKH", "P2WSH"],
        p=[0.45, 0.25, 0.25, 0.05]
    ))

def distribute_amount_satoshis(total: int, n: int) -> list:
    if total < n * 100:
        raise ValueError(f"total amount {total} too small for {n} outputs")
    if n == 1:
        return [total]
    dist_total = total - n * 100
    fracs = rng.dirichlet(np.ones(n))
    parts = [int(dist_total * float(f)) for f in fracs]
    parts[-1] += dist_total - sum(parts)
    return [p + 100 for p in parts]

def random_timestamp_in_range(start_year=2012, end_year=2018) -> pd.Timestamp:
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp(f"{end_year}-12-31 23:59:59")
    delta_s = (end - start).total_seconds()
    offset_s = float(rng.uniform(0, delta_s))
    return start + pd.Timedelta(seconds=offset_s)

def fix_accounting_satoshis(in_amts, out_amts, fee):
    assert sum(in_amts) == sum(out_amts) + fee, f"Conservation violation: {sum(in_amts)} != {sum(out_amts)} + {fee}"
    assert all(x >= 0 for x in in_amts), "Negative input amount"
    assert all(x >= 0 for x in out_amts), "Negative output amount"
    assert fee >= 0, "Negative fee"
    assert fee <= sum(in_amts), "Fee > total inputs"
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
    # fix_accounting is handled before conversion to float

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


# ═══════════════════════════════════════════════════════════════════════════════
# PROBABILISTIC SCENARIO GENERATOR (V7)
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 1-6 — Generating Probabilistic Scenarios")
print("=" * 70)

import sys
sys.path.append(BASE_DIR)
from data_pipeline.hierarchical_sampler import HierarchicalSampler

print("Loading Real Data Profiles...")
macro = pd.read_csv(os.path.join(BASE_DIR, "real_data/BitcoinHeist/bitcoinheist_address_profiles.csv"))
micro = pd.read_csv(os.path.join(BASE_DIR, "real_data/ORBITAAL/orbitaal_node_profiles.csv"))
sampler = HierarchicalSampler(macro, micro)

all_records = []

# TARGET DIRICHLET WEIGHTS [chain_hop, fan_out, fan_in, mixer_round]
TYPOLOGY_TARGETS = {
    "normal": [0.40, 0.30, 0.20, 0.10],
    "ransomware": [0.30, 0.10, 0.60, 0.00],
    "peeling_chain": [0.80, 0.15, 0.05, 0.00],
    "layering": [0.20, 0.70, 0.00, 0.10],
    "mixing": [0.10, 0.10, 0.10, 0.70]
}

for k, v in TYPOLOGY_TARGETS.items():
    TYPOLOGY_TARGETS[k] = [max(x, 0.01) for x in v]
    s = sum(TYPOLOGY_TARGETS[k])
    TYPOLOGY_TARGETS[k] = [x/s for x in TYPOLOGY_TARGETS[k]]

DIRICHLET_CONCENTRATION = 1.0 # Low concentration -> high scenario variance

def generate_probabilistic_scenario(sc_id, pattern_type, target_tx_count, base_ts, offsets_s, sc_ips, sc_asns, node_type_ctx, profile):
    records = []
    
    target_weights = TYPOLOGY_TARGETS[pattern_type]
    alphas = np.array(target_weights) * DIRICHLET_CONCENTRATION
    scenario_weights = rng.dirichlet(alphas)
    
    primitives = ["chain_hop", "fan_out", "fan_in", "mixer_round"]
    
    base_amt = int(profile["micro"]["mean_transfer_amount"])
    active_wallets = [(gen_unique_wallet(all_wallets), int(np.clip(rng.normal(base_amt * 10, base_amt), 100, 21_000_000 * SATOSHIS_PER_BTC)))] 
    
    for t in range(target_tx_count):
        prim = rng.choice(primitives, p=scenario_weights)
        tx_ts = base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
        
        def s_amt():
            return int(np.clip(rng.normal(base_amt, base_amt * 0.5), 100, 21_000_000 * SATOSHIS_PER_BTC))
            
        while True:
            # Resampling loop for impossible transactions
            fee_sats = sample_fee_satoshis()
            
            in_addrs = []
            in_amts = []
            out_addrs = []
            out_amts = []
            
            # Temporary copy so we don't destroy active_wallets if we abort
            temp_active = list(active_wallets)
            
            if prim == "chain_hop":
                if temp_active:
                    in_w, bal = temp_active.pop(0)
                else:
                    in_w = gen_unique_wallet(all_wallets)
                    bal = s_amt() * 2
                
                in_addrs = [in_w]
                in_amts = [bal]
                
                available_sats = sum(in_amts)
                if available_sats <= 100:
                    if active_wallets: active_wallets.pop(0)
                    continue # Resample
                fee_sats = min(fee_sats, available_sats - 100)
                
                out_w = gen_unique_wallet(all_wallets)
                out_addrs = [out_w]
                out_amts = [available_sats - fee_sats]
                
                temp_active.append((out_w, out_amts[0]))
                
            elif prim == "fan_out":
                if temp_active:
                    in_w, bal = temp_active.pop(0)
                else:
                    in_w = gen_unique_wallet(all_wallets)
                    bal = s_amt() * 5
                
                in_addrs = [in_w]
                in_amts = [bal]
                n_out = random.randint(3, 8)
                
                available_sats = sum(in_amts)
                min_req = n_out * 100
                if available_sats <= min_req:
                    if active_wallets: active_wallets.pop(0)
                    continue # Resample
                    
                fee_sats = min(fee_sats, available_sats - min_req)
                tot_out = available_sats - fee_sats
                
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                out_amts = distribute_amount_satoshis(tot_out, n_out)
                
                for w, a in zip(out_addrs, out_amts):
                    temp_active.append((w, a))
                    
            elif prim == "fan_in":
                if pattern_type == "ransomware":
                    n_in = random.randint(1, 2)
                else:
                    n_in = random.randint(3, 8)
                    
                for _ in range(n_in):
                    if temp_active:
                        w, a = temp_active.pop(0)
                        in_addrs.append(w)
                        in_amts.append(a)
                    else:
                        in_addrs.append(gen_unique_wallet(all_wallets))
                        in_amts.append(s_amt())
                        
                available_sats = sum(in_amts)
                if available_sats <= 100:
                    if active_wallets: active_wallets.pop(0)
                    continue # Resample
                    
                fee_sats = min(fee_sats, available_sats - 100)
                tot_out = available_sats - fee_sats
                
                out_w = gen_unique_wallet(all_wallets)
                out_addrs = [out_w]
                out_amts = [tot_out]
                temp_active.append((out_w, tot_out))
                
            elif prim == "mixer_round":
                n_in = random.randint(3, 6)
                for _ in range(n_in):
                    if temp_active:
                        w, a = temp_active.pop(0)
                        in_addrs.append(w)
                        in_amts.append(a)
                    else:
                        in_addrs.append(gen_unique_wallet(all_wallets))
                        in_amts.append(s_amt())
                        
                n_out = random.randint(3, 6)
                available_sats = sum(in_amts)
                min_req = n_out * 100
                if available_sats <= min_req:
                    if active_wallets: active_wallets = active_wallets[1:]
                    continue # Resample
                    
                fee_sats = min(fee_sats, available_sats - min_req)
                tot_out = available_sats - fee_sats
                
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                out_amts = distribute_amount_satoshis(tot_out, n_out)
                
                for w, a in zip(out_addrs, out_amts):
                    temp_active.append((w, a))
            
            # If we reached here, the transaction is valid!
            active_wallets = temp_active
            break # break out of resampling loop
            
        active_wallets = [(w, a) for w, a in active_wallets if a > fee_sats * 2]
        
        is_illicit = 0 if pattern_type == "normal" else 1
        source_tag = pattern_type
        
        # Hard assertion before serialization
        out_amts = fix_accounting_satoshis(in_amts, out_amts, fee_sats)
        
        in_amts_btc = [a / SATOSHIS_PER_BTC for a in in_amts]
        out_amts_btc = [a / SATOSHIS_PER_BTC for a in out_amts]
        fee_btc = fee_sats / SATOSHIS_PER_BTC
        
        records.append(make_tx_record(
            in_addrs, in_amts_btc, out_addrs, out_amts_btc, fee_btc,
            tx_ts, is_illicit, pattern_type, sc_id, node_type_ctx, sc_ips, sc_asns, source_tag
        ))
        
    return records


# Generate scenarios
def main():
    global txid_counter, all_wallets, rng, all_records
    SCENARIO_COUNTS = {
        "normal": N_LICIT_SCENARIOS,
        "ransomware": N_RANSOMWARE_TARGET // 20, 
        "peeling_chain": N_PEELING_SCENARIOS,
        "layering": N_LAYERING_SCENARIOS,
        "mixing": N_MIXING_SCENARIOS
    }
    
    scenario_num = 0
    for pat_type, num_scenarios in SCENARIO_COUNTS.items():
        print(f"Generating {num_scenarios} {pat_type} scenarios...")
        node_type_ctx = "licit" if pat_type == "normal" else "illicit"
        
        for _ in range(num_scenarios):
            scenario_num += 1
            if scenario_num % 100 == 0:
                print(f"  Generated {scenario_num} scenarios...")
            sc_id = f"{pat_type}_{scenario_num:05d}"
            
            # Sample profile
            if pat_type == "ransomware":
                # Just use pooled for now, could pick families
                prof = sampler.sample(scenario_type="ransomware")
                t_year = prof["macro"]["year"]
            else:
                # We'll match era uniformly or based on ransomware if we tracked it,
                # For now, let's just use uniform 2013-2018 or specific year
                t_year = random.randint(2013, 2018)
                prof = sampler.sample(scenario_type="background", target_year=t_year)
                
            # B1 FIX: typology-specific sc_size multipliers.
            # BitcoinHeist total_count median = 1 for BOTH background and ransomware.
            # Without this fix, max(5, 1) = 5 for ALL typologies → num_txns collapses
            # to identical distributions (97.5% licit/illicit overlap diagnosed in audit).
            # Multipliers and floors reflect real behavioral differences per typology:
            #   peeling_chain: long chains → 1.5x, floor=10
            #   layering:      moderate depth → 1.2x, floor=8
            #   mixing:        round-trip cycles → floor=15 (must have enough for rounds)
            #   ransomware:    short, concentrated → 0.5x, cap=50
            #   normal:        unchanged baseline
            _TYPOLOGY_SC_SIZE = {
                "peeling_chain": (1.5, 10, 300),
                "layering":      (1.2, 8,  300),
                "mixing":        (1.0, 15, 300),
                "ransomware":    (0.5, 3,  50),
                "normal":        (1.0, 5,  200),
            }
            _raw_count = max(1, int(prof["macro"]["total_count"]))
            _mult, _floor, _cap = _TYPOLOGY_SC_SIZE.get(pat_type, (1.0, 5, 200))
            sc_size = max(_floor, min(int(_raw_count * _mult), _cap))
            
            target_dur_hrs = max(2.0, float(prof["macro"]["active_days"]) * 24.0)
            
            # Use year for timestamp
            sc_base_ts = random_timestamp_in_range(t_year, t_year)
            
            # ORBITAAL temporal structure
            mean_inter_event = prof["micro"]["inter_event_delta_mean"]
            # Convert to bursty offsets
            b = prof["micro"]["burstiness_B"]
            # Generate inter-event times using a pareto or similar if bursty
            if b > 0.2:
                deltas = rng.pareto(1/b, size=sc_size-1) * mean_inter_event
            else:
                deltas = rng.exponential(mean_inter_event, size=sc_size-1)
                
            # Scale deltas to fit target_dur_hrs roughly, or just use deltas!
            # If we use deltas, we preserve the micro profile perfectly.
            time_offsets_s = [0.0]
            cur_t = 0.0
            for d in deltas:
                cur_t += d
                time_offsets_s.append(cur_t)
            
            n_ips = random.randint(1, 3)
            sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=min(n_ips, 2), replace=True))
            sc_ips = [gen_ipv4_for_asn(scenario_num * 3 + i) for i in range(n_ips)]
            
            recs = generate_probabilistic_scenario(sc_id, pat_type, sc_size, sc_base_ts, time_offsets_s, sc_ips, sc_asns_list, node_type_ctx, prof)
            all_records.extend(recs)
    
    licit_records = [r for r in all_records if r["is_illicit"] == 0]
    exchange_records = []
    ransom_records = [r for r in all_records if r["pattern_type"] == "ransomware"]
    peeling_records = [r for r in all_records if r["pattern_type"] == "peeling_chain"]
    layering_records = [r for r in all_records if r["pattern_type"] == "layering"]
    mixing_records = [r for r in all_records if r["pattern_type"] == "mixing"]
    
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

if __name__ == "__main__":
    main()
