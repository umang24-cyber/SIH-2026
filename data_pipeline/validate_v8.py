import pandas as pd
import json
import numpy as np

def validate_v8():
    blockchain = pd.read_csv('data/processed_v8/blockchain_transactions.csv')
    network = pd.read_csv('data/processed_v8/network_metadata.csv')
    
    report = {}
    
    # 1. MONETARY
    def safe_parse(x):
        try:
            return json.loads(x)
        except:
            return eval(x)
            
    blockchain['in_amounts'] = blockchain['input_amounts'].apply(safe_parse)
    blockchain['out_amounts'] = blockchain['output_amounts'].apply(safe_parse)
    
    all_in = [amt for sublist in blockchain['in_amounts'] for amt in sublist]
    all_out = [amt for sublist in blockchain['out_amounts'] for amt in sublist]
    all_amts = all_in + all_out
    
    report["monetary"] = {
        "min_amount": float(min(all_amts)),
        "max_amount": float(max(all_amts)),
        "has_negative_amount": bool(any(a < 0 for a in all_amts)),
        "has_sub_satoshi": bool(any(a > 0 and a < 1e-8 for a in all_amts)),
        "has_nan_inf": bool(any(pd.isna(a) or np.isinf(a) for a in all_amts)),
        "fee_min": float(blockchain['fee_btc'].min()),
        "fee_median": float(blockchain['fee_btc'].median()),
        "fee_max": float(blockchain['fee_btc'].max())
    }
    
    # Conservation
    conservation_errors = 0
    for _, row in blockchain.iterrows():
        in_sum = sum(row['in_amounts'])
        out_sum = sum(row['out_amounts'])
        fee = row['fee_btc']
        # sum(inputs) >= sum(outputs) + fee
        if in_sum + 1e-7 < out_sum + fee:
            conservation_errors += 1
            
    report["monetary"]["conservation_errors"] = int(conservation_errors)
    
    # 2. DATA
    train_split = blockchain[blockchain['split'] == 'train']
    test_split = blockchain[blockchain['split'] == 'test']
    
    train_txids = set(train_split['txid'])
    test_txids = set(test_split['txid'])
    
    train_scenarios = set(train_split['scenario_id'])
    test_scenarios = set(test_split['scenario_id'])
    
    report["data"] = {
        "transaction_count": int(len(blockchain)),
        "scenario_count": int(blockchain['scenario_id'].nunique()),
        "duplicate_txids": int(len(blockchain) - blockchain['txid'].nunique()),
        "train_test_txid_overlap": int(len(train_txids & test_txids)),
        "train_test_scenario_overlap": int(len(train_scenarios & test_scenarios))
    }
    
    # 3. NETWORK
    report["network"] = {
        "network_record_count": int(len(network)),
        "valid_txids": bool(network['txid'].notna().all()),
        "required_fields_present": bool(all(col in network.columns for col in ['txid', 'relay_ip', 'relay_port', 'node_type', 'country_code', 'asn']))
    }
    
    # 4. CORRELATION
    ledger_txids = set(blockchain['txid'])
    network_txids = set(network['txid'])
    matched = ledger_txids & network_txids
    
    report["correlation"] = {
        "matched": int(len(matched)),
        "unmatched_ledger": int(len(ledger_txids - network_txids)),
        "unmatched_network": int(len(network_txids - ledger_txids)),
        "correlation_rate": float(len(matched) / max(len(ledger_txids), len(network_txids)) if ledger_txids else 0)
    }
    
    with open('data_quality_report_v8.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print("V8 validation complete. Saved to data_quality_report_v8.json")

if __name__ == "__main__":
    validate_v8()
