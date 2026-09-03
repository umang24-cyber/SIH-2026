"""
validate.py — Ground-truth validation of detected candidate structures.

IMPORTANT: This module reads is_illicit and pattern_type from the merged
DataFrame ONLY for debugging/evaluation purposes. These columns are NEVER
passed to detection logic and have no influence on what gets detected.

Reports per-typology precision, recall, and F1, plus false-positive analysis.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)

# Maps our candidate_type strings to the ground-truth pattern_type values
_TYPE_MAP = {
    "peeling_chain": "peeling_chain",
    "layering":      "layering",
    "mixing":        "mixing",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_validation(
    candidates: list[CandidateStructure],
    df:         pd.DataFrame,
    output_path: Path = config.VALIDATION_REPORT_JSON,
) -> dict:
    """
    Evaluate detection quality against ground-truth labels.

    Parameters
    ----------
    candidates : list[CandidateStructure]
        All detected candidates.
    df : pd.DataFrame
        Merged DataFrame containing ``txid``, ``pattern_type``, ``scenario_id``.
    output_path : Path
        Where to write the validation report JSON.

    Returns
    -------
    dict
        The validation report (also written to output_path).
    """
    log.info("Running ground-truth validation …")

    # Build txid → pattern_type lookup
    txid_to_pattern: dict[int, str] = dict(
        zip(df["txid"].astype(int), df["pattern_type"].astype(str))
    )
    txid_to_scenario: dict[int, str] = dict(
        zip(df["txid"].astype(int), df["scenario_id"].astype(str))
    )

    # --- Per-candidate classification ---
    candidate_results = []
    for cand in candidates:
        patterns = [
            txid_to_pattern.get(txid, "unknown")
            for txid in cand.member_txids
        ]
        total = len(patterns)
        gt_type = _TYPE_MAP.get(cand.candidate_type, "")

        matching = sum(1 for p in patterns if p == gt_type)
        tp_ratio = matching / total if total > 0 else 0.0
        is_tp    = tp_ratio >= config.VALIDATION_TP_THRESHOLD

        # Most common pattern in this candidate (for false-positive labelling)
        from collections import Counter
        dominant_pattern = Counter(patterns).most_common(1)[0][0] if patterns else "unknown"

        scenarios = list({
            txid_to_scenario.get(txid, "")
            for txid in cand.member_txids
            if txid_to_scenario.get(txid)
        })

        candidate_results.append({
            "candidate_id":    cand.candidate_id,
            "candidate_type":  cand.candidate_type,
            "member_tx_count": total,
            "tp_ratio":        round(tp_ratio, 4),
            "is_true_positive": is_tp,
            "dominant_gt_pattern": dominant_pattern,
            "covered_scenarios": scenarios,
        })

    # --- Per-typology precision / recall ---
    typology_metrics = {}
    for our_type, gt_type in _TYPE_MAP.items():
        our_candidates = [c for c in candidate_results if c["candidate_type"] == our_type]
        tp = sum(1 for c in our_candidates if c["is_true_positive"])
        fp = len(our_candidates) - tp

        # Recall: how many ground-truth scenarios of this type did we cover?
        gt_scenarios = set(
            df.loc[df["pattern_type"] == gt_type, "scenario_id"].astype(str)
        )
        covered_gt = set()
        for c in our_candidates:
            if c["is_true_positive"]:
                covered_gt |= set(c["covered_scenarios"])
        covered_gt &= gt_scenarios

        recall    = len(covered_gt) / len(gt_scenarios) if gt_scenarios else 0.0
        precision = tp / len(our_candidates) if our_candidates else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )

        typology_metrics[our_type] = {
            "num_detected":       len(our_candidates),
            "true_positives":     tp,
            "false_positives":    fp,
            "precision":          round(precision, 4),
            "recall":             round(recall, 4),
            "f1":                 round(f1, 4),
            "gt_scenario_count":  len(gt_scenarios),
            "covered_gt_scenarios": len(covered_gt),
        }

    # --- False-positive analysis ---
    false_positives = [
        c for c in candidate_results if not c["is_true_positive"]
    ]
    fp_by_dominant = defaultdict(int)
    for c in false_positives:
        fp_by_dominant[c["dominant_gt_pattern"]] += 1

    report = {
        "summary": {
            "total_candidates":    len(candidates),
            "total_true_positives": sum(
                1 for c in candidate_results if c["is_true_positive"]
            ),
            "total_false_positives": len(false_positives),
        },
        "per_typology": typology_metrics,
        "false_positive_dominant_patterns": dict(fp_by_dominant),
        "per_candidate": candidate_results,
    }

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary to stdout
    log.info("=" * 60)
    log.info("VALIDATION REPORT SUMMARY")
    log.info("  Total candidates: %d", len(candidates))
    for ttype, metrics in typology_metrics.items():
        log.info(
            "  %-15s  detected=%d  TP=%d  FP=%d  P=%.2f  R=%.2f  F1=%.2f",
            ttype,
            metrics["num_detected"],
            metrics["true_positives"],
            metrics["false_positives"],
            metrics["precision"],
            metrics["recall"],
            metrics["f1"],
        )
    log.info("  FP dominant patterns: %s", dict(fp_by_dominant))
    log.info("  Full report -> %s", output_path)
    log.info("=" * 60)

    return report
