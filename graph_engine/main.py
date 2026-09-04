"""
main.py — CLI entry point for the graph engine pipeline.

Usage
-----
    python -m graph_engine.main [--data-dir PATH] [--output-dir PATH] [--no-validate]

Steps
-----
1. Ingest     — Load and merge CSVs, validate integrity.
2. Build      — Construct full heterogeneous graph + wallet projection.
3. Detect     — Run all three typology detectors.
4. Features   — Enrich candidates with network-layer features.
5. Export     — Write graph_export.json and candidates_ml_handoff.csv.
6. Validate   — Compare against ground truth (skipped with --no-validate).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("graph_engine.main")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="SIH PS 146 — Bitcoin AML Graph Engine"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing blockchain_transactions.csv and network_metadata.csv "
             "(default: data/processed relative to project root)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output files (default: output/ relative to project root)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip ground-truth validation step (faster, no label columns needed)",
    )
    args = parser.parse_args(argv)

    # Override config paths if CLI args were supplied
    from graph_engine import config
    if args.data_dir:
        config.BLOCKCHAIN_CSV = args.data_dir / "blockchain_transactions.csv"
        config.NETWORK_CSV    = args.data_dir / "network_metadata.csv"
    if args.output_dir:
        config.GRAPH_EXPORT_JSON      = args.output_dir / "graph_export.json"
        config.ML_HANDOFF_CSV         = args.output_dir / "candidates_ml_handoff.csv"
        config.VALIDATION_REPORT_JSON = args.output_dir / "validation_report.json"

    t_total = time.perf_counter()

    # ------------------------------------------------------------------
    # Step 1 — Ingest
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("STEP 1 / 6 — INGEST")
    t0 = time.perf_counter()
    from graph_engine import ingest
    df = ingest.load_merged_df()
    log.info("  Done in %.1fs", time.perf_counter() - t0)

    # ------------------------------------------------------------------
    # Step 2 — Build graph
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("STEP 2 / 6 — GRAPH BUILD")
    t0 = time.perf_counter()
    from graph_engine import graph_build
    G = graph_build.build_full_graph(df)
    P = graph_build.build_wallet_projection(G)
    log.info("  Done in %.1fs", time.perf_counter() - t0)

    # ------------------------------------------------------------------
    # Step 3 — Typology detection
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("STEP 3 / 6 — TYPOLOGY DETECTION")
    t0 = time.perf_counter()

    from graph_engine.detectors import peeling_chain, layering, mixing

    peel_candidates   = peeling_chain.detect(G, P)
    layer_candidates  = layering.detect(G, P)
    mix_candidates    = mixing.detect(G, P)

    all_candidates = peel_candidates + layer_candidates + mix_candidates
    log.info(
        "  Detected: %d peeling chains, %d layering, %d mixing clusters  (%.1fs)",
        len(peel_candidates), len(layer_candidates), len(mix_candidates),
        time.perf_counter() - t0,
    )

    # ------------------------------------------------------------------
    # Step 4 — Feature enrichment
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("STEP 4 / 6 — FEATURE ENRICHMENT")
    t0 = time.perf_counter()
    from graph_engine import features as feat_module
    features_df = feat_module.enrich_and_build_dataframe(all_candidates, G)
    log.info("  Done in %.1fs  (%d candidates)", time.perf_counter() - t0, len(features_df))

    # ------------------------------------------------------------------
    # Step 5 — Export
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("STEP 5 / 6 — EXPORT")
    t0 = time.perf_counter()
    from graph_engine import export as export_module
    export_module.export_graph_json(G, all_candidates)
    export_module.export_ml_handoff_csv(features_df)
    log.info("  Done in %.1fs", time.perf_counter() - t0)

    # ------------------------------------------------------------------
    # Step 6 — Validation (optional)
    # ------------------------------------------------------------------
    if not args.no_validate:
        log.info("=" * 60)
        log.info("STEP 6 / 6 — GROUND-TRUTH VALIDATION")
        t0 = time.perf_counter()
        from graph_engine import validate as validate_module
        validate_module.run_validation(all_candidates, df)
        log.info("  Done in %.1fs", time.perf_counter() - t0)
    else:
        log.info("STEP 6 / 6 — VALIDATION SKIPPED (--no-validate)")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed = time.perf_counter() - t_total
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE in %.1fs", elapsed)
    log.info("  graph_export.json       -> %s", config.GRAPH_EXPORT_JSON)
    log.info("  candidates_ml_handoff   -> %s", config.ML_HANDOFF_CSV)
    if not args.no_validate:
        log.info("  validation_report.json  -> %s", config.VALIDATION_REPORT_JSON)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
