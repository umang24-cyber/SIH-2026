import re

with open('data_pipeline/generate_v6.py', 'r') as f:
    content = f.read()

# 1. Update Ransomware Phase 3
ransom_old = 'op_arch = rng.choice(["classic_star", "layered_fanout", "peeling_consolidation"], p=[0.50, 0.25, 0.25])'
ransom_new = '''op_arch = rng.choice(["classic_star", "layered_fanout", "peeling_consolidation", "mixer_cashout", "peeling_cashout"], p=[0.30, 0.20, 0.20, 0.15, 0.15])'''
content = content.replace(ransom_old, ransom_new)

ransom_inject = '''
    elif op_arch == "mixer_cashout":
        # Victim pays primary, primary cashes out via mixer
        for t in range(camp_size // 2):
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            n_in = sample_n_inputs("ransomware")
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_in)]
            total_amt = sample_amount()
            in_amts = distribute_amount(round(total_amt + fee, 8), n_in)
            ransom_records.append(make_tx_record(
                in_addrs, in_amts, [primary_syndicate], [total_amt], fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))
        mixer = gen_unique_wallet(all_wallets)
        n_p = 5
        fee = sample_fee()
        mixer_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[camp_size // 2]))
        in_addrs = [primary_syndicate] + [gen_unique_wallet(all_wallets) for _ in range(n_p-1)]
        in_amts = [sample_amount() for _ in range(n_p)]
        tot_amt = sum(in_amts) - fee
        ransom_records.append(make_tx_record(
            in_addrs, in_amts, [mixer], [tot_amt], fee,
            mixer_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
        ))
        fee2 = sample_fee()
        out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        out_amts = distribute_amount(round(tot_amt - fee2, 8), n_p)
        ransom_records.append(make_tx_record(
            [mixer], [tot_amt], out_addrs, out_amts, fee2,
            mixer_ts + pd.Timedelta(hours=2), 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
        ))

    elif op_arch == "peeling_cashout":
        # Victim pays primary, primary cashes out via peeling chain
        for t in range(camp_size // 2):
            fee = sample_fee()
            tx_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[t]))
            in_addrs = [gen_unique_wallet(all_wallets) for _ in range(sample_n_inputs("ransomware"))]
            total_amt = sample_amount()
            in_amts = distribute_amount(round(total_amt + fee, 8), len(in_addrs))
            ransom_records.append(make_tx_record(
                in_addrs, in_amts, [primary_syndicate], [total_amt], fee,
                tx_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))
        remaining = sample_amount() * 5
        current_w = primary_syndicate
        for hop in range(6):
            fee = sample_fee()
            if remaining - fee <= 0.05: break
            peel_amt = round(remaining * 0.2, 8)
            pass_amt = round(remaining - peel_amt - fee, 8)
            out_addrs = [gen_unique_wallet(all_wallets), gen_unique_wallet(all_wallets)]
            out_amts = [peel_amt, pass_amt]
            hop_ts = sc_base_ts + pd.Timedelta(seconds=float(offsets_s[camp_size // 2]) + hop * 3600)
            ransom_records.append(make_tx_record(
                [current_w], [remaining], out_addrs, out_amts, fee,
                hop_ts, 1, "ransomware", sc_id, "illicit", sc_ips, sc_asns_list, "ransomware_campaign"
            ))
            current_w = out_addrs[1]
            remaining = pass_amt
'''

if 'op_arch == "peeling_cashout"' not in content:
    content = content.replace('        # Now sweep them in a chain (peeling)', ransom_inject + '\n        # Now sweep them in a chain (peeling)')

# 2. Update Peeling Phase 4
peel_old = 'op_arch = rng.choice(["branching_peel", "deep_peel"], p=[0.70, 0.30])'
peel_new = 'op_arch = rng.choice(["branching_peel", "deep_peel", "peeling_with_fanout"], p=[0.50, 0.25, 0.25])'
content = content.replace(peel_old, peel_new)

peel_inject = '''
    elif op_arch == "peeling_with_fanout":
        # Peeling chain that occasionally splinters into secondary branching fan-outs (Layering-like)
        current_wallet = gen_unique_wallet(all_wallets)
        remaining = total_amount
        for hop in range(chain_length):
            fee = sample_fee()
            if remaining - fee <= 1e-6: break
            hop_ts = sc_base_ts + pd.Timedelta(minutes=random.randint(20, 180) * (hop+1))
            
            if hop > 0 and hop % 3 == 0:
                # Layering-like fanout
                n_out = random.randint(4, 8)
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                pass_amt = round(remaining * 0.5, 8)
                peel_amts = distribute_amount(round(remaining - pass_amt - fee, 8), n_out - 1)
                out_amts = peel_amts + [pass_amt]
                peeling_records.append(make_tx_record(
                    [current_wallet], [remaining], out_addrs, out_amts, fee,
                    hop_ts, 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peel"
                ))
                current_wallet = out_addrs[-1]
                remaining = pass_amt
            else:
                n_out = sample_n_outputs("peeling_chain")
                out_addrs = [gen_unique_wallet(all_wallets) for _ in range(n_out)]
                pass_amt = round(remaining * float(rng.uniform(0.6, 0.9)), 8)
                peel_amts = distribute_amount(round(remaining - pass_amt - fee, 8), n_out - 1)
                out_amts = peel_amts + [pass_amt]
                peeling_records.append(make_tx_record(
                    [current_wallet], [remaining], out_addrs, out_amts, fee,
                    hop_ts, 1, "peeling_chain", sc_id, "illicit", sc_ips, sc_asns_list, "planted_peel"
                ))
                current_wallet = out_addrs[-1]
                remaining = pass_amt
'''

if 'op_arch == "peeling_with_fanout"' not in content:
    content = content.replace('print(f"  Planted {len(peeling_records):,} peeling txns', peel_inject + '\nprint(f"  Planted {len(peeling_records):,} peeling txns')

# 3. Update Mixing Phase 6
mix_old = 'op_arch = rng.choice(["classic_mix", "sequential_mix", "self_mix"], p=[0.50, 0.25, 0.25])'
mix_new = 'op_arch = rng.choice(["classic_mix", "sequential_mix", "self_mix", "mix_with_consolidation"], p=[0.40, 0.20, 0.20, 0.20])'
content = content.replace(mix_old, mix_new)

mix_inject = '''
    elif op_arch == "mix_with_consolidation":
        # Mixing -> Exchange-style consolidation (peeling-like fan-in)
        n_p = random.randint(4, 7)
        in_amts = [base_denom] * n_p
        tot_in = round(sum(in_amts), 8)
        current_in = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        fee = sample_fee()
        tot_out = round(tot_in - fee, 8)
        new_out = [gen_unique_wallet(all_wallets) for _ in range(n_p)]
        out_amts = [round(tot_out / n_p, 8)] * n_p
        mixing_records.append(make_tx_record(
            current_in, in_amts, new_out, out_amts, fee,
            sc_base_ts, 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
        ))
        
        # Consolidate outputs in a chain
        c_wallet = new_out[0]
        c_amt = out_amts[0]
        for i in range(1, n_p):
            fee = sample_fee()
            in_addrs = [c_wallet, new_out[i]]
            in_amts = [c_amt, out_amts[i]]
            next_w = gen_unique_wallet(all_wallets)
            tot = round(sum(in_amts) - fee, 8)
            mixing_records.append(make_tx_record(
                in_addrs, in_amts, [next_w], [tot], fee,
                sc_base_ts + pd.Timedelta(hours=2+i), 1, "mixing", sc_id, "illicit", sc_ips, sc_asns_list, "planted_mixing"
            ))
            c_wallet, c_amt = next_w, tot
'''

if 'op_arch == "mix_with_consolidation"' not in content:
    content = content.replace('print(f"  Planted {len(mixing_records):,} mixing txns', mix_inject + '\nprint(f"  Planted {len(mixing_records):,} mixing txns')

with open('data_pipeline/generate_v6.py', 'w') as f:
    f.write(content)
print("Injected composite typologies successfully.")
