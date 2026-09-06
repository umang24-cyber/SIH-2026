import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append("/home/param/SIH-2026")
from data_pipeline.hierarchical_sampler import HierarchicalSampler

@pytest.fixture
def dummy_data():
    macro = pd.DataFrame({
        'lifespan_days': [1, 10, 100, 200, 300],
        'active_days': [1, 5, 20, 50, 100],
        'total_count': [1, 10, 50, 100, 500],
        'total_income': [1000, 5000, 20000, 50000, 100000],
        'label': ['white', 'white', 'paduaCryptoWall', 'montrealSam', 'white']
    })
    
    micro = pd.DataFrame({
        'activity_count': [1, 10, 50, 100, 500],
        'mean_transfer_amount': [1000, 500, 400, 500, 200],
        'inter_event_delta_mean': [0.0, 3600.0, 1800.0, 600.0, 60.0],
        'burstiness_B': [0.0, 0.5, 0.2, 0.8, -0.1]
    })
    
    return macro, micro

def test_initialization(dummy_data):
    macro, micro = dummy_data
    sampler = HierarchicalSampler(macro, micro)
    assert hasattr(sampler, 'bg_macro')
    assert hasattr(sampler, 'rw_macro')
    
def test_deterministic_seed(dummy_data):
    macro, micro = dummy_data
    sampler1 = HierarchicalSampler(macro, micro, random_state=42)
    sampler2 = HierarchicalSampler(macro, micro, random_state=42)
    
    p1 = sampler1.sample("background")
    p2 = sampler2.sample("background")
    
    assert p1['macro'] == p2['macro']
    assert p1['micro'] == p2['micro']
    
def test_valid_ranges(dummy_data):
    macro, micro = dummy_data
    sampler = HierarchicalSampler(macro, micro, random_state=42)
    
    p = sampler.sample("ransomware")
    assert p['macro']['lifespan_days'] >= 1
    assert p['macro']['active_days'] >= 1
    assert p['macro']['total_count'] >= 1
    assert p['macro']['total_income'] > 0
    assert 'approximations' in p
    
def test_tiny_family_fallback(dummy_data):
    macro, micro = dummy_data
    sampler = HierarchicalSampler(macro, micro, random_state=42)
    
    # montrealSam only has 1 sample (tiny)
    p = sampler.sample("ransomware", family="montrealSam")
    assert p['family'] == "pooled_ransomware"

def test_missing_fields():
    macro = pd.DataFrame({'lifespan_days': [1]})
    micro = pd.DataFrame({'activity_count': [1]})
    
    with pytest.raises(ValueError):
        HierarchicalSampler(macro, micro)
