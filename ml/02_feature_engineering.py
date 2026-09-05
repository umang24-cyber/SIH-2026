"""
02_feature_engineering.py
=========================
Day 1 — Phase 1 Feature Engineering for SIH PS 146 Bitcoin AML.
(Phase 1: no graph/networkx — all features computed from raw CSV columns only.)

Run from the project root (SIH-2026/):
    conda activate ml
    python ml/02_feature_engineering.py

Outputs (in data/processed/):
    scenario_features_train.csv   — one row per train scenario, features only
    scenario_features_test.csv    — one row per test scenario, features only
    scenario_labels_train.csv     — scenario_id + is_illicit + pattern_type (train)
    scenario_labels_test.csv      — scenario_id + is_illicit + pattern_type (test)
    script_type_encoder.json      — label encoding map fitted on train only

Validation gate results printed at the end.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"

ARRAY_COLS = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]

# ---------------------------------------------------------------------------
# Helpers — reusable functions
# ---------------------------------------------------------------------------

def load_and_join(bc_path: Path, net_path: Path) -> pd.DataFrame:
    """Load blockchain + network CSVs, parse array columns, join on txid."""
    bc = pd.read_csv(bc_path)
    bc["timestamp"] = pd.to_datetime(bc["timestamp"])
    for col in ARRAY_COLS:
        bc[col] = bc[col].apply(json.loads)

    net = pd.read_csv(net_path)
    net["relay_timestamp"] = pd.to_datetime(net["relay_timestamp"])

    # Drop columns that are redundant after join (scenario_id, split duplicated in both)
    net = net.drop(columns=["scenario_id", "split"], errors="ignore")
    joined = bc.merge(net, on="txid", how="inner")
    assert len(joined) == len(bc), (
        f"Join size mismatch: bc={len(bc)} vs joined={len(joined)}"
    )
    return joined


def gini_coefficient(values: np.ndarray) -> float:
    """Standard Gini coefficient. Returns 0 for empty or all-zero arrays."""
    v = np.asarray(values, dtype=float)
    v = v[v >= 0]  # guard negatives (shouldn't occur for amounts)
    if len(v) == 0 or v.sum() == 0:
        return 0.0
    v = np.sort(v)
    n = len(v)
    cumv = np.cumsum(v)
    return (2 * np.dot(np.arange(1, n + 1), v) - (n + 1) * cumv[-1]) / (n * cumv[-1])


def shannon_entropy(values) -> float:
    """Shannon entropy of a discrete distribution. Returns 0 for length-1 input."""
    counts = np.asarray(values, dtype=float)
    counts = counts[counts > 0]
    if len(counts) == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p + 1e-12)))


ROUND_TARGETS = np.array([0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0])

def is_round_number(amount: float, tol: float = 0.01) -> bool:
    """True if amount is within tol% of any canonical round denomination."""
    if amount <= 0:
        return False
    return bool(np.any(np.abs(amount - ROUND_TARGETS) / ROUND_TARGETS <= tol))


SUSPICIOUS_NODE_TYPES = {"tor_exit_node", "vpn_proxy", "bulletproof_host"}


def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ---------------------------------------------------------------------------
# Per-scenario feature computation
# ---------------------------------------------------------------------------

def compute_scenario_features(grp: pd.DataFrame) -> dict:
    """
    Compute all Phase-1 features for one scenario group.

    Single-transaction scenario edge cases:
    - fee_ratio_std → 0  (std of one value)
    - inter_tx_delta_* → 0 / NaN handled explicitly; burstiness_B → 0
    - prop_delta_cv → 0 if mean==0
    - hour_of_day_entropy → 0 (only one hour)
    - script_type_entropy → 0
    These are documented below; they are NOT silently NaN — we set them to 0
    because a std/entropy of 0 is the correct degenerate value for n=1.
    """
    grp = grp.sort_values("timestamp").reset_index(drop=True)
    n = len(grp)

    feats = {}

    # ------------------------------------------------------------------
    # Amount features
    # ------------------------------------------------------------------
    in_sums  = grp["input_amounts"].apply(sum)
    out_sums = grp["output_amounts"].apply(sum)
    fees     = grp["fee_btc"]

    feats["total_input_mean"]  = float(in_sums.mean())
    feats["total_output_mean"] = float(out_sums.mean())

    fee_ratios = fees / in_sums.replace(0, np.nan)
    feats["fee_ratio_mean"] = float(fee_ratios.mean())
    # For n==1, std is NaN by default in pandas; set to 0 (correct: no spread)
    feats["fee_ratio_std"]  = float(fee_ratios.std()) if n > 1 else 0.0

    # amount_decay_slope: linear regression of sum(output_amounts) over txn order
    if n > 1:
        slope, *_ = linregress(np.arange(n), out_sums.values)
        feats["amount_decay_slope"] = float(slope)
    else:
        # n==1: slope is undefined; set to 0 (no decay measurable)
        feats["amount_decay_slope"] = 0.0

    all_out_amounts = np.concatenate(grp["output_amounts"].values)
    feats["output_amount_gini"] = gini_coefficient(all_out_amounts)

    # denomination_entropy: Shannon entropy over ~20 log-spaced bins
    if len(all_out_amounts) > 0 and all_out_amounts.max() > 0:
        log_vals = np.log10(np.clip(all_out_amounts, 1e-12, None))
        bin_edges = np.linspace(log_vals.min() - 1e-9, log_vals.max() + 1e-9, 21)
        hist, _ = np.histogram(log_vals, bins=bin_edges)
        feats["denomination_entropy"] = shannon_entropy(hist)
    else:
        feats["denomination_entropy"] = 0.0

    feats["round_number_ratio"] = float(
        np.mean([is_round_number(a) for a in all_out_amounts])
    ) if len(all_out_amounts) > 0 else 0.0

    # io_amount_similarity per txn, then averaged
    io_sim = 1.0 - np.abs(in_sums - out_sums) / in_sums.replace(0, np.nan)
    feats["io_amount_similarity"] = float(io_sim.mean())

    # ------------------------------------------------------------------
    # Structural features
    # ------------------------------------------------------------------
    feats["num_txns"] = n

    num_inputs_per_txn  = grp["input_addresses"].apply(len)
    num_outputs_per_txn = grp["output_addresses"].apply(len)
    feats["mean_num_inputs"]  = float(num_inputs_per_txn.mean())
    feats["mean_num_outputs"] = float(num_outputs_per_txn.mean())
    # io_count_ratio: guard against zero mean_num_outputs (shouldn't happen, but safe)
    mean_out = feats["mean_num_outputs"]
    feats["io_count_ratio"] = feats["mean_num_inputs"] / mean_out if mean_out > 0 else 0.0

    all_in_addrs  = set(a for addrs in grp["input_addresses"]  for a in addrs)
    all_out_addrs = set(a for addrs in grp["output_addresses"] for a in addrs)
    feats["unique_input_addrs"]  = len(all_in_addrs)
    feats["unique_output_addrs"] = len(all_out_addrs)

    # fanout_ratio: unique output addresses per transaction (structural breadth).
    # fanin_ratio:  unique input addresses per transaction (structural depth).
    # NOTE: These are NOT redundant with mean_num_outputs / mean_num_inputs.
    #   mean_num_outputs = per-transaction arity (counting duplicates within a txn).
    #   fanout_ratio     = unique output wallets spread per transaction (scenario-level density).
    # Example where they diverge: peeling_chain has high mean_num_outputs per txn (outputs
    # to change+main chain) but LOW fanout_ratio (same wallet reused across chain hops).
    feats["fanout_ratio"] = len(all_out_addrs) / n if n > 0 else 0.0
    feats["fanin_ratio"]  = len(all_in_addrs)  / n if n > 0 else 0.0
    overlap = all_in_addrs & all_out_addrs
    feats["address_reuse_ratio"] = len(overlap) / len(all_out_addrs) if all_out_addrs else 0.0

    # change_output_ratio: per-txn heuristic, then average across scenario
    # For each txn: a "change output" is one whose amount ≈ largest_input - some_other_output
    # within 1% tolerance. We check all (input, output_pair) combinations.
    change_flags = []
    for _, row in grp.iterrows():
        in_amts  = np.array(row["input_amounts"],  dtype=float)
        out_amts = np.array(row["output_amounts"], dtype=float)
        if len(in_amts) == 0 or len(out_amts) == 0:
            change_flags.append(0.0)
            continue
        max_input = in_amts.max()
        # candidate change = max_input minus each other output amount
        # flag output if it matches any of those candidates within 1%
        txn_change_count = 0
        for out_val in out_amts:
            for other_out in out_amts:
                if other_out == out_val:
                    continue
                candidate = max_input - other_out
                if candidate > 0 and abs(out_val - candidate) / candidate <= 0.01:
                    txn_change_count += 1
                    break
        change_flags.append(txn_change_count / len(out_amts))
    feats["change_output_ratio"] = float(np.mean(change_flags))

    script_counts = grp["script_type"].value_counts()
    feats["script_type_entropy"] = shannon_entropy(script_counts.values)
    # script_type_mode: set later after global encoder is built
    feats["_script_type_mode_raw"] = grp["script_type"].mode().iloc[0]

    # ------------------------------------------------------------------
    # Temporal features
    # ------------------------------------------------------------------
    ts = grp["timestamp"]
    feats["time_span_hours"] = float(
        (ts.max() - ts.min()).total_seconds() / 3600.0
    )

    if n > 1:
        deltas = ts.diff().dt.total_seconds().dropna().values
        feats["inter_tx_delta_mean"] = float(deltas.mean())
        feats["inter_tx_delta_std"]  = float(deltas.std()) if len(deltas) > 1 else 0.0
        feats["inter_tx_delta_min"]  = float(deltas.min())
        mu, sigma = feats["inter_tx_delta_mean"], feats["inter_tx_delta_std"]
        denom = sigma + mu
        # burstiness_B: guard denom==0 (all deltas identical → B=0 is correct)
        feats["burstiness_B"] = float((sigma - mu) / denom) if denom != 0 else 0.0
    else:
        # n==1: no inter-txn deltas; all temporal spread features are 0
        feats["inter_tx_delta_mean"] = 0.0
        feats["inter_tx_delta_std"]  = 0.0
        feats["inter_tx_delta_min"]  = 0.0
        feats["burstiness_B"]        = 0.0

    hours = ts.dt.hour.value_counts()
    feats["hour_of_day_entropy"] = shannon_entropy(hours.values)

    # propagation delta in milliseconds
    rts = grp["relay_timestamp"]
    prop_deltas_ms = (ts - rts).dt.total_seconds() * 1000.0
    feats["prop_delta_mean"] = float(prop_deltas_ms.mean())
    feats["prop_delta_std"]  = float(prop_deltas_ms.std()) if n > 1 else 0.0
    prop_mean = feats["prop_delta_mean"]
    # prop_delta_cv: guard div-by-zero (mean could theoretically be 0)
    feats["prop_delta_cv"] = (feats["prop_delta_std"] / prop_mean
                              if prop_mean != 0 else 0.0)

    # ------------------------------------------------------------------
    # Network-layer features
    # ------------------------------------------------------------------
    node_types = grp["node_type"]
    feats["suspicious_infra_ratio"] = float(
        node_types.isin(SUSPICIOUS_NODE_TYPES).mean()
    )

    asn_counts = grp["asn"].value_counts()
    feats["unique_asn_count"]    = int(asn_counts.shape[0])
    feats["asn_concentration"]   = float(asn_counts.iloc[0]) / n if n > 0 else 0.0

    cc_counts = grp["country_code"].value_counts()
    feats["unique_country_count"]   = int(cc_counts.shape[0])
    feats["country_concentration"]  = float(cc_counts.iloc[0]) / n if n > 0 else 0.0

    unique_ips = grp["relay_ip"].nunique()
    feats["unique_ip_count"] = int(unique_ips)
    feats["ip_to_addr_ratio"] = (
        unique_ips / feats["unique_input_addrs"]
        if feats["unique_input_addrs"] > 0 else 0.0
    )

    feats["alt_port_ratio"]      = float((grp["relay_port"] != 8333).mean())
    feats["unique_user_agents"]  = int(grp["user_agent"].nunique())

    return feats


# ---------------------------------------------------------------------------
# Process one split
# ---------------------------------------------------------------------------

def process_split(bc_path: Path, net_path: Path, split_name: str):
    sep(f"Processing: {split_name}")
    df = load_and_join(bc_path, net_path)
    print(f"  Joined dataframe: {len(df):,} rows, {df['scenario_id'].nunique():,} scenarios")

    rows = []
    for scenario_id, grp in df.groupby("scenario_id"):
        feat = compute_scenario_features(grp)
        feat["scenario_id"] = scenario_id
        # Capture labels — will be separated out below
        feat["_is_illicit"]    = int(grp["is_illicit"].iloc[0])
        feat["_pattern_type"]  = grp["pattern_type"].iloc[0]
        rows.append(feat)

    result = pd.DataFrame(rows)
    print(f"  Feature matrix shape: {result.shape}")
    return result


# ---------------------------------------------------------------------------
# CLI pipeline
# ---------------------------------------------------------------------------

def run_pipeline():
    """Build and validate the persisted feature artifacts."""
    OUT.mkdir(parents=True, exist_ok=True)
    sep("LOADING & PROCESSING TRAIN SPLIT")
    train_df = process_split(
        DATA / "train_blockchain.csv",
        DATA / "train_network.csv",
        "train"
    )

    sep("LOADING & PROCESSING TEST SPLIT")
    test_df = process_split(
        DATA / "test_blockchain.csv",
        DATA / "test_network.csv",
        "test"
    )

    sep("ENCODING script_type_mode (train-only fit)")
    all_train_types = train_df["_script_type_mode_raw"].unique().tolist()
    all_test_types  = test_df["_script_type_mode_raw"].unique().tolist()
    all_types = sorted(set(all_train_types) | set(all_test_types))

    encoder = {t: i for i, t in enumerate(all_types)}
    print(f"  Script type encoding: {encoder}")
    train_df["script_type_mode"] = train_df["_script_type_mode_raw"].map(encoder)
    test_df["script_type_mode"]  = test_df["_script_type_mode_raw"].map(encoder)

    enc_path = DATA / "script_type_encoder.json"
    with open(enc_path, "w") as f:
        json.dump(encoder, f, indent=2)
    print(f"  Encoder saved: {enc_path}")

    label_cols = ["scenario_id", "_is_illicit", "_pattern_type", "_script_type_mode_raw"]
    feature_cols = [c for c in train_df.columns if c not in label_cols]
    print(f"\n  Feature columns ({len(feature_cols)}): {feature_cols}")

    train_features = train_df[["scenario_id"] + [c for c in feature_cols if c != "scenario_id"]]
    test_features  = test_df[["scenario_id"]  + [c for c in feature_cols if c != "scenario_id"]]
    train_labels = train_df[["scenario_id", "_is_illicit", "_pattern_type"]].rename(
        columns={"_is_illicit": "is_illicit", "_pattern_type": "pattern_type"}
    )
    test_labels  = test_df[["scenario_id", "_is_illicit", "_pattern_type"]].rename(
        columns={"_is_illicit": "is_illicit", "_pattern_type": "pattern_type"}
    )

    paths = {
        "scenario_features_train": (DATA / "scenario_features_train.csv", train_features),
        "scenario_features_test":  (DATA / "scenario_features_test.csv",  test_features),
        "scenario_labels_train":   (DATA / "scenario_labels_train.csv",   train_labels),
        "scenario_labels_test":    (DATA / "scenario_labels_test.csv",    test_labels),
    }
    for name, (path, df_out) in paths.items():
        df_out.to_csv(path, index=False)
        print(f"  Saved: {path}  ({len(df_out):,} rows)")

    sep("VALIDATION GATE")
    issues = []
    train_unique_sc = pd.read_csv(DATA / "train_blockchain.csv")["scenario_id"].nunique()
    test_unique_sc  = pd.read_csv(DATA / "test_blockchain.csv")["scenario_id"].nunique()

    if len(train_features) == train_unique_sc:
        print(f"[PASS] scenario_features_train.csv has {len(train_features):,} rows == {train_unique_sc:,} unique train scenarios")
    else:
        msg = f"[FAIL] scenario_features_train.csv has {len(train_features)} rows but {train_unique_sc} unique scenarios"
        print(msg); issues.append(msg)
    if len(test_features) == test_unique_sc:
        print(f"[PASS] scenario_features_test.csv  has {len(test_features):,} rows == {test_unique_sc:,} unique test scenarios")
    else:
        msg = f"[FAIL] scenario_features_test.csv has {len(test_features)} rows but {test_unique_sc} unique scenarios"
        print(msg); issues.append(msg)

    for split_label, feat_df in [("train", train_features), ("test", test_features)]:
        nan_cols = feat_df.isnull().sum()
        nan_cols = nan_cols[nan_cols > 0]
        if len(nan_cols) == 0:
            print(f"[PASS] Zero NaN in {split_label} feature matrix")
        else:
            msg = f"[FAIL] NaN found in {split_label} features: {dict(nan_cols)}"
            print(msg); issues.append(msg)

    for split_label, feat_df in [("train", train_features), ("test", test_features)]:
        leaked = [c for c in ["is_illicit", "pattern_type"] if c in feat_df.columns]
        if not leaked:
            print(f"[PASS] Labels not present in {split_label} features file")
        else:
            msg = f"[FAIL] Label columns found in {split_label} features: {leaked}"
            print(msg); issues.append(msg)

    print("\n--- Pearson |r| vs is_illicit (leakage check) ---")
    high_corr_threshold = 0.9
    for split_label, feat_df, lbl_df in [("train", train_features, train_labels), ("test", test_features, test_labels)]:
        merged_tmp = feat_df.merge(lbl_df[["scenario_id", "is_illicit"]], on="scenario_id")
        numeric_feats = [c for c in merged_tmp.select_dtypes(include=[np.number]).columns if c != "is_illicit"]
        corrs = merged_tmp[numeric_feats].corrwith(merged_tmp["is_illicit"]).abs().sort_values(ascending=False)
        high = corrs[corrs > high_corr_threshold]
        if len(high) > 0:
            print(f"\n  *** [{split_label}] HIGH CORRELATION ALERT — possible leakage: ***")
            for feat, r in high.items():
                print(f"       {feat}: |r|={r:.4f}")
            issues.append(f"[WARN] {split_label}: features with |r|>{high_corr_threshold} vs is_illicit: {high.to_dict()}")
        else:
            print(f"  [{split_label}] No feature has |r| > {high_corr_threshold} with is_illicit.")
        print(f"  [{split_label}] Top-10 correlations:")
        for feat, r in corrs.head(10).items():
            print(f"    {feat:<35} |r| = {r:.4f}")

    print("\n--- Hard-negative exchange wallet spot check ---")
    train_feats_lbl = train_features.merge(train_labels, on="scenario_id")
    exchanges = train_feats_lbl[
        (train_feats_lbl["is_illicit"] == 0) &
        (train_feats_lbl["pattern_type"] == "normal") &
        (train_feats_lbl["num_txns"] >= 50)
    ].nlargest(5, "num_txns")[["scenario_id", "num_txns", "mean_num_outputs", "is_illicit"]]
    if len(exchanges) > 0:
        print(f"  [PASS] Found {len(train_feats_lbl[(train_feats_lbl['is_illicit']==0) & (train_feats_lbl['num_txns']>=50)])} high-txn licit scenarios. Sample (top 5):")
        print(exchanges.to_string(index=False))
    else:
        msg = "[FAIL] No high-txn licit scenarios found — hard-negative check failed"
        print(msg); issues.append(msg)

    sep("VALIDATION GATE SUMMARY")
    if not issues:
        print("  ALL CHECKS PASSED. Safe to proceed to Day 2.")
    else:
        print(f"  {len(issues)} issue(s) found — DO NOT proceed to Day 2 until resolved:")
        for iss in issues:
            print(f"    - {iss}")
    sep("DONE — 02_feature_engineering.py")
    print(f"  Outputs: {DATA}")


if __name__ == "__main__":
    run_pipeline()
