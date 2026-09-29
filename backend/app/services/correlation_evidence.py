"""Shared exact-transaction association and timestamp evidence.

The timing check is descriptive, never a probability or a substitute for an
exact original transaction ID. Relay observation does not establish sender.
"""
from datetime import datetime, timezone
import math
from typing import Any


def original_id(record: dict[str, Any]) -> str:
    value = record.get("transaction_hash", record.get("txid"))
    if value is None or isinstance(value, bool):
        return ""
    return str(value).strip()


def parse_time(value: Any) -> datetime | None:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        return None
    try:
        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                return None
            result = datetime.fromtimestamp(value, timezone.utc)
        else:
            text = str(value).strip()
            result = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if result.tzinfo is None:
                result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError):
        return None


def observation(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("relay_timestamp")
    observed = record.get("relay_timestamp_observed", True)
    parsed = parse_time(value) if observed else None
    return {
        "relay_timestamp": parsed.isoformat().replace("+00:00", "Z") if parsed else None,
        "relay_ip": record.get("relay_ip") if record.get("relay_ip_observed", True) else None,
        "asn": record.get("asn") if record.get("asn_observed", True) else None,
        "node_type": record.get("node_type") if record.get("node_type_observed", True) else None,
    }


def evidence(tx_hash: str, ledger: dict[str, Any] | None,
             relays: list[dict[str, Any]], window_seconds: float,
             correlation_confidence: float | None = None) -> dict[str, Any]:
    if not math.isfinite(window_seconds) or window_seconds <= 0:
        raise ValueError("max_window_seconds must be finite and greater than zero")
    ledger_time = parse_time(ledger.get("timestamp")) if ledger and ledger.get("timestamp_observed", True) else None
    observations = [observation(relay) for relay in relays]
    valid = [parse_time(item["relay_timestamp"]) for item in observations if item["relay_timestamp"]]
    # Multiple observers can see the same transaction; use earliest observation
    # for the descriptive interval, and preserve every observation for review.
    earliest = min(valid) if valid else None
    delta = round((ledger_time - earliest).total_seconds(), 3) if ledger_time and earliest else None
    if delta is None:
        timing_status = "MISSING_TIMESTAMP"
    elif delta < 0:
        timing_status = "CLOCK_ORDER_ISSUE"
    elif delta > window_seconds:
        timing_status = "OUTSIDE_WINDOW"
    else:
        timing_status = "WITHIN_WINDOW"
    matched = ledger is not None and bool(relays)
    reason = (
        "Exact original transaction ID appears in both streams; timing is supporting evidence only."
        if matched else "Original transaction ID occurs in only one stream."
    )
    return {
        "transaction_hash": tx_hash,
        "txid": ledger.get("txid") if ledger else None,
        "match_method": "EXACT_TRANSACTION_ID" if matched else "NONE",
        "match_status": "MATCHED" if matched else "UNMATCHED",
        "ledger_timestamp": ledger_time.isoformat().replace("+00:00", "Z") if ledger_time else None,
        "observations": observations,
        "timing_delta_seconds": delta,
        "timing_status": timing_status,
        "correlation_confidence": correlation_confidence,
        "attribution_status": "RELAY_OBSERVED_ORIGIN_UNVERIFIED" if relays else "NO_RELAY_OBSERVED",
        "reasons": [reason] + (["Observed timestamps are missing or invalid."] if delta is None else [])
                   + (["Timestamps indicate relay after ledger event; inspect clock/source definitions."] if delta is not None and delta < 0 else [])
                   + (["Gap exceeds configured display window; exact-ID association is retained."] if delta is not None and delta > window_seconds else []),
    }
