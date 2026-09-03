"""
Data Parser for Bitcoin Dual-Layer Telemetry.
Handles JSON array deserialization, timestamp parsing, and latency calculation.
"""
import json
import logging
import pandas as pd
from typing import Any

logger = logging.getLogger(__name__)

def parse_json_column(val: Any) -> list:
    """Safely parse a JSON string representation of an array."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON value: {val}")
            return []
    return []

def parse_and_enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses JSON array columns and computes dual-layer timing deltas.
    
    Columns parsed:
      - input_addresses: list[str]
      - output_addresses: list[str]
      - input_amounts: list[float]
      - output_amounts: list[float]
      - timestamp: pd.Timestamp (UTC)
      - relay_timestamp: pd.Timestamp (UTC)
      - propagation_delta_ms: float (ms difference between block time and P2P broadcast)
    """
    array_cols = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]
    for col in array_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_json_column)
            
    # Timestamp conversion
    if "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    if "relay_timestamp" in df.columns:
        df["relay_timestamp_dt"] = pd.to_datetime(df["relay_timestamp"], utc=True)
        
    # Latency calculation in milliseconds
    if "timestamp_dt" in df.columns and "relay_timestamp_dt" in df.columns:
        df["propagation_delta_ms"] = (
            (df["timestamp_dt"] - df["relay_timestamp_dt"]).dt.total_seconds() * 1000.0
        ).round(2)
        
    return df
