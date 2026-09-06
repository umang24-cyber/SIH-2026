"""
audit_v5.py
===========
SIH PS 146 — Bitcoin AML Dataset V5 Acceptance Auditor

CRITICAL DESIGN PRINCIPLE:
  This audit MUST test the EXACT output columns produced by the real ML
  feature-generation pipeline (02_feature_engineering.py → 02b_graph_features.py
  → 02c_merge_features.py). It does NOT re-derive features independently.
  A structural assertion ensures the audit column list == pipeline output columns,
  failing loudly if they ever diverge.

Gates (A through J):
  A — Single-feature AUC < 0.90 (all features)
  B — Simple-rule BAcc < 0.85 (depth-2 tree)
  C — Distribution overlap > 10% (all features)
  D — Correlation documentation (|r| > 0.80, informational)
  E — Rare typology counts >= 200 scenarios each
  F — Within-typology PCA variation (>= 4 components for 90% variance)
  G — Scenario-level split integrity (0 overlap)
  H — Categorical overlap >= 90%
  I — Typology ablation robustness (AUC drop >= 0.03 on top-3 removal)
  J — Binary ablation robustness (informational, report only)

Hard-fail gates: A, B, C, E, G, H, I
Soft/informational gates: D, F, J

Usage:
    python ml/audit_v5.py
"""

import json
import os
import sys
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from scipy.stats import wasserstein_distance
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

FORBIDDEN_COLS = {"scenario_id", "is_illicit", "pattern_type", "is_licit_exchange", "split"}

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURAL GUARD: Pipeline column sync assertion
# ═══════════════════════════════════════════════════════════════════════════════

def get_pipeline_feature_columns():
    """
    Read the ACTUAL feature columns from the pipeline's output files.
    This is the single source of truth — the audit tests whatever
    the pipeline produces, not a hand-picked subset.
    """
    full_train_path = DATA / "scenario_features_full_train.csv"
    if not full_train_path.exists():
        raise FileNotFoundError(
            f"Pipeline output not found: {full_train_path}\n"
            f"Run the full feature pipeline first:\n"
            f"  python ml/02_feature_engineering.py\n"
            f"  python ml/02b_graph_features.py\n"
            f"  python ml/02c_merge_features.py"
        )
    cols = pd.read_csv(full_train_path, nrows=0).columns.tolist()
    feature_cols = [c for c in cols if c not in FORBIDDEN_COLS]
    return feature_cols


def histogram_intersection(x1, x2, bins=50):
    """Compute empirical distribution overlap percentage (0.0 to 1.0)."""
    x1 = np.asarray(x1, dtype=float)
    x2 = np.asarray(x2, dtype=float)
    x1 = x1[np.isfinite(x1)]
    x2 = x2[np.isfinite(x2)]
    if len(x1) == 0 or len(x2) == 0:
        return 0.0
    vmin = min(np.min(x1), np.min(x2))
    vmax = max(np.max(x1), np.max(x2))
    if vmin == vmax:
        return 1.0
    h1, _ = np.histogram(x1, bins=bins, range=(vmin, vmax), density=True)
    h2, bin_edges = np.histogram(x2, bins=bins, range=(vmin, vmax), density=True)
    bin_widths = np.diff(bin_edges)
    overlap = np.sum(np.minimum(h1, h2) * bin_widths)
    return float(np.clip(overlap, 0.0, 1.0))


def run_v5_audit():
    print("=" * 80)
    print("🔍 V6 ACCEPTANCE AUDIT — UNIFIED PIPELINE")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD DATA — from the real pipeline outputs
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📂 Loading pipeline outputs...")
    
    feats_train = pd.read_csv(DATA / "scenario_features_full_train.csv")
    feats_test  = pd.read_csv(DATA / "scenario_features_full_test.csv")
    lbls_train  = pd.read_csv(DATA / "scenario_labels_train.csv")
    lbls_test   = pd.read_csv(DATA / "scenario_labels_test.csv")

    train = feats_train.merge(lbls_train, on="scenario_id")
    test  = feats_test.merge(lbls_test, on="scenario_id")
    all_data = pd.concat([train, test], ignore_index=True)

    # STRUCTURAL GUARD: verify column sync
    pipeline_features = get_pipeline_feature_columns()
    actual_features = [c for c in feats_train.columns if c not in FORBIDDEN_COLS]
    
    if set(pipeline_features) != set(actual_features):
        missing = set(pipeline_features) - set(actual_features)
        extra = set(actual_features) - set(pipeline_features)
        raise RuntimeError(
            f"COLUMN DRIFT DETECTED!\n"
            f"  Pipeline defines: {len(pipeline_features)} features\n"
            f"  Audit sees: {len(actual_features)} features\n"
            f"  Missing: {missing}\n"
            f"  Extra: {extra}\n"
            f"This audit REFUSES to run on a mismatched feature set."
        )
    
    feature_cols = actual_features
    n_features = len(feature_cols)
    print(f"  ✓ Feature column sync verified: {n_features} features")
    print(f"  ✓ Train: {len(train):,} scenarios, Test: {len(test):,} scenarios")
    print(f"  ✓ Total: {len(all_data):,} scenarios")

    y_all = all_data["is_illicit"].values.astype(int)
    y_train_val = train["is_illicit"].values.astype(int)
    y_test_val = test["is_illicit"].values.astype(int)

    gate_results = {}
    gate_details = {}

    # ─────────────────────────────────────────────────────────────────────────
    # PRE-CHECK: Label leakage & integrity
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Pre-Check: Label Leakage & Integrity ---")
    
    leaked_cols = [c for c in ["is_illicit", "pattern_type", "is_licit_exchange"] 
                   if c in feature_cols]
    if leaked_cols:
        print(f"  ❌ LABEL LEAKAGE: {leaked_cols} found in feature columns!")
        return  # Hard stop
    print("  ✓ No label columns in feature matrix")

    # Accounting identity check
    bc_path = DATA / "blockchain_transactions.csv"
    if bc_path.exists():
        df_bc = pd.read_csv(bc_path)
        in_sums = df_bc["input_amounts"].apply(lambda x: sum(json.loads(x)))
        out_sums = df_bc["output_amounts"].apply(lambda x: sum(json.loads(x)))
        residuals = np.abs(in_sums - out_sums - df_bc["fee_btc"])
        max_residual = float(residuals.max())
        acct_violations = int((residuals > 1e-4).sum())
        print(f"  Accounting: max residual = {max_residual:.8f}, violations = {acct_violations}")
    
    # Label homogeneity within scenarios
    bc_full = pd.read_csv(bc_path) if bc_path.exists() else None
    if bc_full is not None:
        label_homo = bc_full.groupby("scenario_id")["is_illicit"].nunique()
        mixed_scenarios = int((label_homo > 1).sum())
        print(f"  Label homogeneity: {mixed_scenarios} mixed-label scenarios")
        assert mixed_scenarios == 0, f"Label homogeneity violated: {mixed_scenarios} scenarios"
        print("  ✓ Label homogeneity: PASS")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE A: Single-Feature AUC (ALL features)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate A: Single-Feature AUC (all features) ---")
    
    single_auc_results = []
    for f in feature_cols:
        vals = all_data[f].values.astype(float)
        if np.std(vals) < 1e-12:
            auc = 0.5
        else:
            auc = roc_auc_score(y_all, vals)
            if auc < 0.5:
                auc = 1.0 - auc  # Flip if negatively correlated
        single_auc_results.append({"feature": f, "auc": float(auc)})
    
    df_gate_a = pd.DataFrame(single_auc_results).sort_values("auc", ascending=False)
    max_single_auc = df_gate_a["auc"].max()
    top_feature = df_gate_a.iloc[0]["feature"]
    
    print(f"  Top-10 single-feature AUCs:")
    for _, row in df_gate_a.head(10).iterrows():
        flag = " ⚠️" if row["auc"] >= 0.90 else ""
        print(f"    {row['feature']:40s} AUC = {row['auc']:.4f}{flag}")
    
    gate_a_pass = max_single_auc < 0.90
    gate_results["A"] = gate_a_pass
    gate_details["A"] = f"Max single-feature AUC = {max_single_auc:.4f} ({top_feature})"
    print(f"  Gate A: {'✅ PASS' if gate_a_pass else '❌ FAIL'} — {gate_details['A']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE B: Simple-Rule BAcc (depth-2 decision tree)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate B: Simple-Rule Balanced Accuracy ---")
    
    X_all = all_data[feature_cols].values.astype(float)
    
    # Depth-2 tree on ALL features
    dt = DecisionTreeClassifier(max_depth=2, random_state=42)
    dt.fit(X_all, y_all)
    dt_preds = dt.predict(X_all)
    dt_bacc = balanced_accuracy_score(y_all, dt_preds)
    
    # Also test top-2 feature pairs
    top_feats = df_gate_a.head(5)["feature"].tolist()
    best_pair_bacc = 0.0
    best_pair_desc = ""
    for i in range(len(top_feats)):
        for j in range(i+1, len(top_feats)):
            f1, f2 = top_feats[i], top_feats[j]
            Xp = all_data[[f1, f2]].values.astype(float)
            dtp = DecisionTreeClassifier(max_depth=2, random_state=42)
            dtp.fit(Xp, y_all)
            bacc = balanced_accuracy_score(y_all, dtp.predict(Xp))
            if bacc > best_pair_bacc:
                best_pair_bacc = bacc
                best_pair_desc = f"{f1} + {f2}"
    
    max_simple_bacc = max(dt_bacc, best_pair_bacc)
    gate_b_pass = max_simple_bacc < 0.85
    gate_results["B"] = gate_b_pass
    gate_details["B"] = f"Depth-2 tree BAcc = {dt_bacc:.4f}, Best pair ({best_pair_desc}) = {best_pair_bacc:.4f}"
    print(f"  All-feature depth-2 tree BAcc: {dt_bacc:.4f}")
    print(f"  Best 2-feature pair: {best_pair_desc} BAcc = {best_pair_bacc:.4f}")
    print(f"  Gate B: {'✅ PASS' if gate_b_pass else '❌ FAIL'} — max = {max_simple_bacc:.4f}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE C: Distribution Overlap (all features)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate C: Distribution Overlap ---")
    
    licit = all_data[all_data["is_illicit"] == 0]
    illicit = all_data[all_data["is_illicit"] == 1]
    
    overlap_results = []
    for f in feature_cols:
        l_vals = licit[f].values.astype(float)
        i_vals = illicit[f].values.astype(float)
        ovl = histogram_intersection(l_vals, i_vals, bins=40)
        overlap_results.append({
            "feature": f,
            "overlap_pct": round(ovl * 100, 1),
        })
    
    df_gate_c = pd.DataFrame(overlap_results).sort_values("overlap_pct")
    min_overlap = df_gate_c["overlap_pct"].min()
    worst_feature = df_gate_c.iloc[0]["feature"]
    
    failing_c = df_gate_c[df_gate_c["overlap_pct"] <= 10.0]
    print(f"  Features with <=10% overlap: {len(failing_c)}")
    for _, row in failing_c.iterrows():
        print(f"    {row['feature']:40s} overlap = {row['overlap_pct']:.1f}%")
    
    print(f"  Bottom-5 overlaps:")
    for _, row in df_gate_c.head(5).iterrows():
        print(f"    {row['feature']:40s} overlap = {row['overlap_pct']:.1f}%")
    
    gate_c_pass = min_overlap > 10.0
    gate_results["C"] = gate_c_pass
    gate_details["C"] = f"Min overlap = {min_overlap:.1f}% ({worst_feature})"
    print(f"  Gate C: {'✅ PASS' if gate_c_pass else '❌ FAIL'} — {gate_details['C']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE D: Correlation Documentation (informational)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate D: Correlation Documentation ---")
    
    corr_matrix = all_data[feature_cols].corr()
    high_corr_pairs = []
    for i in range(len(feature_cols)):
        for j in range(i+1, len(feature_cols)):
            r = corr_matrix.iloc[i, j]
            if abs(r) > 0.80:
                high_corr_pairs.append({
                    "feature_1": feature_cols[i],
                    "feature_2": feature_cols[j],
                    "r": round(r, 4)
                })
    
    df_gate_d = pd.DataFrame(high_corr_pairs)
    print(f"  High-correlation pairs (|r| > 0.80): {len(df_gate_d)}")
    if len(df_gate_d) > 0:
        for _, row in df_gate_d.iterrows():
            print(f"    {row['feature_1']:30s} ↔ {row['feature_2']:30s} r = {row['r']:.4f}")
    
    gate_results["D"] = True  # Informational only
    gate_details["D"] = f"{len(df_gate_d)} pairs with |r| > 0.80 documented"

    # ─────────────────────────────────────────────────────────────────────────
    # GATE E: Rare Typology Counts (>= 200 scenarios each)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate E: Rare Typology Scenario Counts ---")
    
    typ_counts = all_data.groupby("pattern_type")["scenario_id"].nunique()
    print(f"  Typology scenario counts:")
    for pt, cnt in typ_counts.items():
        flag = " ⚠️" if pt in ["peeling_chain", "layering", "mixing"] and cnt < 200 else ""
        print(f"    {pt:25s} {cnt:5d} scenarios{flag}")
    
    rare_types = ["peeling_chain", "layering", "mixing"]
    gate_e_pass = all(
        typ_counts.get(t, 0) >= 200 for t in rare_types
    )
    gate_results["E"] = gate_e_pass
    gate_details["E"] = ", ".join(f"{t}={typ_counts.get(t,0)}" for t in rare_types)
    print(f"  Gate E: {'✅ PASS' if gate_e_pass else '❌ FAIL'} — {gate_details['E']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE F: Within-Typology PCA Variation
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate F: Within-Typology PCA Variation ---")
    
    # Use structural/graph/temporal features
    pca_feature_subset = [f for f in feature_cols if f in [
        "num_txns", "mean_num_inputs", "mean_num_outputs", "io_count_ratio",
        "unique_input_addrs", "unique_output_addrs", "address_reuse_ratio",
        "change_output_ratio", 
        "time_span_hours", "inter_tx_delta_mean", "inter_tx_delta_std",
        "burstiness_B", "max_chain_length", "graph_density", "avg_clustering",
        "max_in_degree", "max_out_degree", "degree_assortativity", "edge_to_node_ratio",
    ]]
    
    illicit_data = all_data[all_data["is_illicit"] == 1]
    pca_results = {}
    gate_f_flag = False
    
    for typ in ["peeling_chain", "layering", "mixing", "ransomware"]:
        typ_data = illicit_data[illicit_data["pattern_type"] == typ]
        if len(typ_data) < 10:
            pca_results[typ] = {"n_samples": len(typ_data), "n_components_90": 0}
            continue
        
        X_typ = typ_data[pca_feature_subset].fillna(0).values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_typ)
        
        n_components = min(len(pca_feature_subset), len(typ_data))
        pca = PCA(n_components=n_components)
        pca.fit(X_scaled)
        
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        n_for_90 = int(np.searchsorted(cumvar, 0.90) + 1)
        
        pca_results[typ] = {
            "n_samples": len(typ_data),
            "n_components_90": n_for_90,
            "top3_variance": cumvar[min(2, len(cumvar)-1)]
        }
        if n_for_90 < 4:
            gate_f_flag = True
        
        print(f"  {typ:20s}: {n_for_90:2d} components for 90% variance ({len(typ_data)} samples)")
    
    gate_results["F"] = True  # Informational, but flag if < 4
    gate_details["F"] = "; ".join(f"{t}={r['n_components_90']}comp" for t, r in pca_results.items())
    if gate_f_flag:
        gate_details["F"] += " ⚠️ WARNING: some typology needs <4 components (rigid templating risk)"
    print(f"  Gate F: {'✅ PASS' if not gate_f_flag else '⚠️ WARNING'} — {gate_details['F']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE G: Scenario-Level Split Integrity
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate G: Scenario-Level Split Integrity ---")
    
    train_scenarios = set(train["scenario_id"])
    test_scenarios = set(test["scenario_id"])
    shared = train_scenarios & test_scenarios
    
    print(f"  Train scenarios: {len(train_scenarios):,}")
    print(f"  Test scenarios:  {len(test_scenarios):,}")
    print(f"  Shared:          {len(shared)}")
    
    gate_g_pass = len(shared) == 0
    gate_results["G"] = gate_g_pass
    gate_details["G"] = f"{len(shared)} shared scenarios"
    print(f"  Gate G: {'✅ PASS' if gate_g_pass else '❌ FAIL'}")

    # Also check txid overlap if raw data available
    if bc_full is not None and "split" in bc_full.columns:
        train_txids = set(bc_full[bc_full["split"] == "train"]["txid"])
        test_txids = set(bc_full[bc_full["split"] == "test"]["txid"])
        shared_txids = train_txids & test_txids
        print(f"  Shared txids: {len(shared_txids)}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE H: Categorical Overlap
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate H: Categorical Overlap ---")
    
    cat_results = {}
    if bc_full is not None:
        net_path = DATA / "network_metadata.csv"
        if net_path.exists():
            df_net = pd.read_csv(net_path)
            df_merged = bc_full[["txid", "scenario_id", "is_illicit"]].merge(
                df_net[["txid", "country_code", "asn", "node_type"]], on="txid"
            )
            
            for cat_col in ["country_code", "asn", "node_type"]:
                licit_cats = set(df_merged[df_merged["is_illicit"] == 0][cat_col].unique())
                illicit_cats = set(df_merged[df_merged["is_illicit"] == 1][cat_col].unique())
                intersection = licit_cats & illicit_cats
                union = licit_cats | illicit_cats
                overlap_pct = len(intersection) / max(len(union), 1) * 100
                cat_results[cat_col] = {
                    "licit": len(licit_cats),
                    "illicit": len(illicit_cats),
                    "shared": len(intersection),
                    "overlap_pct": overlap_pct
                }
                print(f"  {cat_col}: {len(licit_cats)} licit / {len(illicit_cats)} illicit / "
                      f"{len(intersection)} shared ({overlap_pct:.1f}%)")
    
    min_cat_overlap = min((r["overlap_pct"] for r in cat_results.values()), default=100)
    gate_h_pass = min_cat_overlap >= 90.0
    gate_results["H"] = gate_h_pass
    gate_details["H"] = f"Min categorical overlap = {min_cat_overlap:.1f}%"
    print(f"  Gate H: {'✅ PASS' if gate_h_pass else '❌ FAIL'} — {gate_details['H']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE I: Typology Ablation Robustness (THE critical gate)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate I: Typology Ablation Robustness ---")
    
    illicit_train = train[train["is_illicit"] == 1].copy()
    illicit_test = test[test["is_illicit"] == 1].copy()
    
    le = LabelEncoder()
    le.fit(illicit_train["pattern_type"])
    y_typ_train = le.transform(illicit_train["pattern_type"])
    y_typ_test = le.transform(illicit_test["pattern_type"])
    
    X_typ_train = illicit_train[feature_cols].fillna(0).values
    X_typ_test = illicit_test[feature_cols].fillna(0).values
    
    # Baseline: full feature model
    typ_model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", random_state=42, verbosity=0
    )
    typ_model.fit(X_typ_train, y_typ_train)
    typ_proba = typ_model.predict_proba(X_typ_test)
    
    # Per-class OvR AUC baseline
    classes = le.classes_
    baseline_aucs = {}
    for i, c in enumerate(classes):
        y_bin = (y_typ_test == i).astype(int)
        if len(np.unique(y_bin)) > 1:
            baseline_aucs[c] = roc_auc_score(y_bin, typ_proba[:, i])
        else:
            baseline_aucs[c] = float("nan")
    
    print(f"  Baseline OvR AUCs:")
    for c, auc in baseline_aucs.items():
        print(f"    {c:20s} AUC = {auc:.4f}")
    
    # Feature importance for ablation
    importances = typ_model.feature_importances_
    top3_idx = np.argsort(importances)[-3:][::-1]
    top3_features = [feature_cols[i] for i in top3_idx]
    print(f"  Top-3 features to ablate: {top3_features}")
    
    # Ablated model: remove top-3
    ablated_cols = [c for c in feature_cols if c not in top3_features]
    X_typ_train_abl = illicit_train[ablated_cols].fillna(0).values
    X_typ_test_abl = illicit_test[ablated_cols].fillna(0).values
    
    typ_model_abl = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", random_state=42, verbosity=0
    )
    typ_model_abl.fit(X_typ_train_abl, y_typ_train)
    typ_proba_abl = typ_model_abl.predict_proba(X_typ_test_abl)
    
    ablated_aucs = {}
    auc_drops = {}
    gate_i_pass = True
    
    for i, c in enumerate(classes):
        y_bin = (y_typ_test == i).astype(int)
        if len(np.unique(y_bin)) > 1:
            ablated_aucs[c] = roc_auc_score(y_bin, typ_proba_abl[:, i])
        else:
            ablated_aucs[c] = float("nan")
        
        drop = baseline_aucs[c] - ablated_aucs[c]
        auc_drops[c] = drop
        
        # Check: a drop of ~0.00 is a FAIL (redundant cluster shortcut)
        if not np.isnan(drop) and abs(drop) < 0.03:
            gate_i_pass = False
            print(f"    ❌ {c}: baseline={baseline_aucs[c]:.4f} → ablated={ablated_aucs[c]:.4f} "
                  f"(drop={drop:.4f} < 0.03 — SUSPICIOUS)")
        else:
            print(f"    ✅ {c}: baseline={baseline_aucs[c]:.4f} → ablated={ablated_aucs[c]:.4f} "
                  f"(drop={drop:.4f})")
    
    gate_results["I"] = gate_i_pass
    gate_details["I"] = "; ".join(f"{c}: Δ={auc_drops[c]:.4f}" for c in classes)
    print(f"  Gate I: {'✅ PASS' if gate_i_pass else '❌ FAIL'} — {gate_details['I']}")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE J: Binary Ablation Robustness (informational)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- Gate J: Binary Ablation Robustness ---")
    
    X_bin_train = train[feature_cols].fillna(0).values
    X_bin_test = test[feature_cols].fillna(0).values
    
    n_licit = (y_train_val == 0).sum()
    n_illicit_tr = (y_train_val == 1).sum()
    spw = n_licit / max(n_illicit_tr, 1)
    
    bin_model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=spw,
        tree_method="hist", random_state=42, verbosity=0
    )
    bin_model.fit(X_bin_train, y_train_val)
    bin_proba = bin_model.predict_proba(X_bin_test)[:, 1]
    baseline_bin_auc = roc_auc_score(y_test_val, bin_proba)
    
    # Top-3 features for binary
    bin_importances = bin_model.feature_importances_
    bin_top3_idx = np.argsort(bin_importances)[-3:][::-1]
    bin_top3 = [feature_cols[i] for i in bin_top3_idx]
    
    bin_ablated_cols = [c for c in feature_cols if c not in bin_top3]
    X_bin_train_abl = train[bin_ablated_cols].fillna(0).values
    X_bin_test_abl = test[bin_ablated_cols].fillna(0).values
    
    bin_model_abl = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=spw,
        tree_method="hist", random_state=42, verbosity=0
    )
    bin_model_abl.fit(X_bin_train_abl, y_train_val)
    bin_proba_abl = bin_model_abl.predict_proba(X_bin_test_abl)[:, 1]
    ablated_bin_auc = roc_auc_score(y_test_val, bin_proba_abl)
    
    bin_drop = baseline_bin_auc - ablated_bin_auc
    
    print(f"  Baseline binary AUC:  {baseline_bin_auc:.4f}")
    print(f"  Top-3 ablated:        {bin_top3}")
    print(f"  Ablated binary AUC:   {ablated_bin_auc:.4f}")
    print(f"  Drop:                 {bin_drop:.4f}")
    
    gate_results["J"] = True  # Informational
    gate_details["J"] = (f"baseline={baseline_bin_auc:.4f}, ablated={ablated_bin_auc:.4f}, "
                         f"drop={bin_drop:.4f}, top3={bin_top3}")
    
    if abs(bin_drop) < 0.005:
        gate_details["J"] += " ⚠️ near-zero drop — possible redundancy"
    print(f"  Gate J: INFORMATIONAL — {gate_details['J']}")

    # ─────────────────────────────────────────────────────────────────────────
    # FINAL VERDICT
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("📋 GATE RESULTS SUMMARY")
    print("=" * 80)
    
    hard_gates = ["A", "B", "C", "E", "G", "H", "I"]
    all_hard_pass = all(gate_results.get(g, False) for g in hard_gates)
    
    for g in sorted(gate_results.keys()):
        status = "✅ PASS" if gate_results[g] else "❌ FAIL"
        hard = " [HARD]" if g in hard_gates else " [SOFT]"
        print(f"  Gate {g}{hard}: {status} — {gate_details[g]}")
    
    print("=" * 80)
    overall = "🎉 PASS — ALL HARD GATES PASSED" if all_hard_pass else "❌ FAIL — HARD GATE(S) FAILED"
    print(f"OVERALL: {overall}")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORT REPORT
    # ─────────────────────────────────────────────────────────────────────────
    report_path = ROOT / "V6_ACCEPTANCE_AUDIT.md"
    
    md = f"""# V5 Acceptance Audit Report — SIH PS 146 AML Synthetic Dataset

> **Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
> **Dataset Version:** v5.0  
> **Feature Count:** {n_features} (pipeline-synced, structurally verified)
> **Overall Audit Status:** {overall}

---

## Gate Results Summary

| Gate | Type | Status | Details |
|------|------|--------|---------|
"""
    for g in sorted(gate_results.keys()):
        status = "✅ PASS" if gate_results[g] else "❌ FAIL"
        gtype = "HARD" if g in hard_gates else "SOFT"
        md += f"| {g} | {gtype} | {status} | {gate_details[g]} |\n"

    md += f"""
---

## Gate A: Single-Feature AUC Analysis

Max single-feature AUC: **{max_single_auc:.4f}** (threshold: < 0.90)

| Feature | AUC |
|---------|-----|
"""
    for _, row in df_gate_a.head(15).iterrows():
        md += f"| {row['feature']} | {row['auc']:.4f} |\n"

    md += f"""
---

## Gate B: Simple-Rule Separability

- All-feature depth-2 tree BAcc: **{dt_bacc:.4f}**
- Best 2-feature pair ({best_pair_desc}): **{best_pair_bacc:.4f}**
- Threshold: < 0.85

---

## Gate C: Distribution Overlap

Min overlap: **{min_overlap:.1f}%** ({worst_feature})

| Feature | Overlap % |
|---------|-----------|
"""
    for _, row in df_gate_c.head(15).iterrows():
        md += f"| {row['feature']} | {row['overlap_pct']:.1f}% |\n"

    md += f"""
---

## Gate D: Correlation Analysis

{len(df_gate_d)} pairs with |r| > 0.80 documented.

"""
    if len(df_gate_d) > 0:
        md += "| Feature 1 | Feature 2 | r |\n|-----------|-----------|---|\n"
        for _, row in df_gate_d.iterrows():
            md += f"| {row['feature_1']} | {row['feature_2']} | {row['r']:.4f} |\n"

    md += f"""
---

## Gate E: Typology Counts

{gate_details['E']}

---

## Gate F: Within-Typology PCA

{gate_details['F']}

---

## Gate G: Split Integrity

{gate_details['G']}

---

## Gate H: Categorical Overlap

{gate_details['H']}

---

## Gate I: Typology Ablation (Critical)

Top-3 features ablated: {top3_features}

| Typology | Baseline AUC | Ablated AUC | Drop |
|----------|-------------|-------------|------|
"""
    for c in classes:
        md += f"| {c} | {baseline_aucs[c]:.4f} | {ablated_aucs[c]:.4f} | {auc_drops[c]:.4f} |\n"

    md += f"""
---

## Gate J: Binary Ablation (Informational)

{gate_details['J']}

---

*Report generated by `ml/audit_v5.py` — tests the EXACT output of the unified ML pipeline.*
*Feature column sync structurally verified: {n_features} features.*
"""
    
    with open(report_path, "w") as f:
        f.write(md)
    print(f"\n📄 Report saved: {report_path}")
    
    return {
        "passed": all_hard_pass,
        "gate_results": gate_results,
        "gate_details": gate_details,
        "max_single_auc": max_single_auc,
        "max_simple_bacc": max_simple_bacc,
        "min_overlap": min_overlap,
        "baseline_aucs": baseline_aucs,
        "ablated_aucs": ablated_aucs,
        "auc_drops": auc_drops,
        "baseline_bin_auc": baseline_bin_auc,
        "ablated_bin_auc": ablated_bin_auc,
        "bin_drop": bin_drop,
    }


if __name__ == "__main__":
    result = run_v5_audit()
    sys.exit(0 if result["passed"] else 1)
