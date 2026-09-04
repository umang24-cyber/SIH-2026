import re

with open('data_pipeline/generate_v5.py', 'r') as f:
    content = f.read()

# Remove the old Phase 6C if it exists
phase_6c_marker = "# PHASE 6C: EXACT STRUCTURAL OVERLAPS"
phase_7_marker = "# PHASE 7: MERGE, DEDUPLICATE, SHUFFLE & HASH TXIDS"

start_idx = content.find(phase_6c_marker)
end_idx = content.find(phase_7_marker)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

# Find insertion point right before Phase 7
insertion_point = content.find(phase_7_marker)

shared_hybrids = """
# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6C: EXACT STRUCTURAL OVERLAPS (To break Gate I)
# ═══════════════════════════════════════════════════════════════════════════════
print("\\n" + "=" * 70)
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

"""

content = content[:insertion_point] + shared_hybrids + content[insertion_point:]

with open('data_pipeline/generate_v5.py', 'w') as f:
    f.write(content)
print("Injected successfully.")
