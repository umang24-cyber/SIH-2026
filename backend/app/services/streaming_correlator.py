"""
Streaming Temporal Correlation Engine for Asynchronous Blockchain & P2P Telemetry.
100% Offline / Air-Gapped Linux & WSL2 compliant.

Solves the core forensic challenge:
1. Reconciles raw, unsorted, out-of-order P2P Mempool frames and Mined Block events in a sliding temporal buffer.
2. Generates real-time Server-Sent Events (SSE) telemetry streams with instant heuristic risk scoring.
"""
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from backend.app.services.data_service import data_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.ml_service import ml_service
from backend.app.services.correlation_evidence import evidence, original_id
import math

logger = logging.getLogger(__name__)

class StreamingCorrelator:
    def __init__(self):
        self.default_window_sec: float = 60.0

    async def generate_replay_stream(
        self,
        speed_tx_per_sec: float = 15.0,
        max_events: int = 100,
        scenario_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Async generator for Server-Sent Events (SSE).
        Streams live transaction frames with real-time heuristic scoring and alert flags.
        """
        delay = 1.0 / max(1.0, min(speed_tx_per_sec, 100.0))
        
        # Select transaction pool
        if scenario_id and scenario_id in data_service.scenario_tx_map:
            tx_ids = data_service.scenario_tx_map[scenario_id][:max_events]
        else:
            tx_ids = list(data_service.txid_map.keys())[:max_events]

        event_counter = 0
        for txid in tx_ids:
            tx = data_service.txid_map.get(txid)
            if not tx:
                continue

            event_counter += 1
            node_type = str(tx.get("node_type", "residential"))
            is_tor = node_type == "tor_exit_node" or bool(tx.get("is_tor", False))
            
            # Real-time feature inference
            ml_pred = ml_service.predict_risk(txid)
            risk_score = ml_pred.get("risk_score", 0.0)
            
            # Check active heuristic alerts for this tx
            typology_flags = typology_detector.get_typologies_for_tx(txid)
            
            is_critical = risk_score >= 0.75 or is_tor or len(typology_flags) > 0

            delta_ms = float(tx.get("propagation_delta_ms", 0.0))
            payload = {
                "event_id": event_counter,
                "event_type": "CRITICAL_ALERT" if is_critical else "TX_STREAM",
                "timestamp": str(tx.get("timestamp", "")),
                "txid": txid,
                "amount_btc": float(sum(tx.get("output_amounts", [0.0]))),
                "inputs_count": len(tx.get("input_addresses", [])),
                "outputs_count": len(tx.get("output_addresses", [])),
                "network": {
                    "ip": tx.get("relay_ip", "0.0.0.0"),
                    "isp": tx.get("isp", "Unknown"),
                    "country": tx.get("country_code", "US"),
                    "node_type": node_type,
                    "is_tor": is_tor,
                    "delta_t_sec": round(delta_ms / 1000.0, 3)
                },
                "risk_assessment": {
                    "risk_score": risk_score,
                    "risk_level": "CRITICAL" if risk_score >= 0.75 else ("HIGH" if risk_score >= 0.5 else "LOW"),
                    "typologies": typology_flags,
                    "is_alert": is_critical
                }
            }

            # Format as standard Server-Sent Event (SSE)
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(delay)

    def reconcile_asynchronous_streams(
        self,
        mempool_stream: List[Dict[str, Any]],
        block_stream: List[Dict[str, Any]],
        max_window_seconds: float = 120.0
    ) -> Dict[str, Any]:
        """
        Temporal Sliding-Window Correlation Engine:
        Accepts two raw, unsorted streams (P2P gossip frames & Mined Block frames),
        simulates arrival jitter, and reconstructs the cross-layer transaction graph.
        """
        start_time = time.perf_counter()
        
        if not math.isfinite(max_window_seconds) or max_window_seconds <= 0:
            raise ValueError("max_window_seconds must be finite and greater than zero")
        mempool_buffer: Dict[str, List[Dict[str, Any]]] = {}
        block_buffer: Dict[str, Dict[str, Any]] = {}
        conflicting_blocks: set[str] = set()
        
        correlated_events: List[Dict[str, Any]] = []
        timing_deltas: List[float] = []
        orphan_mempool_packets: int = 0
        orphan_block_events: int = 0
        
        # Ingest mempool stream
        for m in mempool_stream:
            txid = original_id(m)
            if txid:
                mempool_buffer.setdefault(txid, []).append(m)

        # Buffer by the original ID, regardless of arrival order.
        for b in block_stream:
            txid = original_id(b)
            if not txid:
                continue
            if txid in block_buffer:
                if block_buffer[txid] != b:
                    conflicting_blocks.add(txid)
                continue
            block_buffer[txid] = b

        for txid, b in block_buffer.items():
            if txid in conflicting_blocks:
                item = evidence(txid, {"txid": b.get("txid"), "timestamp": b.get("block_timestamp")}, mempool_buffer.get(txid, []), max_window_seconds)
                item["match_status"] = "CONFLICTING"
                item["reasons"].append("Contradictory block records share a transaction ID; not counted as a match.")
                correlated_events.append({**item, "correlation_status": "CONFLICTING"})
                continue
            if txid in mempool_buffer:
                relays = mempool_buffer[txid]
                item = evidence(txid, {"txid": b.get("txid"), "timestamp": b.get("block_timestamp")}, relays, max_window_seconds)
                delta_t = item["timing_delta_seconds"]
                if delta_t is not None and item["timing_status"] == "WITHIN_WINDOW":
                    timing_deltas.append(delta_t)
                correlated_events.append({
                    **item, "txid": b.get("txid"), "correlation_status": "MATCHED",
                    "relay_ip": item["observations"][0]["relay_ip"],
                    "asn": item["observations"][0]["asn"],
                    "is_tor": relays[0].get("is_tor") is True,
                    "btc_value": float(b.get("btc_value", 0.0)),
                    "block_height": b.get("block_height", 0),
                })
            else:
                orphan_block_events += 1

        for txid in mempool_buffer:
            if txid not in block_buffer:
                orphan_mempool_packets += 1

        for txid, block in block_buffer.items():
            if txid not in mempool_buffer and txid not in conflicting_blocks:
                item = evidence(txid, {"txid": block.get("txid"), "timestamp": block.get("block_timestamp")}, [], max_window_seconds)
                correlated_events.append({**item, "correlation_status": "UNMATCHED"})
        for txid, relays in mempool_buffer.items():
            if txid not in block_buffer:
                item = evidence(txid, None, relays, max_window_seconds)
                correlated_events.append({**item, "correlation_status": "UNMATCHED"})

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_delta = sum(timing_deltas) / len(timing_deltas) if timing_deltas else 0.0
        matched = sum(item["match_status"] == "MATCHED" for item in correlated_events)
        match_rate = (matched / max(1, len(block_buffer))) * 100.0

        return {
            "reconciliation_summary": {
                "total_mempool_frames": len(mempool_stream),
                "total_block_events": len(block_stream),
                "correlated_matches": matched,
                "within_window_matches": len(timing_deltas),
                "timing_issue_count": matched - len(timing_deltas),
                "conflicting_records": len(conflicting_blocks),
                "match_rate_percent": round(match_rate, 2),
                "orphan_mempool_packets": orphan_mempool_packets,
                "orphan_block_events": orphan_block_events,
                "average_propagation_delta_seconds": round(avg_delta, 3),
                "processing_time_ms": round(elapsed_ms, 2)
            },
            "correlated_events": correlated_events[:100]  # sample
        }

    def get_live_batch(
        self,
        limit: int = 20,
        offset: int = 0,
        filter_tor: bool = False
    ) -> Dict[str, Any]:
        """Returns a snapshot of streaming telemetry frames for dashboard polling."""
        tx_items = list(data_service.txid_map.values())
        if filter_tor:
            tx_items = [
                tx for tx in tx_items
                if tx.get("node_type") == "tor_exit_node" or bool(tx.get("is_tor"))
            ]
        
        total = len(tx_items)
        sliced = tx_items[offset : offset + limit]
        
        events = []
        for tx in sliced:
            txid = tx["txid"]
            risk = ml_service.predict_risk(txid)
            node_type = str(tx.get("node_type", "residential"))
            events.append({
                "txid": txid,
                "timestamp": str(tx.get("timestamp")),
                "amount_btc": float(sum(tx.get("output_amounts", [0.0]))),
                "ip_address": tx.get("relay_ip"),
                "country": tx.get("country_code"),
                "node_type": node_type,
                "is_tor": node_type == "tor_exit_node" or bool(tx.get("is_tor")),
                "risk_score": risk.get("risk_score", 0.0),
                "risk_level": "HIGH" if risk.get("risk_score", 0.0) >= 0.5 else "LOW"
            })

        return {
            "total_available": total,
            "count": len(events),
            "offset": offset,
            "events": events
        }

streaming_correlator = StreamingCorrelator()
