import re

with open('data_pipeline/generate_v5.py', 'r') as f:
    content = f.read()

phase_6c_marker = "# PHASE 6C: EXACT STRUCTURAL OVERLAPS"

insertion_point = content.find(phase_6c_marker)

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

content = content[:insertion_point] + licit_struct_code + content[insertion_point:]

with open('data_pipeline/generate_v5.py', 'w') as f:
    f.write(content)
print("Injected Phase 6B successfully.")
