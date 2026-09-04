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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

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
    # Soft row count check — no hardcoded expected count (dataset size varies across versions)
    if len(df) < 100:
        errors.append(
            f"Row count suspiciously low: {len(df)} (expected thousands)"
        )
    else:
        log.info("Row count: %d", len(df))

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


# ===========================================================================
# RawTxRecord adapter layer
# ===========================================================================
#
# Design intent
# -------------
# This section is the *single schema-change seam* for Phase 1.  When the real
# dataset arrives with finalised column names, only ``DEFAULT_FIELD_MAP`` (and
# possibly ``_parse_array_field``) needs updating; nothing downstream changes.
#
# Parallel API — does NOT replace load_merged_df()
# ------------------------------------------------
# The existing DataFrame path (load_merged_df → build_full_graph(df)) is
# preserved unchanged.  The new path is:
#
#     records = iter_records(df)                   # yields RawTxRecord objects
#     G = build_full_graph_from_records(records)   # in graph_build.py
#
# Both paths produce equivalent graphs.
# ===========================================================================


# ---------------------------------------------------------------------------
# Atomic sub-types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalletEntry:
    """A single wallet address paired with its BTC amount in one transaction."""
    address: str
    amount_btc: float


@dataclass(frozen=True)
class NetworkMeta:
    """
    P2P network-layer metadata for one transaction broadcast event.

    All fields map to the ``network_metadata`` category described in the spec.
    """
    relay_ip: str
    relay_timestamp: datetime
    relay_port: int
    node_type: str          # infrastructure classification (residential, tor_exit_node, …)
    country_code: str       # ISO 3166-1 alpha-2
    asn: str                # e.g. "AS55836"
    isp: str
    user_agent: str


# ---------------------------------------------------------------------------
# Canonical internal transaction type
# ---------------------------------------------------------------------------

@dataclass
class RawTxRecord:
    """
    One parsed Bitcoin transaction, schema-decoupled from the raw CSV.

    This is the canonical internal shape consumed by
    ``graph_build.build_full_graph_from_records``.  Schema changes only touch
    the adapter (``FieldMap`` + ``adapt_row``).

    Required fields
    ---------------
    txid        : int
    timestamp   : datetime   — block-confirmation time (UTC)
    inputs      : list[WalletEntry]   — at least 1 entry
    outputs     : list[WalletEntry]   — at least 1 entry
    fee_btc     : float               — must be >= 0
    script_type : str
    network     : NetworkMeta

    Optional passthrough (present when source data has them)
    --------------------------------------------------------
    scenario_id  : str | None
    split        : str | None
    is_illicit   : int | None   — ground-truth; NEVER passed to detectors
    pattern_type : str | None   — ground-truth; NEVER passed to detectors
    """

    # --- Required ---
    txid: int
    timestamp: datetime
    inputs: list[WalletEntry]
    outputs: list[WalletEntry]
    fee_btc: float
    script_type: str
    network: NetworkMeta

    # --- Optional passthrough ---
    scenario_id:  Optional[str] = None
    split:        Optional[str] = None
    is_illicit:   Optional[int] = None
    pattern_type: Optional[str] = None

    # --- Derived convenience properties ---

    @property
    def input_addresses(self) -> list[str]:
        return [e.address for e in self.inputs]

    @property
    def output_addresses(self) -> list[str]:
        return [e.address for e in self.outputs]

    @property
    def input_amounts(self) -> list[float]:
        return [e.amount_btc for e in self.inputs]

    @property
    def output_amounts(self) -> list[float]:
        return [e.amount_btc for e in self.outputs]

    @property
    def total_input_btc(self) -> float:
        return sum(e.amount_btc for e in self.inputs)

    @property
    def total_output_btc(self) -> float:
        return sum(e.amount_btc for e in self.outputs)


# ---------------------------------------------------------------------------
# FieldMap — the schema-change seam
# ---------------------------------------------------------------------------

@dataclass
class FieldMap:
    """
    Maps logical field categories to the actual column names in the raw
    DataFrame.

    When the real dataset arrives with different column names, update only
    ``DEFAULT_FIELD_MAP``; all adapter logic is written against this map.

    Array fields (``input_addresses``, etc.) are expected to be Python lists
    already parsed by ``_load_blockchain`` before the adapter runs, but
    ``adapt_row`` also accepts raw JSON strings as a fallback.
    """

    # --- Transaction identity ---
    txid:        str = "txid"
    timestamp:   str = "timestamp"

    # --- Input side (parallel arrays, 1:1 indexed) ---
    input_addresses: str = "input_addresses"
    input_amounts:   str = "input_amounts"

    # --- Output side (parallel arrays, 1:1 indexed) ---
    output_addresses: str = "output_addresses"
    output_amounts:   str = "output_amounts"

    # --- Transaction-level fee + script ---
    fee_btc:     str = "fee_btc"
    script_type: str = "script_type"

    # --- Network / broadcast metadata ---
    relay_ip:        str = "relay_ip"
    relay_timestamp: str = "relay_timestamp"
    relay_port:      str = "relay_port"
    node_type:       str = "node_type"
    country_code:    str = "country_code"
    asn:             str = "asn"
    isp:             str = "isp"
    user_agent:      str = "user_agent"

    # --- Optional passthrough ---
    scenario_id:  str = "scenario_id"
    split:        str = "split"
    is_illicit:   str = "is_illicit"
    pattern_type: str = "pattern_type"


#: Pre-built map for the v2 dataset described in DATA_DICTIONARY.md.
#: Update only this object when real schema column names arrive.
DEFAULT_FIELD_MAP: FieldMap = FieldMap()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_record(rec: RawTxRecord) -> list[str]:
    """
    Validate a ``RawTxRecord`` and return a list of hard-error strings.

    An empty return list means the record is valid.

    Hard failures (cause ``adapt_row`` to return None)
    ---------------------------------------------------
    - Missing / null timestamp
    - Empty inputs list
    - Empty outputs list
    - Negative fee

    Soft warnings (record passes through, warning logged)
    ------------------------------------------------------
    - An address appears on both input and output sides (UTXO change reuse is
      a legitimate Bitcoin pattern; graph layer handles self-loop skipping).
    - Accounting identity violation (|sum_in - sum_out - fee| > 1e-6 BTC).
    """
    errors: list[str] = []

    if rec.timestamp is None:
        errors.append("timestamp is None")

    if not rec.inputs:
        errors.append("inputs list is empty (no input wallets)")

    if not rec.outputs:
        errors.append("outputs list is empty (no output wallets)")

    if rec.fee_btc < 0:
        errors.append(f"fee_btc is negative: {rec.fee_btc}")

    if errors:
        # Hard failures — soft checks are not meaningful without inputs/outputs
        return errors

    # --- Soft checks (warn; do NOT add to error list) ---

    overlap = set(rec.input_addresses) & set(rec.output_addresses)
    if overlap:
        log.warning(
            "txid %d: address(es) appear on both input and output sides "
            "(UTXO change-address reuse — valid, passing through): %s",
            rec.txid,
            overlap,
        )

    residual = abs(rec.total_input_btc - rec.total_output_btc - rec.fee_btc)
    if residual > 1e-6:
        log.warning(
            "txid %d: accounting identity violated "
            "(|in - out - fee| = %.8f BTC > 1e-6)",
            rec.txid, residual,
        )

    return errors  # empty → valid


# ---------------------------------------------------------------------------
# Row adapter
# ---------------------------------------------------------------------------

def _get_field(row_or_dict, field_name: str, default=None):
    """Unified attribute/key accessor for both namedtuples and plain dicts."""
    if isinstance(row_or_dict, dict):
        return row_or_dict.get(field_name, default)
    val = getattr(row_or_dict, field_name, default)
    return default if val is None else val


def _parse_array_field(raw, field_name: str, txid) -> Optional[list]:
    """
    Normalise an array field that may arrive as a Python list (already parsed
    by ``_load_blockchain``) or as a raw JSON string.

    Returns the list on success, None on failure.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            result = json.loads(raw)
            if not isinstance(result, list):
                raise ValueError(f"Expected list, got {type(result).__name__}")
            return result
        except (json.JSONDecodeError, ValueError) as exc:
            log.error(
                "txid %s: JSON parse failure in '%s': %r — %s",
                txid, field_name, raw, exc,
            )
            return None
    log.error(
        "txid %s: unexpected type for '%s': %s",
        txid, field_name, type(raw).__name__,
    )
    return None


def adapt_row(
    row,
    field_map: FieldMap = DEFAULT_FIELD_MAP,
) -> Optional[RawTxRecord]:
    """
    Convert one raw DataFrame row (namedtuple from ``itertuples``) or a plain
    dict into a ``RawTxRecord``.

    Returns ``None`` if the record fails hard validation.  Soft issues
    (change-address overlap, accounting) are logged as warnings and the record
    is returned normally.

    Parameters
    ----------
    row : namedtuple | dict
        A single row from a pandas DataFrame (``itertuples`` output) or a
        plain dict for testing / synthetic data.
    field_map : FieldMap
        Column-name mapping.  Defaults to ``DEFAULT_FIELD_MAP`` (v2 schema).

    Returns
    -------
    RawTxRecord | None
    """
    fm = field_map
    txid_raw = _get_field(row, fm.txid)

    try:
        txid = int(txid_raw)
    except (TypeError, ValueError):
        log.error(
            "adapt_row: cannot parse txid from value %r — skipping row", txid_raw
        )
        return None

    # --- Timestamp ---
    ts_raw = _get_field(row, fm.timestamp)
    if ts_raw is None:
        log.error("txid %d: timestamp is missing — skipping", txid)
        return None
    if isinstance(ts_raw, datetime):
        timestamp = ts_raw
    else:
        try:
            timestamp = pd.Timestamp(ts_raw).to_pydatetime()
        except Exception as exc:
            log.error(
                "txid %d: cannot parse timestamp %r — skipping: %s",
                txid, ts_raw, exc,
            )
            return None

    # --- Array fields ---
    in_addrs  = _parse_array_field(
        _get_field(row, fm.input_addresses),  fm.input_addresses,  txid
    )
    in_amts   = _parse_array_field(
        _get_field(row, fm.input_amounts),    fm.input_amounts,    txid
    )
    out_addrs = _parse_array_field(
        _get_field(row, fm.output_addresses), fm.output_addresses, txid
    )
    out_amts  = _parse_array_field(
        _get_field(row, fm.output_amounts),   fm.output_amounts,   txid
    )

    if any(x is None for x in (in_addrs, in_amts, out_addrs, out_amts)):
        log.error("txid %d: array field parse failure — skipping", txid)
        return None

    if len(in_addrs) != len(in_amts):
        log.error(
            "txid %d: input_addresses length (%d) != input_amounts length (%d) — skipping",
            txid, len(in_addrs), len(in_amts),
        )
        return None

    if len(out_addrs) != len(out_amts):
        log.error(
            "txid %d: output_addresses length (%d) != output_amounts length (%d) — skipping",
            txid, len(out_addrs), len(out_amts),
        )
        return None

    inputs  = [
        WalletEntry(address=str(a), amount_btc=float(v))
        for a, v in zip(in_addrs, in_amts)
    ]
    outputs = [
        WalletEntry(address=str(a), amount_btc=float(v))
        for a, v in zip(out_addrs, out_amts)
    ]

    # --- Scalar blockchain fields ---
    try:
        fee_btc = float(_get_field(row, fm.fee_btc, 0.0))
    except (TypeError, ValueError):
        log.error("txid %d: cannot parse fee_btc — skipping", txid)
        return None

    script_type = str(_get_field(row, fm.script_type, "unknown"))

    # --- Network metadata ---
    relay_ts_raw = _get_field(row, fm.relay_timestamp)
    if relay_ts_raw is None:
        log.error("txid %d: relay_timestamp is missing — skipping", txid)
        return None
    if isinstance(relay_ts_raw, datetime):
        relay_timestamp = relay_ts_raw
    else:
        try:
            relay_timestamp = pd.Timestamp(relay_ts_raw).to_pydatetime()
        except Exception as exc:
            log.error(
                "txid %d: cannot parse relay_timestamp %r — skipping: %s",
                txid, relay_ts_raw, exc,
            )
            return None

    try:
        relay_port = int(_get_field(row, fm.relay_port, 8333))
    except (TypeError, ValueError):
        relay_port = 8333

    network = NetworkMeta(
        relay_ip        = str(_get_field(row, fm.relay_ip,        "")),
        relay_timestamp = relay_timestamp,
        relay_port      = relay_port,
        node_type       = str(_get_field(row, fm.node_type,       "unknown")),
        country_code    = str(_get_field(row, fm.country_code,    "")),
        asn             = str(_get_field(row, fm.asn,             "")),
        isp             = str(_get_field(row, fm.isp,             "")),
        user_agent      = str(_get_field(row, fm.user_agent,      "")),
    )

    # --- Optional passthrough ---
    scenario_id_v  = _get_field(row, fm.scenario_id)
    split_v        = _get_field(row, fm.split)
    is_illicit_v   = _get_field(row, fm.is_illicit)
    pattern_type_v = _get_field(row, fm.pattern_type)

    # Safely coerce is_illicit to int or None
    if is_illicit_v is not None:
        try:
            is_illicit_v = int(is_illicit_v)
        except (TypeError, ValueError):
            is_illicit_v = None

    rec = RawTxRecord(
        txid         = txid,
        timestamp    = timestamp,
        inputs       = inputs,
        outputs      = outputs,
        fee_btc      = fee_btc,
        script_type  = script_type,
        network      = network,
        scenario_id  = str(scenario_id_v)  if scenario_id_v  is not None else None,
        split        = str(split_v)         if split_v         is not None else None,
        is_illicit   = is_illicit_v,
        pattern_type = str(pattern_type_v) if pattern_type_v is not None else None,
    )

    errors = validate_record(rec)
    if errors:
        log.error(
            "txid %d: hard validation failed — skipping. Errors: %s",
            txid, errors,
        )
        return None

    return rec


# ---------------------------------------------------------------------------
# Public iterator API
# ---------------------------------------------------------------------------

def iter_records(
    df: pd.DataFrame,
    field_map: FieldMap = DEFAULT_FIELD_MAP,
) -> Iterator[RawTxRecord]:
    """
    Yield valid ``RawTxRecord`` objects from a merged DataFrame.

    Invalid rows (failed hard validation) are skipped and counted.  A summary
    log line is emitted at the end.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``load_merged_df()`` (or any DataFrame conforming to
        ``field_map``).
    field_map : FieldMap
        Column-name mapping.  Defaults to ``DEFAULT_FIELD_MAP``.

    Yields
    ------
    RawTxRecord
    """
    total    = 0
    rejected = 0

    for row in df.itertuples(index=False):
        total += 1
        rec = adapt_row(row, field_map)
        if rec is None:
            rejected += 1
            continue
        yield rec

    if rejected:
        log.warning(
            "iter_records: rejected %d / %d rows (%.1f%%)",
            rejected, total, 100.0 * rejected / max(total, 1),
        )
    else:
        log.info("iter_records: all %d rows passed validation", total)
