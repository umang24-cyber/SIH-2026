import re

with open('data_pipeline/generate_v5.py', 'r') as f:
    content = f.read()

# 1. We will add a new phase "PHASE 6B: LICIT STRUCTURAL EQUIVALENTS" before Phase 7.
insertion_point = content.find("# PHASE 7: MERGE, DEDUPLICATE, SHUFFLE & HASH TXIDS")

licit_struct_code = """
# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6B: LICIT STRUCTURAL EQUIVALENTS (To break structural separability)
# ═══════════════════════════════════════════════════════════════════════════════
print("\\n" + "=" * 70)
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

"""

# 2. To fix Gate I (Typology Ablation), we will create ILLICIT HYBRIDS.
# Ransomware -> Mixer, Layering -> Peeling, etc.
illicit_hybrid_code = """
# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6C: CROSS-TYPOLOGY HYBRIDS (To break Gate I separability)
# ═══════════════════════════════════════════════════════════════════════════════
print("\\n" + "=" * 70)
print("PHASE 6C — Cross-Typology Hybrids")
print("=" * 70)

# Hybrid 1: Ransomware ending in a Mixer (Labeled Ransomware)
for sc_idx in range(300):
    sc_id = f"ransom_mix_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 21 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    # 1. Victims pay primary syndicate
    primary = gen_unique_wallet(all_wallets)
    total_ransom = 0
    for t in range(random.randint(3, 8)):
        fee = sample_fee()
        amt = sample_amount()
        ransom_records.append(make_tx_record(
            [gen_unique_wallet(all_wallets)], [round(amt + fee, 8)], [primary], [amt], fee,
            sc_base_ts + pd.Timedelta(hours=t), 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_ransom_mix"
        ))
        total_ransom += amt
        
    # 2. Primary enters mixer
    fee_mix = sample_fee()
    mix_participants = 4
    base_denom = round(total_ransom / mix_participants, 8)
    if base_denom <= 1e-6: continue
    
    in_amts = [total_ransom]
    in_addrs = [primary]
    for _ in range(mix_participants - 1):
        in_addrs.append(gen_unique_wallet(all_wallets))
        in_amts.append(total_ransom)
        
    out_addrs = [gen_unique_wallet(all_wallets) for _ in range(mix_participants)]
    tot_out = round(sum(in_amts) - fee_mix, 8)
    out_amts = [round(tot_out / mix_participants, 8)] * mix_participants
    ransom_records.append(make_tx_record(
        in_addrs, in_amts, out_addrs, out_amts, fee_mix,
        sc_base_ts + pd.Timedelta(hours=24), 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_ransom_mix"
    ))

# Hybrid 2: Layering using Peeling Chains (Labeled Layering)
for sc_idx in range(300):
    sc_id = f"layer_peel_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 22 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    # Fan out to 2 wallets
    total_amount = max(round(float(rng.lognormal(1.0, 1.0)), 8), 0.5)
    fee1 = sample_fee()
    w1, w2 = gen_unique_wallet(all_wallets), gen_unique_wallet(all_wallets)
    layering_records.append(make_tx_record(
        [gen_unique_wallet(all_wallets)], [round(total_amount + fee1, 8)], [w1, w2], [round(total_amount/2, 8)]*2, fee1,
        sc_base_ts, 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_layer_peel"
    ))
    
    # Each wallet does a 5-hop peeling chain
    for cw, camt in [(w1, round(total_amount/2, 8)), (w2, round(total_amount/2, 8))]:
        for hop in range(5):
            fee = sample_fee()
            if camt - fee <= 1e-6: break
            nw = gen_unique_wallet(all_wallets)
            peel = gen_unique_wallet(all_wallets)
            peel_amt = round(camt * 0.1, 8)
            pass_amt = round(camt - peel_amt - fee, 8)
            layering_records.append(make_tx_record(
                [cw], [camt], [peel, nw], [peel_amt, pass_amt], fee,
                sc_base_ts + pd.Timedelta(hours=hop+1), 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_layer_peel"
            ))
            cw, camt = nw, pass_amt

# Hybrid 3: Peeling using Layering (Labeled Peeling)
for sc_idx in range(300):
    sc_id = f"peel_layer_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 23 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    current_wallet = gen_unique_wallet(all_wallets)
    remaining = max(round(float(rng.lognormal(1.0, 1.2)), 8), 0.5)
    
    for hop in range(4):
        fee = sample_fee()
        hop_ts = sc_base_ts + pd.Timedelta(hours=hop)
        n_out = 5 # Fan out to 5 (layering style)
        out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
        pass_amt = round(remaining * 0.6, 8)
        peel_amts = distribute_amount(round(remaining - pass_amt - fee, 8), n_out - 1)
        out_amts = peel_amts + [pass_amt]
        
        peeling_records.append(make_tx_record(
            [current_wallet], [remaining], out_addrs, out_amts, fee,
            hop_ts, 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_peel_layer"
        ))
        current_wallet = out_addrs[-1]
        remaining = pass_amt

# Hybrid 4: Mixing using Layering (Labeled Mixing)
for sc_idx in range(300):
    sc_id = f"mix_layer_{sc_idx:04d}"
    sc_base_ts = random_timestamp_in_range(2013, 2018)
    sc_ips = [gen_ipv4_for_asn(sc_idx * 24 + i) for i in range(2)]
    sc_asns_list = list(rng.choice(GLOBAL_ASNS, size=2, replace=True))
    
    # 1. 5 participants fan-in to a central mixer (layering-like)
    mixer = gen_unique_wallet(all_wallets)
    in_addrs = [gen_unique_wallet(all_wallets) for _ in range(5)]
    total_amt = sum([sample_amount() for _ in range(5)])
    in_amts = distribute_amount(round(total_amt + sample_fee(), 8), 5)
    mixing_records.append(make_tx_record(
        in_addrs, in_amts, [mixer], [total_amt], sample_fee(),
        sc_base_ts, 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_mix_layer"
    ))
    
    # 2. Mixer fans out
    out_addrs = [gen_unique_wallet(all_wallets) for _ in range(5)]
    out_amts = distribute_amount(round(total_amt - sample_fee(), 8), 5)
    mixing_records.append(make_tx_record(
        [mixer], [total_amt], out_addrs, out_amts, sample_fee(),
        sc_base_ts + pd.Timedelta(hours=1), 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "hybrid_mix_layer"
    ))

"""

content = content[:insertion_point] + licit_struct_code + illicit_hybrid_code + content[insertion_point:]

with open('data_pipeline/generate_v5.py', 'w') as f:
    f.write(content)
