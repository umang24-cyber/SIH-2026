"""
Data Parser for Bitcoin Dual-Layer Telemetry.
Handles JSON array deserialization, timestamp parsing, latency calculation,
and dynamic CSV/JSON/XML format parsing for live ingestion.
"""
import io
import json
import logging
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

def parse_json_column(val: Any) -> list:
    """Safely parse a JSON string representation of an array or return list."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass
        # Handle delimiter separated fallback (comma, semicolon, pipe)
        if ";" in s:
            return [x.strip() for x in s.split(";") if x.strip()]
        if "," in s:
            return [x.strip() for x in s.split(",") if x.strip()]
        if "|" in s:
            return [x.strip() for x in s.split("|") if x.strip()]
        if s:
            return [s]
    return []

def normalize_transaction_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize transaction dictionary keys and types for ingestion."""
    txid = int(d.get("txid", 0))
    if txid == 0:
        import time
        txid = int(time.time() * 1000) % 900000000 + 100000000

    ts = str(d.get("timestamp", "2026-09-06 12:00:00"))
    relay_ts = str(d.get("relay_timestamp") or ts)

    raw_in = d.get("input_addresses") or d.get("inputs", [])
    raw_out = d.get("output_addresses") or d.get("outputs", [])

    in_addrs = []
    in_amts = []
    if isinstance(raw_in, list):
        for item in raw_in:
            if isinstance(item, dict):
                in_addrs.append(str(item.get("address", "")))
                if "amount" in item:
                    in_amts.append(float(item["amount"]))
            else:
                in_addrs.append(str(item))
    else:
        in_addrs = parse_json_column(raw_in)

    out_addrs = []
    out_amts = []
    if isinstance(raw_out, list):
        for item in raw_out:
            if isinstance(item, dict):
                out_addrs.append(str(item.get("address", "")))
                if "amount" in item:
                    out_amts.append(float(item["amount"]))
            else:
                out_addrs.append(str(item))
    else:
        out_addrs = parse_json_column(raw_out)

    if not in_amts:
        raw_in_amts = parse_json_column(d.get("input_amounts", []))
        in_amts = [float(x) for x in raw_in_amts] if raw_in_amts else [2.5]
    if not out_amts:
        raw_out_amts = parse_json_column(d.get("output_amounts", []))
        out_amts = [float(x) for x in raw_out_amts] if raw_out_amts else [2.5]

    # Satoshi-safe normalization: Bitcoin hard cap is 21,000,000 BTC.
    # If values were recorded in satoshis (>= 21,000,000), convert to BTC (/ 1e8).
    if any(a > 21_000_000 for a in in_amts):
        in_amts = [round(a / 100_000_000.0, 8) for a in in_amts]
    if any(a > 21_000_000 for a in out_amts):
        out_amts = [round(a / 100_000_000.0, 8) for a in out_amts]

    # Calculate propagation delta if not present
    prop_delta = d.get("propagation_delta_ms")
    if prop_delta is None:
        try:
            t1 = pd.to_datetime(ts, utc=True)
            t2 = pd.to_datetime(relay_ts, utc=True)
            prop_delta = round(abs((t1 - t2).total_seconds() * 1000.0), 2)
        except Exception:
            prop_delta = 125.0

    return {
        "txid": txid,
        "timestamp": ts,
        "relay_timestamp": relay_ts,
        "input_addresses": [str(a) for a in in_addrs],
        "output_addresses": [str(a) for a in out_addrs],
        "input_amounts": in_amts,
        "output_amounts": out_amts,
        "fee_btc": float(d.get("fee_btc", 0.0001)),
        "script_type": str(d.get("script_type", "P2PKH")),
        "scenario_id": str(d.get("scenario_id") or f"custom_{txid}"),
        "relay_ip": str(d.get("relay_ip", "127.0.0.1")),
        "relay_port": int(d.get("relay_port", 8333)),
        "node_type": str(d.get("node_type", "residential")),
        "country_code": str(d.get("country_code", "US")),
        "asn": str(d.get("asn", "AS15169")),
        "isp": str(d.get("isp", "Standard Relay ISP")),
        "user_agent": str(d.get("user_agent", "/Satoshi:22.0.0/")),
        "propagation_delta_ms": float(prop_delta)
    }

def _scale_satoshi_list(amts: Any) -> list:
    """Scale satoshis to BTC if any amount exceeds Bitcoin max supply."""
    if not isinstance(amts, list):
        return amts
    try:
        float_amts = [float(x) for x in amts]
        if any(a > 21_000_000 for a in float_amts):
            return [round(a / 100_000_000.0, 8) for a in float_amts]
        return float_amts
    except Exception:
        return amts

def parse_and_enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses JSON array columns and computes dual-layer timing deltas for DataFrames.
    """
    array_cols = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]
    for col in array_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_json_column)
            
    if "input_amounts" in df.columns:
        df["input_amounts"] = df["input_amounts"].apply(_scale_satoshi_list)
    if "output_amounts" in df.columns:
        df["output_amounts"] = df["output_amounts"].apply(_scale_satoshi_list)

    if "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    if "relay_timestamp" in df.columns:
        df["relay_timestamp_dt"] = pd.to_datetime(df["relay_timestamp"], utc=True)
        
    if "timestamp_dt" in df.columns and "relay_timestamp_dt" in df.columns:
        df["propagation_delta_ms"] = (
            (df["timestamp_dt"] - df["relay_timestamp_dt"]).dt.total_seconds() * 1000.0
        ).round(2)
        
    return df

def parse_json_payload(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Parse JSON transaction or list of transactions into normalized dict records."""
    if isinstance(data, dict):
        return [normalize_transaction_dict(data)]
    if isinstance(data, list):
        return [normalize_transaction_dict(item) for item in data if isinstance(item, dict)]
    raise ValueError("Invalid JSON data format: expected object or array of objects.")

def parse_csv_bytes(csv_content: bytes) -> List[Dict[str, Any]]:
    """Parse raw CSV bytes into normalized transaction records."""
    df = pd.read_csv(io.BytesIO(csv_content))
    df = parse_and_enrich_dataframe(df)
    records = df.to_dict(orient="records")
    return [normalize_transaction_dict(r) for r in records]

def parse_xml_bytes(xml_content: bytes) -> List[Dict[str, Any]]:
    """Parse raw XML bytes containing <transaction> elements into normalized transaction records."""
    root = ET.fromstring(xml_content)
    records = []
    
    # Check if root is transaction or contains transaction tags
    elements = root.findall(".//transaction") if root.tag != "transaction" else [root]
    for el in elements:
        tx_dict = {}
        for child in el:
            tag = child.tag.lower()
            text = child.text.strip() if child.text else ""
            if tag in ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]:
                items = [li.text.strip() for li in child.findall("./item") if li.text]
                if items:
                    tx_dict[tag] = items
                else:
                    tx_dict[tag] = parse_json_column(text)
            else:
                tx_dict[tag] = text
        records.append(normalize_transaction_dict(tx_dict))
        
    return records
