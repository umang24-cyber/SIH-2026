"""
02c_merge_features.py
=====================
Day 2 — Merge Phase-1 features with graph features.

Run from SIH-2026/:
    conda activate ml
    python ml/02c_merge_features.py

Outputs:
    data/processed_v8_v8/scenario_features_full_train.csv
    data/processed_v8_v8/scenario_features_full_test.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed_v8"

def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

for split in ["train", "test"]:
    sep(f"Merging: {split}")
    feats = pd.read_csv(DATA / f"scenario_features_{split}.csv")
    graph = pd.read_csv(DATA / f"scenario_graph_features_{split}.csv")

    before_rows = len(feats)
    merged = feats.merge(graph, on="scenario_id", how="left")
    assert len(merged) == before_rows, \
        f"Row count changed after merge! {before_rows} -> {len(merged)}"

    print(f"  Phase-1 features: {feats.shape}")
    print(f"  Graph features:   {graph.shape}")
    print(f"  Merged shape:     {merged.shape}")

    # NaN audit — report any NaN per column
    nan_counts = merged.isnull().sum()
    nan_cols   = nan_counts[nan_counts > 0]
    if len(nan_cols) == 0:
        print("  NaN check: PASS — zero NaN")
    else:
        print(f"  NaN found in {len(nan_cols)} column(s):")
        for col, cnt in nan_cols.items():
            pct = cnt / len(merged) * 100
            # Graph features degenerate for small scenarios are expected — document
            expected_cols = {"degree_assortativity", "avg_clustering",
                             "max_chain_length", "graph_density",
                             "edge_to_node_ratio", "max_in_degree", "max_out_degree"}
            tag = "[EXPECTED-GRAPH-DEGENERATE]" if col in expected_cols else "[UNEXPECTED — STOP]"
            print(f"    {tag} {col}: {cnt} NaN ({pct:.2f}%)")
        unexpected = [c for c in nan_cols.index if c not in
                      {"degree_assortativity","avg_clustering","max_chain_length",
                       "graph_density","edge_to_node_ratio","max_in_degree","max_out_degree"}]
        if unexpected:
            raise RuntimeError(f"Unexpected NaN in columns: {unexpected} — stopping.")
        else:
            print("  All NaN are in documented graph-degenerate columns. Filling with 0.")
            for col in nan_cols.index:
                merged[col] = merged[col].fillna(0)

    out_path = DATA / f"scenario_features_full_{split}.csv"
    merged.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")

    # Final dtypes summary
    print(f"\n  Dtypes:")
    print(merged.dtypes.to_string())

sep("DONE — 02c_merge_features.py")
