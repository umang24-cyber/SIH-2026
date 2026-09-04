import re
import sys

def patch_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    out_lines = []
    current_phase = ""
    
    for line in lines:
        if "PHASE 4" in line: current_phase = "ransomware"
        elif "PHASE 5" in line: current_phase = "peeling"
        elif "PHASE 6" in line: current_phase = "layering"
        elif "PHASE 7" in line: current_phase = "mixing"
        elif "PHASE 8" in line: current_phase = "other"
            
        if "res = round(sum(in_amts) - sum(out_amts) - fee, 8)" in line or \
           "res = round(tot_in - sum(chunk_out_amts) - fee_in, 8)" in line or \
           "res = round(total_in - sum(round_out_amts) - fee, 8)" in line or \
           "res = round(total_in - sum(out_amts) - fee, 8)" in line:
            
            indent = line[:line.find("res = round")]
            
            if "chunk" in line:
                in_addrs, in_amts, out_addrs, out_amts = "chunk_in_addrs", "chunk_in_amts", "chunk_out_addrs", "chunk_out_amts"
            elif "round_out_amts" in line:
                in_addrs, in_amts, out_addrs, out_amts = "round_in_addrs", "round_in_amts", "round_out_addrs", "round_out_amts"
            elif "total_in - sum(out_amts)" in line:
                in_addrs, in_amts, out_addrs, out_amts = "round_in_addrs", "in_amts", "out_addrs", "out_amts"
            else:
                in_addrs, in_amts, out_addrs, out_amts = "in_addrs", "in_amts", "out_addrs", "out_amts"
            
            # Custom noise
            noise = []
            noise.append(indent + "# --- V4 NOISE INJECTION ---")
            
            if current_phase == "peeling":
                # Peeling: high outputs (fanout) sometimes, low inputs. High reuse.
                noise.append(indent + f"if random.random() < 0.4:")
                noise.append(indent + f"    for _ in range(random.randint(1, 4)):")
                noise.append(indent + f"        if len({out_amts}) > 0 and {out_amts}[-1] > 0.05:")
                noise.append(indent + f"            split_amt = round({out_amts}[-1] * float(rng.uniform(0.1, 0.4)), 8)")
                noise.append(indent + f"            {out_amts}[-1] = round({out_amts}[-1] - split_amt, 8)")
                noise.append(indent + f"            {out_addrs}.append(random.choice({in_addrs}) if random.random() < 0.7 else gen_unique_wallet(all_wallets))")
                noise.append(indent + f"            {out_amts}.append(split_amt)")
                noise.append(indent + f"if random.random() < 0.2:")
                noise.append(indent + f"    for _ in range(random.randint(1, 2)):")
                noise.append(indent + f"        dust = round(float(rng.uniform(0.001, 0.02)), 8)")
                noise.append(indent + f"        {in_addrs}.append(gen_unique_wallet(all_wallets))")
                noise.append(indent + f"        {in_amts}.append(dust)")
                noise.append(indent + f"        if len({out_amts}) > 0: {out_amts}[0] = round({out_amts}[0] + dust, 8)")
                
            elif current_phase == "layering":
                # Layering: sometimes high inputs, sometimes high outputs. Address reuse is moderate.
                noise.append(indent + f"if random.random() < 0.3:")
                noise.append(indent + f"    for _ in range(random.randint(1, 3)):")
                noise.append(indent + f"        dust = round(float(rng.uniform(0.001, 0.02)), 8)")
                noise.append(indent + f"        {in_addrs}.append(random.choice({in_addrs}) if random.random() < 0.4 else gen_unique_wallet(all_wallets))")
                noise.append(indent + f"        {in_amts}.append(dust)")
                noise.append(indent + f"        if len({out_amts}) > 0: {out_amts}[0] = round({out_amts}[0] + dust, 8)")
                noise.append(indent + f"if random.random() < 0.3:")
                noise.append(indent + f"    for _ in range(random.randint(1, 3)):")
                noise.append(indent + f"        if len({out_amts}) > 0 and {out_amts}[-1] > 0.05:")
                noise.append(indent + f"            split_amt = round({out_amts}[-1] * float(rng.uniform(0.1, 0.4)), 8)")
                noise.append(indent + f"            {out_amts}[-1] = round({out_amts}[-1] - split_amt, 8)")
                noise.append(indent + f"            {out_addrs}.append(random.choice({in_addrs}) if random.random() < 0.4 else gen_unique_wallet(all_wallets))")
                noise.append(indent + f"            {out_amts}.append(split_amt)")
                
            elif current_phase == "mixing":
                # Mixing: high inputs and high outputs already. Just add some reuse and occasional dummy inputs.
                noise.append(indent + f"if random.random() < 0.2:")
                noise.append(indent + f"    for _ in range(random.randint(1, 2)):")
                noise.append(indent + f"        dust = round(float(rng.uniform(0.001, 0.02)), 8)")
                noise.append(indent + f"        {in_addrs}.append(gen_unique_wallet(all_wallets))")
                noise.append(indent + f"        {in_amts}.append(dust)")
                noise.append(indent + f"        if len({out_amts}) > 0: {out_amts}[0] = round({out_amts}[0] + dust, 8)")
                noise.append(indent + f"if random.random() < 0.3 and len({out_addrs}) > 0:")
                noise.append(indent + f"    for _ in range(max(1, len({out_addrs})//3)):")
                noise.append(indent + f"        idx = random.randint(0, len({out_addrs})-1)")
                noise.append(indent + f"        {out_addrs}[idx] = random.choice({in_addrs}) if random.random() < 0.6 else gen_unique_wallet(all_wallets)")
                
            elif current_phase == "ransomware":
                # Ransomware: high variance, sometimes massive sweeps, sometimes massive splits.
                noise.append(indent + f"if random.random() < 0.35:")
                noise.append(indent + f"    for _ in range(random.randint(1, 6)):")
                noise.append(indent + f"        dust = round(float(rng.uniform(0.001, 0.02)), 8)")
                noise.append(indent + f"        {in_addrs}.append(random.choice({in_addrs}) if random.random() < 0.3 else gen_unique_wallet(all_wallets))")
                noise.append(indent + f"        {in_amts}.append(dust)")
                noise.append(indent + f"        if len({out_amts}) > 0: {out_amts}[0] = round({out_amts}[0] + dust, 8)")
                noise.append(indent + f"if random.random() < 0.35:")
                noise.append(indent + f"    for _ in range(random.randint(1, 6)):")
                noise.append(indent + f"        if len({out_amts}) > 0 and {out_amts}[-1] > 0.05:")
                noise.append(indent + f"            split_amt = round({out_amts}[-1] * float(rng.uniform(0.1, 0.4)), 8)")
                noise.append(indent + f"            {out_amts}[-1] = round({out_amts}[-1] - split_amt, 8)")
                noise.append(indent + f"            {out_addrs}.append(random.choice({in_addrs}) if random.random() < 0.3 else gen_unique_wallet(all_wallets))")
                noise.append(indent + f"            {out_amts}.append(split_amt)")

            noise.append(indent + "# --------------------------")
            out_lines.extend([n + "\n" for n in noise])
            out_lines.append(line)
        else:
            out_lines.append(line)
            
    with open(filepath, 'w') as f:
        f.writelines(out_lines)

if __name__ == '__main__':
    patch_file('data_pipeline/generate_v4.py')
