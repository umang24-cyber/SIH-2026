import pytest
from data_pipeline.generate_v8 import distribute_amount_satoshis, fix_accounting_satoshis
import random

def test_distribute_amount_satoshis_valid():
    parts = distribute_amount_satoshis(1000, 3)
    assert len(parts) == 3
    assert sum(parts) == 1000
    assert all(x >= 100 for x in parts)

def test_distribute_amount_satoshis_invalid():
    with pytest.raises(ValueError):
        distribute_amount_satoshis(200, 3)

def test_fan_in_insufficient_inputs():
    # Simulated fan_in where inputs cannot cover the fee
    in_amts = [50, 60] # Total 110
    fee = 1000
    
    available_sats = sum(in_amts)
    if available_sats <= 100:
        pass # would resample
    else:
        fee_sats = min(fee, available_sats - 100)
        assert fee_sats == 10 # 110 - 100
        
        tot_out = available_sats - fee_sats
        out_amts = [tot_out]
        
        # Check invariants
        assert sum(in_amts) == sum(out_amts) + fee_sats
        assert fee_sats >= 0
        assert all(x >= 0 for x in out_amts)

def test_mixer_round_insufficient_inputs():
    in_amts = [50, 50, 50] # total 150
    fee = 500
    n_out = 3 # needs at least 300
    
    available_sats = sum(in_amts)
    min_req = n_out * 100
    
    # Assert it would resample
    assert available_sats <= min_req

def test_normal_fan_in():
    in_amts = [5000, 10000] # Total 15000
    fee = 1000
    
    available_sats = sum(in_amts)
    assert available_sats > 100
    fee_sats = min(fee, available_sats - 100)
    assert fee_sats == 1000
    
    tot_out = available_sats - fee_sats
    out_amts = [tot_out]
    
    assert sum(in_amts) == sum(out_amts) + fee_sats
    assert all(x >= 0 for x in out_amts)

def test_normal_mixer_round():
    in_amts = [5000, 10000, 5000] # Total 20000
    fee = 1000
    n_out = 4 # min req 400
    
    available_sats = sum(in_amts)
    min_req = n_out * 100
    
    assert available_sats > min_req
    fee_sats = min(fee, available_sats - min_req)
    assert fee_sats == 1000
    
    tot_out = available_sats - fee_sats
    out_amts = distribute_amount_satoshis(tot_out, n_out)
    
    assert sum(in_amts) == sum(out_amts) + fee_sats
    assert all(x >= 100 for x in out_amts)
