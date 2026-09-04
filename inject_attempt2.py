import re

# 1. Update feature engineering to remove redundant fanin/fanout ratios
with open('ml/02_feature_engineering.py', 'r') as f:
    feat_content = f.read()

feat_content = feat_content.replace('feats["fanin_ratio"]  = feats["unique_input_addrs"]  / n', '# fanin_ratio removed due to mathematical redundancy with mean_num_inputs')
feat_content = feat_content.replace('feats["fanout_ratio"] = feats["unique_output_addrs"] / n', '# fanout_ratio removed due to mathematical redundancy with mean_num_outputs')

with open('ml/02_feature_engineering.py', 'w') as f:
    f.write(feat_content)

# 2. Update generate_v6.py to add fan-in to Layering and Peeling
with open('data_pipeline/generate_v6.py', 'r') as f:
    gen_content = f.read()

# Peeling Phase 4
peel_old = 'op_arch = rng.choice(["branching_peel", "deep_peel", "peeling_with_fanout"], p=[0.50, 0.25, 0.25])'
peel_new = 'op_arch = rng.choice(["branching_peel", "deep_peel", "peeling_with_fanout", "peeling_with_fanin"], p=[0.35, 0.20, 0.25, 0.20])'
gen_content = gen_content.replace(peel_old, peel_new)

peel_inject = '''
    elif op_arch == "peeling_with_fanin":
        # Ransomware-like fan-in followed by a peeling chain
        n_victims = random.randint(10, 30)
        sc_base_ts = random_timestamp_in_range(2013, 2018)
        primary = gen_unique_wallet(all_wallets)
        for t in range(n_victims):
            fee = sample_fee()
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(sample_n_inputs("ransomware"))]
            total_amt = sample_amount()
            in_amts = distribute_amount(round(total_amt + fee, 8), len(in_addrs))
            peeling_records.append(make_tx_record(
                in_addrs, in_amts, [primary], [total_amt], fee,
                sc_base_ts + pd.Timedelta(minutes=t*10), 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peel"
            ))
        remaining = sample_amount() * n_victims
        current_wallet = primary
        for hop in range(chain_length):
            fee = sample_fee()
            if remaining - fee <= 1e-6: break
            n_out = sample_n_outputs("peeling_chain")
            out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
            pass_amt = round(remaining * float(rng.uniform(0.6, 0.9)), 8)
            peel_amts = distribute_amount(round(remaining - pass_amt - fee, 8), n_out - 1)
            out_amts = peel_amts + [pass_amt]
            peeling_records.append(make_tx_record(
                [current_wallet], [remaining], out_addrs, out_amts, fee,
                sc_base_ts + pd.Timedelta(hours=5) + pd.Timedelta(minutes=random.randint(20, 180) * (hop+1)), 
                1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peel"
            ))
            current_wallet = out_addrs[-1]
            remaining = pass_amt
'''

if 'op_arch == "peeling_with_fanin"' not in gen_content:
    gen_content = gen_content.replace('print(f"  Planted {len(peeling_records):,} peeling txns', peel_inject + '\nprint(f"  Planted {len(peeling_records):,} peeling txns')


# Layering Phase 5
layer_old = 'op_arch = rng.choice(["classic_layer", "deep_layer", "dense_layer"], p=[0.40, 0.30, 0.30])'
layer_new = 'op_arch = rng.choice(["classic_layer", "deep_layer", "dense_layer", "layering_with_fanin"], p=[0.25, 0.25, 0.25, 0.25])'
gen_content = gen_content.replace(layer_old, layer_new)

layer_inject = '''
    elif op_arch == "layering_with_fanin":
        # Ransomware-like fan-in followed by massive layering fanout
        n_victims = random.randint(15, 40)
        sc_base_ts = random_timestamp_in_range(2013, 2018)
        primary = gen_unique_wallet(all_wallets)
        total_collected = 0
        for t in range(n_victims):
            fee = sample_fee()
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(sample_n_inputs("ransomware"))]
            total_amt = sample_amount()
            in_amts = distribute_amount(round(total_amt + fee, 8), len(in_addrs))
            total_collected += total_amt
            layering_records.append(make_tx_record(
                in_addrs, in_amts, [primary], [total_amt], fee,
                sc_base_ts + pd.Timedelta(minutes=t*5), 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
            ))
            
        fee1 = sample_fee()
        in_addrs = [primary]
        in_amts = [round(total_collected, 8)]
        branch_wallets = [gen_unique_wallet(all_wallets) for _ in range(n_fanout)]
        branch_amts = distribute_amount(round(total_collected - fee1, 8), n_fanout)
        layering_records.append(make_tx_record(
            in_addrs, in_amts, branch_wallets, branch_amts, fee1,
            sc_base_ts + pd.Timedelta(hours=4), 1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
        ))
        for bw, bamt in zip(branch_wallets, branch_amts):
            cw, camt = bw, bamt
            for hop in range(random.randint(5, 10)):
                fee = sample_fee()
                if camt - fee <= 1e-6: break
                nw = gen_unique_wallet(all_wallets)
                layering_records.append(make_tx_record(
                    [cw], [camt], [nw], [round(camt - fee, 8)], fee,
                    sc_base_ts + pd.Timedelta(hours=4) + pd.Timedelta(minutes=random.randint(60, 600) * (hop+1)), 
                    1, "layering", sc_id, "illicit", sc_ips, sc_asns_list, "planted_layering"
                ))
                cw, camt = round(camt - fee, 8)
'''

if 'op_arch == "layering_with_fanin"' not in gen_content:
    gen_content = gen_content.replace('print(f"  Planted {len(layering_records):,} layering txns', layer_inject + '\nprint(f"  Planted {len(layering_records):,} layering txns')

with open('data_pipeline/generate_v6.py', 'w') as f:
    f.write(gen_content)

print("Injected Attempt 2 fixes successfully.")
