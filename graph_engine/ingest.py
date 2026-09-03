"""
ingest.py — Load, parse, validate, and merge the two CSV datasets.

Returns a single merged DataFrame. Every downstream module calls
``load_merged_df()`` instead of touching the CSVs directly.

JSON-array columns are expanded into Python lists in-place:
    input_addresses  → list[str]
    output_addresses → list[str]
    input_amounts    → list[float]
    output_amounts   → list[float]

Ground-truth columns (is_illicit, pattern_type) are loaded but NEVER
passed to detection logic — they are available only for validate.py.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from graph_engine import config

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_merged_df(
    blockchain_path: Path = config.BLOCKCHAIN_CSV,
    network_path: Path    = config.NETWORK_CSV,
) -> pd.DataFrame:
    """
    Load, parse, and inner-join the two CSVs on ``txid``.

    Returns
    -------
    pd.DataFrame
        One row per transaction (82,078 expected), with all JSON array columns
        parsed into Python lists and relay_timestamp parsed as datetime.
    """
    log.info("Loading blockchain CSV: %s", blockchain_path)
    bc = _load_blockchain(blockchain_path)

    log.info("Loading network CSV: %s", network_path)
    net = _load_network(network_path)

    log.info("Joining on txid …")
    merged = bc.merge(net, on="txid", how="inner", suffixes=("", "_net"))

    # Drop duplicate scenario_id / split columns brought in by the network side
    for col in ("scenario_id_net", "split_net"):
        if col in merged.columns:
            merged.drop(columns=[col], inplace=True)

    _validate(merged)

    log.info(
        "Ingest complete: %d rows, %d columns", len(merged), len(merged.columns)
    )
    return merged


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ARRAY_COLS = ("input_addresses", "output_addresses", "input_amounts", "output_amounts")


def _load_blockchain(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"txid": "int64"})

    # Parse JSON array columns
    for col in _ARRAY_COLS:
        if col not in df.columns:
            log.error("Expected column '%s' not found in %s", col, path)
            sys.exit(1)
        df[col] = df[col].apply(_parse_json_array(col))

    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    return df


def _load_network(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"txid": "int64"})

    # relay_timestamp has millisecond precision — parse carefully
    df["relay_timestamp"] = pd.to_datetime(df["relay_timestamp"], utc=True)

    return df


def _parse_json_array(col_name: str):
    """Return a per-cell parsing function that raises informatively on error."""
    def _parse(cell):
        try:
            result = json.loads(cell)
            if not isinstance(result, list):
                raise ValueError(f"Expected list, got {type(result)}")
            return result
        except (json.JSONDecodeError, ValueError) as exc:
            # We don't have txid here, but the row index will appear in the
            # stack trace. Raise so validate() can catch global failures.
            raise ValueError(
                f"JSON parse failure in column '{col_name}': {cell!r}"
            ) from exc
    return _parse


def _validate(df: pd.DataFrame) -> None:
    """Run post-merge integrity assertions and log warnings for soft issues."""
    errors: list[str] = []

    # --- Hard assertions ---
    expected_rows = 82_078
    if len(df) != expected_rows:
        errors.append(
            f"Row count mismatch: expected {expected_rows}, got {len(df)}"
        )

    if df["txid"].duplicated().any():
        n = df["txid"].duplicated().sum()
        errors.append(f"{n} duplicate txids after merge")

    required_cols = [
        "txid", "timestamp", "input_addresses", "output_addresses",
        "input_amounts", "output_amounts", "fee_btc", "script_type",
        "relay_timestamp", "relay_ip", "relay_port", "node_type",
        "country_code", "asn", "isp", "user_agent",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing columns after merge: {missing}")

    if errors:
        for msg in errors:
            log.error("INGEST ERROR: %s", msg)
        sys.exit(1)

    # --- Array-length alignment checks ---
    bad_ia = df.apply(
        lambda r: len(r["input_addresses"]) != len(r["input_amounts"]), axis=1
    )
    if bad_ia.any():
        n = bad_ia.sum()
        log.warning(
            "%d rows have mismatched input_addresses / input_amounts lengths", n
        )

    bad_oa = df.apply(
        lambda r: len(r["output_addresses"]) != len(r["output_amounts"]), axis=1
    )
    if bad_oa.any():
        n = bad_oa.sum()
        log.warning(
            "%d rows have mismatched output_addresses / output_amounts lengths", n
        )

    # --- Accounting identity (soft check) ---
    df["_sum_in"]  = df["input_amounts"].apply(sum)
    df["_sum_out"] = df["output_amounts"].apply(sum)
    df["_residual"] = (df["_sum_in"] - df["_sum_out"] - df["fee_btc"]).abs()
    bad_accounting = (df["_residual"] > 1e-6).sum()
    if bad_accounting:
        log.warning(
            "%d rows violate accounting identity (residual > 1e-6 BTC)",
            bad_accounting,
        )
    df.drop(columns=["_sum_in", "_sum_out", "_residual"], inplace=True)

    # --- Timing check: relay_timestamp must be < timestamp ---
    timing_violations = (df["relay_timestamp"] >= df["timestamp"]).sum()
    if timing_violations:
        log.warning(
            "%d rows have relay_timestamp >= block timestamp", timing_violations
        )

    log.info(
        "Validation passed: %d rows, no hard errors. "
        "Typology distribution — %s",
        len(df),
        df["pattern_type"].value_counts().to_dict() if "pattern_type" in df.columns else "n/a",
    )
