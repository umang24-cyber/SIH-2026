"""
generate_v9.py
==============
SIH 2026 — Bitcoin AML Dataset V9 Generation Pipeline

V9 Key Design Principles (vs V8):
  1. SIZE LEAKAGE FIX: All typologies share a continuous lognormal size support
     N ∈ [5, 300]. No typology-specific floor/cap that creates deterministic
     size separation between classes.
  2. BALANCED TYPOLOGY COUNTS: Ransomware, peeling_chain, layering, and mixing
     each get exactly 560 illicit scenarios (25% of illicit total). Replaces the
     V8 imbalanced 1400/260/260/320 split.
  3. ARCHITECTURE-C ALIGNMENT: Scenarios are the ML prediction unit.
     Evidence subgraphs are generated as ground-truth localization artifacts
     and are NEVER fed back through the ML model.
  4. STANDALONE SIZE SAMPLER: Replaces HierarchicalSampler + BitcoinHeist
     real-data dependency with a pure lognormal mixture that is reproducible
     without external CSVs, and whose parameters are validated against Gate A
     size-separation prerequisites in Phase 2.

Phase 2 Status: SIZE SAMPLING COMPLETE AND GATE-A VALIDATED.
Phase 3 Status: COMPLETE — transaction content generation implemented.

Usage:
    conda activate ml
    python data_pipeline/generate_v9.py --generate        # full generation
    python data_pipeline/generate_v9.py --validate-sizes  # Gate A check only
    python data_pipeline/generate_v9.py --features        # feature engineering

V8 WARNING: data_pipeline/generate_v8.py is FROZEN. Do not modify it.
            Do not import from this file into generate_v8.py or vice versa.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

# ═══════════════════════════════════════════════════════════════════════════════
# LOCKED CONSTANTS — DO NOT CHANGE WITHOUT DESIGN REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

V9_SEED: int = 20260921

N_LICIT_SCENARIOS: int      = 3200
N_RANSOMWARE_SCENARIOS: int = 560
N_PEELING_SCENARIOS: int    = 560
N_LAYERING_SCENARIOS: int   = 560
N_MIXING_SCENARIOS: int     = 560
N_TOTAL_SCENARIOS: int      = (
    N_LICIT_SCENARIOS + N_RANSOMWARE_SCENARIOS + N_PEELING_SCENARIOS
    + N_LAYERING_SCENARIOS + N_MIXING_SCENARIOS
)
assert N_TOTAL_SCENARIOS == 5440

N_MIN: int = 5
N_MAX: int = 300
SPLIT_RATIO: float = 0.20

# Derived from train_v8.py (confirmed Phase 3 pre-flight):
# sss1 test_size=0.30, sss2 test_size=0.50 → proper=70%, eval=15%, cal=15%
PROPER_TRAIN_FRACTION: float       = 0.70
EVAL_FRACTION_OF_HOLDOUT: float    = 0.50

SATOSHIS_PER_BTC: int = 100_000_000

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "processed_v9"

# ═══════════════════════════════════════════════════════════════════════════════
# SIZE SAMPLING PARAMETERS (GATE A VALIDATED — PHASE 2, ITERATION 5)
# ═══════════════════════════════════════════════════════════════════════════════
SIZE_PARAMS: Dict = {
    "licit": {
        "retail_weight": 0.55, "retail_mu": 2.7, "retail_sigma": 0.85,
        "merchant_weight": 0.30, "merchant_mu": 3.2, "merchant_sigma": 0.75,
        "inst_mu": 3.9, "inst_sigma": 0.60,
    },
    "ransomware":    {"mu": 2.1, "sigma": 0.95},
    "peeling_chain": {"mu": 3.2, "sigma": 0.85},
    "layering":      {"mu": 3.3, "sigma": 0.85},
    "mixing":        {"mu": 3.3, "sigma": 0.85},
}


def sample_v9_scenario_size(pattern_type: str, rng: np.random.Generator) -> int:
    """Sample N ∈ [5, 300]. Phase 2 validated."""
    if pattern_type == "normal":
        lp = SIZE_PARAMS["licit"]
        rw, mw = lp["retail_weight"], lp["merchant_weight"]
        ci = int(rng.choice(3, p=[rw, mw, 1.0 - rw - mw]))
        if ci == 0:   raw = rng.lognormal(lp["retail_mu"],   lp["retail_sigma"])
        elif ci == 1: raw = rng.lognormal(lp["merchant_mu"], lp["merchant_sigma"])
        else:         raw = rng.lognormal(lp["inst_mu"],     lp["inst_sigma"])
    else:
        p = SIZE_PARAMS[pattern_type]
        raw = rng.lognormal(p["mu"], p["sigma"])
    return int(np.clip(round(raw), N_MIN, N_MAX))


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_all_wallets: set = set()
_txid_counter: int = 0
_used_txids: set = set()


def _gen_unique_wallet(rng: np.random.Generator) -> str:
    global _all_wallets
    for _ in range(200):
        length = int(rng.integers(25, 34))
        chars = rng.choice(list(BASE58_ALPHABET), size=length)
        w = "1" + "".join(chars)
        if w not in _all_wallets:
            _all_wallets.add(w); return w
    w = f"1V9U{len(_all_wallets):012d}"
    _all_wallets.add(w); return w


def _make_txid(rng: np.random.Generator) -> int:
    global _txid_counter, _used_txids
    for _ in range(100):
        _txid_counter += 1
        h = hashlib.sha256(f"v9:{_txid_counter}:{rng.integers(0,2**32)}".encode()).hexdigest()
        txid = 100_000_000 + (int(h[:8], 16) % 900_000_000)
        if txid not in _used_txids:
            _used_txids.add(txid)
            return txid
    txid = 100_000_000 + len(_used_txids) + 1
    while txid in _used_txids: txid += 1
    _used_txids.add(txid)
    return txid


def _fee_sat(rng: np.random.Generator) -> int:
    """Fee in SATOSHIS. Range 1,000–45,000 sat."""
    return int(rng.integers(1_000, 45_001))


def _amt_sat(rng: np.random.Generator) -> int:
    """Random amount in SATOSHIS from lognormal BTC distribution."""
    return int(max(rng.lognormal(-1.8, 1.4) * SATOSHIS_PER_BTC, 100))


def _distribute(total_sat: int, n: int, rng: np.random.Generator) -> List[int]:
    """Split total_sat into n parts each >= 100 sat."""
    if n == 1: return [total_sat]
    base = n * 100
    rem = total_sat - base
    fracs = rng.dirichlet(np.ones(n))
    parts = [int(rem * float(f)) for f in fracs]
    parts[-1] += rem - sum(parts)
    return [p + 100 for p in parts]


def _ts(rng: np.random.Generator, y0: int = 2013, y1: int = 2022) -> pd.Timestamp:
    s = pd.Timestamp(f"{y0}-01-01")
    e = pd.Timestamp(f"{y1}-12-31 23:59:59")
    return s + pd.Timedelta(seconds=float(rng.uniform(0, (e - s).total_seconds())))


def _script(rng: np.random.Generator) -> str:
    return str(rng.choice(["P2PKH","P2SH","P2WPKH","P2WSH"], p=[0.45,0.25,0.25,0.05]))


ASNS = ["AS3320","AS15169","AS7922","AS4134","AS1221","AS7018","AS8075",
        "AS2914","AS3257","AS6939","AS9002","AS3356","AS174","AS6147"]
COUNTRIES = ["US","DE","GB","NL","SG","JP","CN","CA","FR","AU","RU","CH"]
NODE_T = ["datacenter","residential","mobile","tor_exit_node","vpn_proxy","bulletproof_host"]
NODE_W = [0.42, 0.35, 0.10, 0.05, 0.05, 0.03]
UAS = ["/Satoshi:0.18.1/","/Satoshi:21.0.0/","/Satoshi:22.0.0/","/Satoshi:0.17.0/","/bitcore:8.25.10/"]
UA_W = [0.30, 0.25, 0.25, 0.10, 0.10]


def _net_rec(txid: int, ts: pd.Timestamp, sc_id: str, split: str,
             illicit: bool, rng: np.random.Generator) -> Dict:
    prop_ms = int(rng.integers(50, 500))
    rts = ts - pd.Timedelta(milliseconds=prop_ms)
    nt  = str(rng.choice(NODE_T, p=NODE_W))
    port = (8333 if rng.random() < 0.85 else
            int(rng.choice([18333, 9050, 8333])))
    cc  = str(rng.choice(COUNTRIES))
    asn = str(rng.choice(ASNS))
    pfx = abs(hash(asn + cc)) % 220 + 1
    ip  = f"{pfx}.{int(rng.integers(1,254))}.{int(rng.integers(1,254))}.{int(rng.integers(1,254))}"
    return {"txid": txid, "relay_timestamp": rts, "relay_ip": ip, "relay_port": port,
            "node_type": nt, "country_code": cc, "asn": asn, "isp": f"ISP_{asn}",
            "protocol_version": 70015, "user_agent": str(rng.choice(UAS, p=UA_W)),
            "scenario_id": sc_id, "split": split}


def _bc_rec(txid, ts, in_a, in_s, out_a, out_s, fee, sc, illicit, pt, sc_id, split) -> Dict:
    """Blockchain record. Validates accounting before serializing."""
    it, ot = sum(in_s), sum(out_s)
    assert fee >= 0 and it > 0 and ot > 0 and fee <= it
    assert all(s > 0 for s in in_s) and all(s > 0 for s in out_s)
    assert abs(it - ot - fee) <= 1, f"Conservation: in={it} out={ot} fee={fee}"
    return {"txid": txid, "timestamp": ts,
            "input_addresses":  json.dumps(in_a),
            "output_addresses": json.dumps(out_a),
            "input_amounts":    json.dumps([s / SATOSHIS_PER_BTC for s in in_s]),
            "output_amounts":   json.dumps([s / SATOSHIS_PER_BTC for s in out_s]),
            "fee_btc": fee / SATOSHIS_PER_BTC,
            "script_type": sc, "is_illicit": int(illicit),
            "pattern_type": pt, "scenario_id": sc_id, "split": split}


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_licit(sc_id, n, base_ts, split, rng):
    bc, net = [], []
    pool = [(_gen_unique_wallet(rng), _amt_sat(rng) * 5)]
    ts   = base_ts
    pws  = [0.40, 0.30, 0.20, 0.10]
    for _ in range(n):
        ts += pd.Timedelta(seconds=float(rng.exponential(3600)))
        sc = _script(rng)
        p  = int(rng.choice(4, p=pws))
        ia, is_, oa, os_ = [], [], [], []
        while not pool:
            pool.append((_gen_unique_wallet(rng), _amt_sat(rng)))
        if p == 0:  # chain_hop
            w, b = pool.pop(0)
            ia=[w]; is_=[b]
            f = min(_fee_sat(rng), b-100)
            ow = _gen_unique_wallet(rng); oa=[ow]; os_=[b-f]
            pool.append((ow, b-f))
        elif p == 1:  # fan_out
            w, b = pool.pop(0)
            ia=[w]; is_=[b]; no = int(rng.integers(2,7))
            mr = no*100; f = min(_fee_sat(rng), b-mr)
            if b <= mr+1000: b=mr+_amt_sat(rng); is_=[b]
            f = min(_fee_sat(rng), b-mr)
            os_ = _distribute(b-f, no, rng)
            oa  = [_gen_unique_wallet(rng) for _ in range(no)]
            for wa,sa in zip(oa,os_): pool.append((wa,sa))
        elif p == 2:  # fan_in
            ni = int(rng.integers(2,5))
            for _ in range(ni):
                if pool: w,b=pool.pop(0)
                else: w,b=_gen_unique_wallet(rng),_amt_sat(rng)
                ia.append(w); is_.append(b)
            it=sum(is_);
            if it<200: is_=[max(s,200) for s in is_]; it=sum(is_)
            f=min(_fee_sat(rng),it-100)
            ow=_gen_unique_wallet(rng); oa=[ow]; os_=[it-f]
            pool.append((ow,it-f))
        else:  # change-return
            for _ in range(2):
                if pool: w,b=pool.pop(0)
                else: w,b=_gen_unique_wallet(rng),_amt_sat(rng)
                ia.append(w); is_.append(b)
            it=sum(is_); f=min(_fee_sat(rng),it-200)
            os_=_distribute(it-f,2,rng)
            oa=[_gen_unique_wallet(rng),_gen_unique_wallet(rng)]
            for wa,sa in zip(oa,os_): pool.append((wa,sa))
        txid=_make_txid(rng)
        bc.append(_bc_rec(txid,ts,ia,is_,oa,os_,int(sum(is_)-sum(os_)),sc,False,"normal",sc_id,split))
        net.append(_net_rec(txid,ts,sc_id,split,False,rng))
    return bc, net


def _gen_ransomware(sc_id, n, base_ts, split, rng):
    bc, net = [], []
    attacker = [(_gen_unique_wallet(rng), 0)]
    ts = base_ts
    for _ in range(n):
        ts += pd.Timedelta(seconds=float(rng.exponential(7200)))
        sc = _script(rng)
        if rng.random() < 0.65:  # fan_in victims
            nv = int(rng.integers(1,4))
            ia, is_ = [], []
            for _ in range(nv):
                if rng.random() < 0.2: # multi-input victim
                    ia.extend([_gen_unique_wallet(rng), _gen_unique_wallet(rng)])
                    is_.extend([_amt_sat(rng), _amt_sat(rng)])
                else:
                    ia.append(_gen_unique_wallet(rng))
                    is_.append(_amt_sat(rng)*2)
            
            it=sum(is_); f=min(_fee_sat(rng),it-100)
            
            # Victim change
            oa, os_ = [], []
            if rng.random() < 0.70 and (it-f) > 500:
                vic_chg = int((it-f) * rng.uniform(0.1, 0.4))
                vic_chg = max(100, vic_chg)
                oa.append(_gen_unique_wallet(rng)); os_.append(vic_chg)
            else:
                vic_chg = 0
                
            ow=_gen_unique_wallet(rng); oa.append(ow); os_.append(it-f-vic_chg)
            attacker.append((ow,it-f-vic_chg))
        else:  # chain_hop
            if attacker:
                w,b=attacker.pop(0)
                if b<200: b=_amt_sat(rng)
                ia=[w]; is_=[b]
                # Attacker consolidation
                if attacker and rng.random() < 0.30:
                    w2,b2 = attacker.pop(0)
                    ia.append(w2); is_.append(b2)
                    b += b2
            else:
                w,b=_gen_unique_wallet(rng),_amt_sat(rng)
                ia=[w]; is_=[b]
                
            f=min(_fee_sat(rng),b-100)
            ow=_gen_unique_wallet(rng); oa=[ow]; os_=[b-f]
            attacker.append((ow,b-f))
        txid=_make_txid(rng)
        bc.append(_bc_rec(txid,ts,ia,is_,oa,os_,int(sum(is_)-sum(os_)),sc,True,"ransomware",sc_id,split))
        net.append(_net_rec(txid,ts,sc_id,split,True,rng))
    return bc, net


def _gen_peeling(sc_id, n, base_ts, split, rng):
    bc, net = [], []
    cw = _gen_unique_wallet(rng)
    cb = _amt_sat(rng) * 3
    ts = base_ts
    for _ in range(n):
        ts += pd.Timedelta(seconds=float(rng.exponential(1800)))
        sc = _script(rng)
        if cb < 300: cb = _amt_sat(rng) + 1000
        
        if rng.random() < 0.20:
            ia=[cw, _gen_unique_wallet(rng)]
            extra = _amt_sat(rng)
            is_=[cb, extra]
            cb += extra
        else:
            ia=[cw]; is_=[cb]
            
        f=min(_fee_sat(rng),cb-200); rem=cb-f
        pf=float(rng.uniform(0.30,0.70))
        ps=max(100,int(rem*pf)); cs=rem-ps
        if cs<100: cs=100; ps=rem-100
        
        oa = []
        os_ = []
        if rng.random() < 0.15 and ps >= 200:
            ps1 = max(100, int(ps*0.5))
            ps2 = ps - ps1
            oa.extend([_gen_unique_wallet(rng), _gen_unique_wallet(rng)])
            os_.extend([ps1, ps2])
            pw = oa[0]
        else:
            pw=_gen_unique_wallet(rng)
            oa.append(pw); os_.append(ps)
            
        if rng.random() < 0.10 and _all_wallets:
            chw = str(rng.choice(list(_all_wallets)))
        else:
            chw=_gen_unique_wallet(rng)
            
        oa.append(chw); os_.append(cs)
        cw=pw; cb=os_[0]
        txid=_make_txid(rng)
        bc.append(_bc_rec(txid,ts,ia,is_,oa,os_,f,sc,True,"peeling_chain",sc_id,split))
        net.append(_net_rec(txid,ts,sc_id,split,True,rng))
    return bc, net


def _gen_layering(sc_id, n, base_ts, split, rng):
    bc, net = [], []
    pool = [(_gen_unique_wallet(rng),_amt_sat(rng)) for _ in range(int(rng.integers(2,5)))]
    ts = base_ts; rn = 0
    for _ in range(n):
        ts += pd.Timedelta(seconds=float(rng.exponential(2400)))
        sc = _script(rng); rn += 1
        if not pool: pool=[(_gen_unique_wallet(rng),_amt_sat(rng))]
        ia, is_, oa, os_ = [], [], [], []
        
        psize = len(pool)
        if psize < 2:
            probs = [0.80, 0.10, 0.10]
        elif psize > 6:
            probs = [0.10, 0.80, 0.10]
        else:
            probs = [0.40, 0.40, 0.20]
            
        action = rng.choice(["fan_out", "fan_in", "chain"], p=probs)
        
        if action == "fan_out":
            w,b=pool.pop(0)
            if b<500: b=_amt_sat(rng)
            ia=[w]; is_=[b]; no=int(rng.integers(2,6)); mr=no*100
            f=min(_fee_sat(rng),b-mr)
            os_=_distribute(b-f,no,rng); oa=[_gen_unique_wallet(rng) for _ in range(no)]
            for wa,sa in zip(oa,os_): pool.append((wa,sa))
        elif action == "fan_in":
            ni=min(int(rng.integers(2,5)),len(pool)) or 1
            for _ in range(ni):
                if pool: w,b=pool.pop(0)
                else: w,b=_gen_unique_wallet(rng),_amt_sat(rng)
                ia.append(w); is_.append(b)
            it=sum(is_)
            if it<200: it=200; is_=[it]
            f=min(_fee_sat(rng),it-100)
            ow=_gen_unique_wallet(rng); oa=[ow]; os_=[it-f]; pool.append((ow,it-f))
        else:
            w,b=pool.pop(0)
            ia=[w]; is_=[b]; f=min(_fee_sat(rng), b-100)
            ow=_gen_unique_wallet(rng); oa=[ow]; os_=[b-f]; pool.append((ow,b-f))
        fee=int(sum(is_)-sum(os_)); fee=max(0,fee)
        txid=_make_txid(rng)
        bc.append(_bc_rec(txid,ts,ia,is_,oa,os_,fee,sc,True,"layering",sc_id,split))
        net.append(_net_rec(txid,ts,sc_id,split,True,rng))
    return bc, net


def _gen_mixing(sc_id, n, base_ts, split, rng):
    bc, net = [], []
    ts = base_ts
    denoms = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 50_000_000]
    for _ in range(n):
        ts += pd.Timedelta(seconds=float(rng.exponential(3600)))
        sc = _script(rng)
        p  = rng.choice(["cj","setup","disp"], p=[0.60,0.20,0.20])
        ia, is_, oa, os_ = [], [], [], []
        if p == "cj":
            np_ = int(rng.integers(3,9))
            dm  = int(rng.choice(denoms))
            ia, is_, oa, os_ = [], [], [], []
            for _ in range(np_):
                ia.append(_gen_unique_wallet(rng))
                is_.append(dm + int(rng.integers(0, dm//10)))
                
            it  = sum(is_)
            f_per = min(_fee_sat(rng), dm-100)
            
            for i in range(np_):
                oa.append(_gen_unique_wallet(rng))
                os_.append(dm - f_per)
                
                chg = is_[i] - dm
                if chg > 100:
                    oa.append(_gen_unique_wallet(rng))
                    os_.append(chg)
                    
            ot  = sum(os_)
            fee = max(0, it - ot)
        elif p == "setup":
            ni=int(rng.integers(2,5)); ia=[_gen_unique_wallet(rng) for _ in range(ni)]
            is_=[_amt_sat(rng) for _ in range(ni)]; it=sum(is_)
            f=min(_fee_sat(rng),it-100)
            ow=_gen_unique_wallet(rng); oa=[ow]; os_=[it-f]; fee=f
        else:
            w=_gen_unique_wallet(rng); b=_amt_sat(rng)*3; ia=[w]; is_=[b]
            no=int(rng.integers(3,8)); mr=no*100; f=min(_fee_sat(rng),b-mr)
            os_=_distribute(b-f,no,rng); oa=[_gen_unique_wallet(rng) for _ in range(no)]
            fee=int(b-sum(os_)); fee=max(0,fee)
        # Final guard
        os_=[max(100,s) for s in os_]
        fee=max(0,int(sum(is_)-sum(os_)))
        txid=_make_txid(rng)
        bc.append(_bc_rec(txid,ts,ia,is_,oa,os_,fee,sc,True,"mixing",sc_id,split))
        net.append(_net_rec(txid,ts,sc_id,split,True,rng))
    return bc, net


# ═══════════════════════════════════════════════════════════════════════════════
# GATE A REAL-DATA REVALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_gate_a_on_meta(meta_df: pd.DataFrame) -> None:
    from scipy import stats as sp
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import roc_auc_score, average_precision_score
    from sklearn.feature_selection import mutual_info_classif

    sz = meta_df["n_txns"].values
    lb = meta_df["is_illicit"].values
    lit = meta_df[meta_df["is_illicit"]==0]["n_txns"].values
    ill = meta_df[meta_df["is_illicit"]==1]["n_txns"].values

    bins=np.arange(N_MIN,N_MAX+2)
    ha,_=np.histogram(lit,bins=bins,density=True)
    hb,_=np.histogram(ill,bins=bins,density=True)
    ovl=float(np.sum(np.minimum(ha,hb)))
    ks,_=sp.ks_2samp(lit,ill)
    dt=DecisionTreeClassifier(max_depth=3,random_state=V9_SEED)
    dt.fit(sz.reshape(-1,1),lb)
    pr=dt.predict_proba(sz.reshape(-1,1))[:,1]
    auc=float(roc_auc_score(lb,pr)); prauc=float(average_precision_score(lb,pr))
    sb=np.digitize(sz,bins=[5,7,16,41,81,151,301]).reshape(-1,1)
    mi=float(mutual_info_classif(sb,lb,discrete_features=True,random_state=V9_SEED)[0])

    gates={"OVL":(ovl,">=",0.75),"KS":(ks,"<=",0.20),
           "AUC_1D":(auc,"<=",0.58),"PRAUC_1D":(prauc,"<=",0.45),"MI":(mi,"<=",0.01)}
    print("\n  Gate A re-validation (real num_txns from generated data):")
    fail=False
    for k,(v,op,thr) in gates.items():
        ok=(v>=thr) if op==">=" else (v<=thr)
        print(f"    {k:<12} {v:>8.4f}  target {op}{thr}  {'PASS' if ok else 'FAIL'}")
        if not ok: fail=True
    print(f"\n  Gate A overall: {'ALL PASS' if not fail else 'SOME FAIL'}")
    if fail:
        raise RuntimeError("Gate A failed on real generated data. Do not proceed to feature engineering.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_v9_dataset(output_dir: str = str(OUT_DIR)) -> str:
    global _all_wallets, _txid_counter
    _all_wallets = set(); _txid_counter = 0

    out = Path(output_dir)
    assert "processed_v9" in str(out) or "test" in str(out), \
        f"SAFETY: output must contain 'processed_v9', got {out}"
    out.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(V9_SEED)
    random.seed(V9_SEED)
    print(f"[V9] Seed={V9_SEED} | Output={out} | Scenarios={N_TOTAL_SCENARIOS}")

    # Scenario list
    counts = {"normal":N_LICIT_SCENARIOS,"ransomware":N_RANSOMWARE_SCENARIOS,
              "peeling_chain":N_PEELING_SCENARIOS,"layering":N_LAYERING_SCENARIOS,
              "mixing":N_MIXING_SCENARIOS}
    meta = []
    sc_num = 0
    for pt, cnt in counts.items():
        for _ in range(cnt):
            sc_num += 1
            n = sample_v9_scenario_size(pt, rng)
            meta.append((f"{pt}_{sc_num:05d}", pt, n))

    # Stratified train/test split
    labels_arr = [0 if m[1]=="normal" else 1 for m in meta]
    ids_arr    = [m[0] for m in meta]
    sss = StratifiedShuffleSplit(n_splits=1, test_size=SPLIT_RATIO, random_state=V9_SEED)
    idx_tr, idx_te = next(sss.split(np.zeros(N_TOTAL_SCENARIOS), labels_arr))
    split_map = {ids_arr[i]: "train" for i in idx_tr}
    split_map.update({ids_arr[i]: "test" for i in idx_te})
    print(f"  Train={len(idx_tr)}, Test={len(idx_te)}")

    # Generate
    gen = {"normal":_gen_licit,"ransomware":_gen_ransomware,
           "peeling_chain":_gen_peeling,"layering":_gen_layering,"mixing":_gen_mixing}
    bc_all, net_all, meta_rows = [], [], []
    for i, (sc_id, pt, n_txns) in enumerate(meta):
        if i % 500 == 0:
            print(f"  {i+1}/{N_TOTAL_SCENARIOS} — {sc_id} ({pt}, N={n_txns})")
        sp = split_map[sc_id]
        bts = _ts(rng)
        bc_recs, net_recs = gen[pt](sc_id, n_txns, bts, sp, rng)
        bc_all.extend(bc_recs); net_all.extend(net_recs)
        meta_rows.append({"scenario_id":sc_id,"pattern_type":pt,
                          "is_illicit":0 if pt=="normal" else 1,
                          "n_txns":len(bc_recs),"split":sp})

    print(f"  BC records: {len(bc_all):,} | Net records: {len(net_all):,}")

    # Accounting invariant checks
    print("\n  Accounting invariant checks...")
    bc_df = pd.DataFrame(bc_all)
    def _parse(col): return bc_df[col].apply(json.loads)
    bc_df["_it"] = _parse("input_amounts").apply(lambda x: round(sum(x)*SATOSHIS_PER_BTC))
    bc_df["_ot"] = _parse("output_amounts").apply(lambda x: round(sum(x)*SATOSHIS_PER_BTC))
    bc_df["_fs"] = bc_df["fee_btc"].apply(lambda x: round(x*SATOSHIS_PER_BTC))
    checks = {
        "neg_input_total":  (bc_df["_it"]<=0).sum(),
        "neg_output_total": (bc_df["_ot"]<=0).sum(),
        "neg_fee":          (bc_df["_fs"]<0).sum(),
        "fee_gt_input":     (bc_df["_fs"]>bc_df["_it"]).sum(),
        "nan_values":       bc_df[["fee_btc"]].isna().sum().sum(),
        "conservation_fail":(((bc_df["_it"]-bc_df["_ot"]-bc_df["_fs"]).abs())>2).sum(),
    }
    for k,v in checks.items():
        print(f"    {k:<25}: {v}  (expected 0)")
        if v > 0:
            raise RuntimeError(f"Accounting invariant violated: {k}={v}")
    bc_df = bc_df.drop(columns=["_it","_ot","_fs"])

    # Gate A re-validation
    meta_df = pd.DataFrame(meta_rows)
    _validate_gate_a_on_meta(meta_df)

    # Write CSVs
    print("\n  Writing CSVs...")
    net_df = pd.DataFrame(net_all)
    for sp in ["train","test"]:
        sp_ids = {sid for sid,s in split_map.items() if s==sp}
        bc_df[bc_df["scenario_id"].isin(sp_ids)].to_csv(out/f"{sp}_blockchain.csv", index=False)
        net_df[net_df["scenario_id"].isin(sp_ids)].to_csv(out/f"{sp}_network.csv", index=False)
        lbl = meta_df[meta_df["split"]==sp][["scenario_id","is_illicit","pattern_type","n_txns"]]
        lbl.to_csv(out/f"scenario_labels_{sp}.csv", index=False)
        print(f"    {sp}: BC={len(bc_df[bc_df['scenario_id'].isin(sp_ids)]):,}  "
              f"Net={len(net_df[net_df['scenario_id'].isin(sp_ids)]):,}  Labels={len(lbl)}")

    # TXID/Scenario overlap check
    print("\n  Zero-overlap check...")
    tr_ids = set(pd.read_csv(out/"train_blockchain.csv",usecols=["txid"])["txid"])
    te_ids = set(pd.read_csv(out/"test_blockchain.csv", usecols=["txid"])["txid"])
    tr_sc  = set(pd.read_csv(out/"train_blockchain.csv",usecols=["scenario_id"])["scenario_id"])
    te_sc  = set(pd.read_csv(out/"test_blockchain.csv", usecols=["scenario_id"])["scenario_id"])
    txid_ovlp  = len(tr_ids & te_ids)
    scen_ovlp  = len(tr_sc & te_sc)
    print(f"    TXID overlap:     {txid_ovlp}  (expected 0)")
    print(f"    Scenario overlap: {scen_ovlp}  (expected 0)")
    assert txid_ovlp == 0 and scen_ovlp == 0

    print("\n[V9] Generation complete.")
    return str(out)


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════

def run_feature_engineering(data_dir: str = str(OUT_DIR)) -> None:
    data = Path(data_dir)
    assert "processed_v9" in str(data) or "test" in str(data)

    sys.path.insert(0, str(ROOT))
    import importlib
    ml_02  = importlib.import_module("ml.02_feature_engineering")
    ml_02b = importlib.import_module("ml.02b_graph_features")
    compute_scenario_features = ml_02.compute_scenario_features
    load_and_join = ml_02.load_and_join
    compute_graph_features = ml_02b.compute_graph_features

    encoder = {}
    for split_name in ["train","test"]:
        print(f"\n  Feature engineering: {split_name}")
        df = load_and_join(data/f"{split_name}_blockchain.csv",
                           data/f"{split_name}_network.csv")

        ph1_rows = []
        for sc_id, grp in df.groupby("scenario_id"):
            feat = compute_scenario_features(grp)
            feat.update({"scenario_id": sc_id,
                         "_is_illicit": int(grp["is_illicit"].iloc[0]),
                         "_pattern_type": grp["pattern_type"].iloc[0]})
            ph1_rows.append(feat)
        feat_df = pd.DataFrame(ph1_rows)

        gr_rows = []
        for sc_id, grp in df.groupby("scenario_id"):
            gf = compute_graph_features(grp)
            gf.pop("_cycle_detected", None)
            gf["scenario_id"] = sc_id
            gr_rows.append(gf)
        graph_df = pd.DataFrame(gr_rows)

        if split_name == "train":
            all_types = sorted(feat_df["_script_type_mode_raw"].unique())
            encoder   = {t: i for i, t in enumerate(all_types)}
            with open(data/"script_type_encoder.json","w") as f:
                json.dump(encoder, f, indent=2)
        feat_df["script_type_mode"] = feat_df["_script_type_mode_raw"].map(encoder)

        label_meta = {"scenario_id","_is_illicit","_pattern_type","_script_type_mode_raw"}
        fc = [c for c in feat_df.columns if c not in label_meta]
        merged = feat_df[["scenario_id"]+fc].merge(graph_df, on="scenario_id", how="left")

        degen = {"degree_assortativity","avg_clustering","max_chain_length",
                 "graph_density","edge_to_node_ratio","max_in_degree","max_out_degree"}
        for col in merged.columns[merged.isnull().any()]:
            if col in degen:
                print(f"    Filling NaN in '{col}' (graph-degenerate)")
                merged[col] = merged[col].fillna(0)
            else:
                raise RuntimeError(f"Unexpected NaN in '{col}'")
        assert merged.isnull().sum().sum() == 0

        merged.to_csv(data/f"scenario_features_full_{split_name}.csv", index=False)
        feat_df[["scenario_id","_is_illicit","_pattern_type"]].rename(
            columns={"_is_illicit":"is_illicit","_pattern_type":"pattern_type"}
        ).to_csv(data/f"scenario_labels_{split_name}_full.csv", index=False)
        print(f"    {split_name}: {merged.shape[0]} rows, {merged.shape[1]} columns")
    print("\n  Feature engineering complete.")


# ═══════════════════════════════════════════════════════════════════════════════
# Gate A standalone (Phase 2 preserved)
# ═══════════════════════════════════════════════════════════════════════════════

def _monte_carlo_size_check(seed: int = V9_SEED) -> Dict:
    from scipy import stats as sp
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import roc_auc_score, average_precision_score
    from sklearn.feature_selection import mutual_info_classif

    rng = np.random.default_rng(seed)
    counts = {"normal":N_LICIT_SCENARIOS,"ransomware":N_RANSOMWARE_SCENARIOS,
              "peeling_chain":N_PEELING_SCENARIOS,"layering":N_LAYERING_SCENARIOS,
              "mixing":N_MIXING_SCENARIOS}
    by_type = {pt: np.array([sample_v9_scenario_size(pt,rng) for _ in range(c)])
               for pt,c in counts.items()}
    sz = np.concatenate([by_type[k] for k in counts])
    lb = np.concatenate([np.zeros(N_LICIT_SCENARIOS,int),
                         np.ones(N_TOTAL_SCENARIOS-N_LICIT_SCENARIOS,int)])
    lit=by_type["normal"]
    ill=np.concatenate([by_type[k] for k in ["ransomware","peeling_chain","layering","mixing"]])
    bins=np.arange(N_MIN,N_MAX+2)
    ha,_=np.histogram(lit,bins=bins,density=True); hb,_=np.histogram(ill,bins=bins,density=True)
    ovl=float(np.sum(np.minimum(ha,hb))); ks,_=sp.ks_2samp(lit,ill)
    dt=DecisionTreeClassifier(max_depth=3,random_state=seed)
    dt.fit(sz.reshape(-1,1),lb)
    pr=dt.predict_proba(sz.reshape(-1,1))[:,1]
    auc=float(roc_auc_score(lb,pr)); prauc=float(average_precision_score(lb,pr))
    sb=np.digitize(sz,bins=[5,7,16,41,81,151,301]).reshape(-1,1)
    mi=float(mutual_info_classif(sb,lb,discrete_features=True,random_state=seed)[0])
    results={"OVL":{"value":ovl,"target":0.75,"op":"ge","pass":ovl>=0.75},
             "KS":{"value":ks,"target":0.20,"op":"le","pass":ks<=0.20},
             "AUC_1D":{"value":auc,"target":0.58,"op":"le","pass":auc<=0.58},
             "PRAUC_1D":{"value":prauc,"target":0.45,"op":"le","pass":prauc<=0.45},
             "MI":{"value":mi,"target":0.01,"op":"le","pass":mi<=0.01}}
    results["all_pass"]=all(v["pass"] for v in results.values() if isinstance(v,dict))
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--validate-sizes", action="store_true")
    p.add_argument("--generate",       action="store_true")
    p.add_argument("--features",       action="store_true")
    p.add_argument("--output-dir", default=str(OUT_DIR))
    args = p.parse_args()

    if args.validate_sizes:
        print(f"Gate A validation (seed={V9_SEED})...")
        res = _monte_carlo_size_check()
        for k,v in res.items():
            if k=="all_pass": continue
            op=">=" if v["op"]=="ge" else "<="
            print(f"  {k:<12} {v['value']:>8.4f}  target {op}{v['target']}  {'PASS' if v['pass'] else 'FAIL'}")
        print(f"\n  OVERALL: {'ALL PASS' if res['all_pass'] else 'SOME FAIL'}")
        sys.exit(0 if res["all_pass"] else 1)
    elif args.generate:
        generate_v9_dataset(output_dir=args.output_dir)
    elif args.features:
        run_feature_engineering(data_dir=args.output_dir)
    else:
        p.print_help()
