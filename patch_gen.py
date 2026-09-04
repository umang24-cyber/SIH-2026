import re
import sys
import textwrap

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # The noise block template (dedented)
    noise_template = textwrap.dedent("""\
        # --- V4 NOISE INJECTION ---
        if random.random() < 0.5:
            # aggressive dust sweep to increase mean_num_inputs & unique_input_addrs
            extra_ins = random.randint(1, 6)
            for _ in range(extra_ins):
                dust = round(float(rng.uniform(0.001, 0.015)), 8)
                {IN_ADDRS}.append(random.choice({IN_ADDRS}) if random.random() < 0.5 else gen_unique_wallet(all_wallets))
                {IN_AMTS}.append(dust)
                if len({OUT_AMTS}) > 0:
                    {OUT_AMTS}[0] = round({OUT_AMTS}[0] + dust, 8)

        if random.random() < 0.5 and len({OUT_AMTS}) > 0 and {OUT_AMTS}[-1] > 0.05:
            # split change to increase outputs (decreases fanin_ratio)
            extra_outs = random.randint(1, 6)
            for _ in range(extra_outs):
                if {OUT_AMTS}[-1] < 0.01: break
                split_amt = round({OUT_AMTS}[-1] * float(rng.uniform(0.1, 0.4)), 8)
                {OUT_AMTS}[-1] = round({OUT_AMTS}[-1] - split_amt, 8)
                {OUT_ADDRS}.append(random.choice({IN_ADDRS}) if random.random() < 0.4 else gen_unique_wallet(all_wallets))
                {OUT_AMTS}.append(split_amt)

        if random.random() < 0.6 and len({OUT_ADDRS}) > 0:
            # aggressive address reuse to change address_reuse_ratio and edge_to_node_ratio
            for _ in range(random.randint(1, max(1, len({OUT_ADDRS})//2))):
                idx = random.randint(0, len({OUT_ADDRS})-1)
                {OUT_ADDRS}[idx] = random.choice({IN_ADDRS}) if random.random() < 0.8 else gen_unique_wallet(all_wallets)
        # --------------------------
        {ORIGINAL_LINE}""")

    def make_repl(in_addrs, in_amts, out_addrs, out_amts):
        def repl(m):
            indent = m.group(1)
            orig = m.group(2)
            noise = noise_template.format(
                IN_ADDRS=in_addrs, IN_AMTS=in_amts, OUT_ADDRS=out_addrs, OUT_AMTS=out_amts, ORIGINAL_LINE=orig
            )
            lines = noise.split('\n')
            indented_lines = [indent + line if line else '' for line in lines]
            return '\n'.join(indented_lines)
        return repl
    
    # 1. Standard in_amts, out_amts
    std_pattern = r'(\s+)(res = round\(sum\(in_amts\) - sum\(out_amts\) - fee, 8\))'
    content = re.sub(std_pattern, make_repl("in_addrs", "in_amts", "out_addrs", "out_amts"), content)

    # 2. chunk_in_amts
    chunk_pattern = r'(\s+)(res = round\(tot_in - sum\(chunk_out_amts\) - fee_in, 8\))'
    content = re.sub(chunk_pattern, make_repl("chunk_in_addrs", "chunk_in_amts", "chunk_out_addrs", "chunk_out_amts"), content)

    # 3. round_in_amts
    round_pattern = r'(\s+)(res = round\(total_in - sum\(round_out_amts\) - fee, 8\))'
    content = re.sub(round_pattern, make_repl("round_in_addrs", "round_in_amts", "round_out_addrs", "round_out_amts"), content)

    # 4. mixing in_amts/out_amts but with round_in_addrs
    mix2_pattern = r'(\s+)(res = round\(total_in - sum\(out_amts\) - fee, 8\))'
    content = re.sub(mix2_pattern, make_repl("round_in_addrs", "in_amts", "out_addrs", "out_amts"), content)

    with open(filepath, 'w') as f:
        f.write(content)
    
    print("Patched successfully!")

if __name__ == '__main__':
    patch_file('data_pipeline/generate_v4.py')
