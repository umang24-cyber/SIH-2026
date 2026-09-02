"""
01_eda_and_validation.py
========================
Day 1 — EDA & Validation for SIH PS 146 Bitcoin AML Dataset.

Run from the project root (SIH-2026/):
    conda activate ml
    python ml/01_eda_and_validation.py

Outputs:
    ml/outputs/scenario_counts_by_pattern.png
    ml/outputs/scenario_counts_by_pattern_split.png
    ml/outputs/scenario_size_boxplot.png
    ml/outputs/scenario_illicit_balance.png
    ml/outputs/eda_report.md
"""

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

TRAIN_BC  = DATA / "train_blockchain.csv"
TRAIN_NET = DATA / "train_network.csv"
TEST_BC   = DATA / "test_blockchain.csv"
TEST_NET  = DATA / "test_network.csv"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ARRAY_COLS = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]

def load_blockchain(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ARRAY_COLS:
        df[col] = df[col].apply(json.loads)
    return df

def load_network(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["relay_timestamp"] = pd.to_datetime(df["relay_timestamp"])
    return df

def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

# ---------------------------------------------------------------------------
# 1. Load all four CSVs
# ---------------------------------------------------------------------------
sep("1. LOADING DATA")
print("Loading train_blockchain ...", end=" ", flush=True)
train_bc  = load_blockchain(TRAIN_BC)
print(f"done — {len(train_bc):,} rows")

print("Loading train_network   ...", end=" ", flush=True)
train_net = load_network(TRAIN_NET)
print(f"done — {len(train_net):,} rows")

print("Loading test_blockchain  ...", end=" ", flush=True)
test_bc   = load_blockchain(TEST_BC)
print(f"done — {len(test_bc):,} rows")

print("Loading test_network    ...", end=" ", flush=True)
test_net  = load_network(TEST_NET)
print(f"done — {len(test_net):,} rows")

# ---------------------------------------------------------------------------
# 2. Validate JSON array column integrity
# ---------------------------------------------------------------------------
sep("2. ARRAY COLUMN INTEGRITY CHECK")

violations = []
for split_name, df in [("train", train_bc), ("test", test_bc)]:
    for idx, row in df.iterrows():
        ia, oa = row["input_addresses"], row["output_addresses"]
        im, om = row["input_amounts"], row["output_amounts"]
        if len(ia) != len(im):
            violations.append((split_name, row["txid"], "input_addresses vs input_amounts",
                               len(ia), len(im)))
        if len(oa) != len(om):
            violations.append((split_name, row["txid"], "output_addresses vs output_amounts",
                               len(oa), len(om)))

if violations:
    print(f"WARNING — {len(violations)} array length mismatch(es) found:")
    for v in violations[:20]:
        print(f"  [{v[0]}] txid={v[1]}: {v[2]} — lengths {v[3]} vs {v[4]}")
    if len(violations) > 20:
        print(f"  ... and {len(violations) - 20} more")
else:
    print("PASS — all input/output address and amount arrays are length-matched.")

# ---------------------------------------------------------------------------
# 3. Label homogeneity per scenario_id
# ---------------------------------------------------------------------------
sep("3. LABEL HOMOGENEITY CHECK")

homogeneity_issues = []
for split_name, df in [("train", train_bc), ("test", test_bc)]:
    agg = df.groupby("scenario_id").agg(
        illicit_nunique=("is_illicit", "nunique"),
        pattern_nunique=("pattern_type", "nunique"),
    )
    bad = agg[(agg["illicit_nunique"] > 1) | (agg["pattern_nunique"] > 1)]
    if len(bad):
        homogeneity_issues.append((split_name, bad))
        print(f"WARNING [{split_name}] — {len(bad)} scenario(s) have mixed labels:")
        print(bad.head(20))
    else:
        print(f"PASS [{split_name}] — all scenarios have homogeneous is_illicit and pattern_type.")

if not homogeneity_issues:
    print("\nAll scenarios across both splits are label-homogeneous.")

# ---------------------------------------------------------------------------
# 4. Scenario-level counts per pattern_type
# ---------------------------------------------------------------------------
sep("4. SCENARIO-LEVEL COUNTS PER PATTERN TYPE")

train_sc = (train_bc.groupby("scenario_id")
            .agg(pattern_type=("pattern_type", "first"),
                 is_illicit=("is_illicit", "first"),
                 n_txns=("txid", "count"))
            .reset_index())
test_sc  = (test_bc.groupby("scenario_id")
            .agg(pattern_type=("pattern_type", "first"),
                 is_illicit=("is_illicit", "first"),
                 n_txns=("txid", "count"))
            .reset_index())

train_counts = train_sc["pattern_type"].value_counts().sort_index()
test_counts  = test_sc["pattern_type"].value_counts().sort_index()

print(f"\n{'Pattern':<20} {'Train Scenarios':>16} {'Test Scenarios':>15}")
print("-" * 53)
all_patterns = sorted(set(train_counts.index) | set(test_counts.index))
for p in all_patterns:
    tc = train_counts.get(p, 0)
    ec = test_counts.get(p, 0)
    print(f"  {p:<18} {tc:>16,} {ec:>15,}")
print(f"  {'TOTAL':<18} {train_counts.sum():>16,} {test_counts.sum():>15,}")
print(f"\n  [Expected] ransomware ~12897/~3225, normal ~1125/~281, "
      f"peeling_chain ~32/~8, layering ~20/~5, mixing ~16/~4")

# ---------------------------------------------------------------------------
# 5. Hard-negative exchange scenario identification
# ---------------------------------------------------------------------------
sep("5. HARD-NEGATIVE EXCHANGE SCENARIO IDENTIFICATION")

normal_licit = train_sc[(train_sc["pattern_type"] == "normal") &
                        (train_sc["is_illicit"] == 0)].copy()
top40 = normal_licit.nlargest(40, "n_txns")[["scenario_id", "n_txns"]]

print("Top 40 normal/licit scenarios by txn count "
      "(expect ~30 with 50-500 txns = planted exchange wallets):\n")
print(top40.to_string(index=False))
n_ge50 = (normal_licit["n_txns"] >= 50).sum()
print(f"\n  Scenarios with >= 50 txns: {n_ge50} (expected ~30)")

# ---------------------------------------------------------------------------
# 6. Plots
# ---------------------------------------------------------------------------
sep("6. GENERATING PLOTS")

PATTERN_ORDER = ["normal", "ransomware", "peeling_chain", "layering", "mixing"]
COLORS = {"train": "#4A90D9", "test": "#E8835A"}

# --- (a) Bar chart: scenario counts per pattern (train vs test side by side)
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(PATTERN_ORDER))
w = 0.35
bars_train = [int(train_counts.get(p, 0)) for p in PATTERN_ORDER]
bars_test  = [int(test_counts.get(p, 0))  for p in PATTERN_ORDER]
ax.bar(x - w/2, bars_train, w, label="Train", color=COLORS["train"], alpha=0.9)
ax.bar(x + w/2, bars_test,  w, label="Test",  color=COLORS["test"],  alpha=0.9)
ax.set_xticks(x)
ax.set_xticklabels(PATTERN_ORDER, fontsize=11)
ax.set_ylabel("Number of Scenarios", fontsize=11)
ax.set_title("Scenario Counts per Pattern Type (Train vs Test)", fontsize=13, fontweight="bold")
ax.legend()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
for bar in ax.patches:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x() + bar.get_width() / 2, h + 10, f"{int(h):,}",
                ha="center", va="bottom", fontsize=7)
plt.tight_layout()
path_a = OUT / "scenario_counts_by_pattern.png"
fig.savefig(path_a, dpi=150)
plt.close()
print(f"  Saved: {path_a}")

# Full + rare-only split panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
for ax, bt, be, patterns, title in [
    (ax1, bars_train, bars_test, PATTERN_ORDER, "All Patterns (full scale)"),
    (ax2, bars_train[2:], bars_test[2:], PATTERN_ORDER[2:], "Rare Patterns Only"),
]:
    x_ax = np.arange(len(patterns))
    ax.bar(x_ax - w/2, bt, w, label="Train", color=COLORS["train"], alpha=0.9)
    ax.bar(x_ax + w/2, be, w, label="Test",  color=COLORS["test"],  alpha=0.9)
    ax.set_xticks(x_ax)
    ax.set_xticklabels(patterns, fontsize=10)
    ax.set_ylabel("Scenarios")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    for bar in ax.patches:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                    str(int(h)), ha="center", va="bottom", fontsize=9)
plt.tight_layout()
path_a2 = OUT / "scenario_counts_by_pattern_split.png"
fig.savefig(path_a2, dpi=150)
plt.close()
print(f"  Saved: {path_a2}")

# --- (b) Box plot: scenario size per pattern_type (log scale, train & test)
all_sc = pd.concat([
    train_sc.assign(split="train"),
    test_sc.assign(split="test")
], ignore_index=True)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, split_label in zip(axes, ["train", "test"]):
    sub = all_sc[all_sc["split"] == split_label]
    groups = [sub[sub["pattern_type"] == p]["n_txns"].values for p in PATTERN_ORDER]
    bp = ax.boxplot(groups, patch_artist=True, notch=False, showfliers=True,
                    medianprops=dict(color="black", linewidth=2))
    palette = ["#6EC6E6", "#F4A460", "#82C882", "#DDA0DD", "#FF8C8C"]
    for patch, color in zip(bp["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    ax.set_xticks(range(1, len(PATTERN_ORDER) + 1))
    ax.set_xticklabels(PATTERN_ORDER, fontsize=9, rotation=15)
    ax.set_ylabel("Txns per Scenario (log scale)")
    ax.set_title(f"Scenario Size Distribution — {split_label.capitalize()}", fontweight="bold")
    ax.set_yscale("log")
plt.tight_layout()
path_b = OUT / "scenario_size_boxplot.png"
fig.savefig(path_b, dpi=150)
plt.close()
print(f"  Saved: {path_b}")

# --- (c) Histogram: is_illicit balance at the SCENARIO level
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, split_label, sc_df in zip(axes, ["Train", "Test"], [train_sc, test_sc]):
    counts_ill = sc_df["is_illicit"].value_counts().sort_index()
    labels = ["Licit (0)", "Illicit (1)"]
    values = [int(counts_ill.get(0, 0)), int(counts_ill.get(1, 0))]
    bars_ = ax.bar(labels, values, color=["#5DA85D", "#D95F5F"], alpha=0.85, width=0.5)
    total = sum(values)
    for bar, val in zip(bars_, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                f"{val:,}\n({val/total:.1%})", ha="center", va="bottom", fontsize=10)
    ax.set_title(f"Scenario-Level is_illicit Balance — {split_label}", fontweight="bold")
    ax.set_ylabel("Scenario Count")
    ax.set_ylim(0, max(values) * 1.18)
plt.tight_layout()
path_c = OUT / "scenario_illicit_balance.png"
fig.savefig(path_c, dpi=150)
plt.close()
print(f"  Saved: {path_c}")

# ---------------------------------------------------------------------------
# 7. Write outputs/eda_report.md
# ---------------------------------------------------------------------------
sep("7. WRITING EDA REPORT")

train_ill_counts = train_sc["is_illicit"].value_counts().sort_index()
test_ill_counts  = test_sc["is_illicit"].value_counts().sort_index()
train_licit_pct   = train_ill_counts.get(0, 0) / len(train_sc) * 100
train_illicit_pct = train_ill_counts.get(1, 0) / len(train_sc) * 100
test_licit_pct    = test_ill_counts.get(0, 0)  / len(test_sc)  * 100
test_illicit_pct  = test_ill_counts.get(1, 0)  / len(test_sc)  * 100

homogeneity_status = "PASS — 0 violations" if not homogeneity_issues else \
    f"FAIL — violations found (see stdout for details)"
array_status = "PASS — 0 violations" if not violations else \
    f"FAIL — {len(violations)} array length mismatches"

md_lines = [
    "# EDA Report — SIH PS 146 Bitcoin AML Dataset",
    "",
    "> Auto-generated by `01_eda_and_validation.py`",
    f"> Dataset version: v2.0 | Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    "---",
    "## 1. Array Column Integrity",
    f"**Status**: {array_status}",
    "",
    "---",
    "## 2. Label Homogeneity",
    f"**Status**: {homogeneity_status}",
    "",
    "---",
    "## 3. Scenario Counts per Pattern Type",
    "",
    "| Pattern | Train Scenarios | Test Scenarios |",
    "|---------|:-:|:-:|",
]
for p in all_patterns:
    md_lines.append(f"| {p} | {train_counts.get(p, 0):,} | {test_counts.get(p, 0):,} |")
md_lines += [
    f"| **TOTAL** | **{train_counts.sum():,}** | **{test_counts.sum():,}** |",
    "",
    "> Class scarcity: layering=5 test scenarios, mixing=4 test scenarios. Use LOSOCV for typology eval.",
    "",
    "---",
    "## 4. Hard-Negative Exchange Scenarios",
    "",
    f"Normal/licit scenarios with >= 50 transactions: **{n_ge50}** (expected ~30).",
    "",
    "| scenario_id | n_txns |",
    "|-------------|--------|",
]
for _, row in top40.head(10).iterrows():
    md_lines.append(f"| {row['scenario_id']} | {row['n_txns']:,} |")

md_lines += [
    "",
    "---",
    "## 5. Scenario-Level is_illicit Balance",
    "",
    "| Split | Licit (0) | Illicit (1) | Licit % | Illicit % |",
    "|-------|-----------|-------------|---------|-----------|",
    f"| Train | {train_ill_counts.get(0,0):,} | {train_ill_counts.get(1,0):,} | "
    f"{train_licit_pct:.1f}% | {train_illicit_pct:.1f}% |",
    f"| Test  | {test_ill_counts.get(0,0):,} | {test_ill_counts.get(1,0):,} | "
    f"{test_licit_pct:.1f}% | {test_illicit_pct:.1f}% |",
    "",
    "---",
    "## 6. Plots",
    "- `scenario_counts_by_pattern.png`",
    "- `scenario_counts_by_pattern_split.png`",
    "- `scenario_size_boxplot.png`",
    "- `scenario_illicit_balance.png`",
    "",
    "_End of EDA report._",
]

report_path = OUT / "eda_report.md"
report_path.write_text("\n".join(md_lines), encoding="utf-8")
print(f"  Saved: {report_path}")

sep("SCENARIO-LEVEL is_illicit BALANCE")
print(f"  Train: {train_ill_counts.get(0,0):>6,} licit ({train_licit_pct:.1f}%) | "
      f"{train_ill_counts.get(1,0):>6,} illicit ({train_illicit_pct:.1f}%)")
print(f"  Test:  {test_ill_counts.get(0,0):>6,} licit ({test_licit_pct:.1f}%)  | "
      f"{test_ill_counts.get(1,0):>6,} illicit ({test_illicit_pct:.1f}%)")

sep("DONE — 01_eda_and_validation.py")
print(f"  Outputs in: {OUT}")
