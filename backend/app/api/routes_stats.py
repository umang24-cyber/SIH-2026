"""
Scenario Cluster Explorer, Forensic Statistics & Benchmark Evaluation Routes.
"""
import json

from fastapi import APIRouter, Query, HTTPException, Response
from typing import List, Dict, Any, Optional
from collections import Counter
from backend.app.services.data_service import data_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.scenario_service import scenario_service
from backend.app.core.config import BASE_DIR

router = APIRouter(tags=["Analytics"])

@router.get("/scenarios")
def list_scenarios(
    prefix: Optional[str] = Query(None, description="Filter by prefix: peel, layer, mix, bg, licit_exchange"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Returns paginated list of scenario clusters with transaction counts and financial volume.
    """
    scenarios = []
    for sc_id, txids in data_service.scenario_tx_map.items():
        if prefix and not sc_id.startswith(prefix):
            continue
            
        total_btc = 0.0
        node_types = []
        for t in txids:
            tx = data_service.txid_map.get(t)
            if tx:
                total_btc += sum(tx.get("input_amounts", [0.0]))
                node_types.append(tx.get("node_type", "residential"))
                
        primary_node_type = Counter(node_types).most_common(1)[0][0] if node_types else "unknown"
        scenarios.append({
            "scenario_id": sc_id,
            "transaction_count": len(txids),
            "total_volume_btc": round(total_btc, 8),
            "primary_node_type": primary_node_type
        })

    # Sort by transaction count descending
    scenarios.sort(key=lambda s: s["transaction_count"], reverse=True)
    
    total = len(scenarios)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "total_scenarios": total,
        "page": page,
        "page_size": page_size,
        "scenarios": scenarios[start:end]
    }

@router.get("/scenarios/{scenario_id}")
def get_scenario_profile(scenario_id: str):
    """
    Retrieves deep forensic risk profile for a specific scenario:
    - Infrastructure risk score (percentage of bulletproof / Tor / VPN relays)
    - Dominant laundering typology
    - Top hub wallets and transaction volume aggregates
    """
    profile = scenario_service.get_scenario_detail(scenario_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_id}' not found."
        )
    return profile

@router.get("/stats/telemetry")
def get_telemetry_stats():
    """
    Returns global network telemetry aggregations across the loaded V7 dataset:
    - Distribution of origin node infrastructure
    - Top origin Autonomous Systems (ASNs)
    - Average propagation latency by infrastructure type
    - Script type distributions
    """
    node_type_counter = Counter()
    asn_counter = Counter()
    country_counter = Counter()
    script_counter = Counter()
    latency_by_type = {}

    for tx in data_service.txid_map.values():
        nt = str(tx.get("node_type", "residential"))
        asn = str(tx.get("asn", "Unknown"))
        cc = str(tx.get("country_code", "US"))
        st = str(tx.get("script_type", "P2PKH"))
        lat = float(tx.get("propagation_delta_ms", 0.0))

        node_type_counter[nt] += 1
        asn_counter[asn] += 1
        country_counter[cc] += 1
        script_counter[st] += 1

        if nt not in latency_by_type:
            latency_by_type[nt] = []
        latency_by_type[nt].append(lat)

    avg_latency = {
        nt: round(sum(vals) / len(vals), 2)
        for nt, vals in latency_by_type.items()
        if vals
    }

    return {
        "total_transactions": len(data_service.txid_map),
        "total_unique_wallets": len(data_service.unique_wallets),
        "total_scenarios": len(data_service.scenario_tx_map),
        "node_type_distribution": dict(node_type_counter.most_common()),
        "top_asns": dict(asn_counter.most_common(10)),
        "top_countries": dict(country_counter.most_common(10)),
        "script_type_distribution": dict(script_counter.most_common()),
        "average_propagation_latency_ms": avg_latency
    }

@router.get("/eval/benchmark")
def get_evaluation_benchmark():
    """
    Return the current V7 candidate benchmark metadata and stored model metrics.

    Heuristic alert counts are runtime observations; precision/recall metrics
    come only from the canonical V7 manifest and are not inferred here.
    """
    manifest_path = BASE_DIR / "ml" / "manifests" / "MANIFEST_v7_candidate.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=503, detail=f"V7 manifest not found: {manifest_path}")
    try:
        with manifest_path.open("r") as handle:
            manifest = json.load(handle)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not read V7 manifest: {exc}") from exc

    return {
        "dataset_version": manifest.get("dataset_version", "v7_candidate"),
        "evaluation_scope": "Offline Air-Gapped V7 Candidate Benchmark",
        "dataset_transactions": len(data_service.txid_map),
        "dataset_scenarios": len(data_service.scenario_tx_map),
        "feature_count": manifest.get("feature_count"),
        "candidate_alerts_flagged": len(typology_detector.detected_alerts),
        "model_metrics": manifest.get("evaluation_metrics", {}),
        "calibration": manifest.get("calibration", {}),
        "metric_timestamp": manifest.get("timestamp"),
    }

@router.get("/alerts/{candidate_id}/export")
def export_forensic_dossier(candidate_id: str):
    """
    Exports a formatted text/markdown forensic case file for law enforcement proceedings.
    """
    evidence = typology_detector.get_evidence(candidate_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    lines = [
        "=" * 80,
        "           BITKAUN FORENSIC INTELLIGENCE DOSSIER (CONFIDENTIAL / LEA USE)",
        "=" * 80,
        f"CANDIDATE ID        : {evidence.candidate_id}",
        f"SCENARIO CLUSTER    : {evidence.scenario_id}",
        f"PREDICTED TYPOLOGY  : {evidence.predicted_pattern_type.upper()}",
        f"BINARY CONFIDENCE   : {evidence.binary_confidence * 100:.1f}%",
        f"TYPOLOGY CONFIDENCE : {evidence.typology_confidence * 100:.1f}%",
        "-" * 80,
        "HEURISTIC MATCH SUMMARY:",
        f"  - Algorithm Applied       : {evidence.typology_heuristic_match.get('heuristic_name')}",
        f"  - Chain Hop Length        : {evidence.typology_heuristic_match.get('chain_length')}",
        f"  - Primary Target Wallet   : {evidence.typology_heuristic_match.get('primary_destination')}",
        "-" * 80,
        "KEY FEATURE ATTRIBUTIONS (SHAP EXPLAINABILITY):"
    ]
    for attr in evidence.ml_feature_attributions:
        lines.append(f"  * {attr.feature_name:<25}: Value={str(attr.value):<10} | SHAP={attr.shap_value:+.3f} [{attr.direction}]")

    lines.extend([
        "-" * 80,
        "NETWORK TELEMETRY SUMMARY:",
        f"  - Origin IPs    : {', '.join(evidence.telemetry_summary.get('origin_ips', []))}",
        f"  - Origin ASNs   : {', '.join(evidence.telemetry_summary.get('origin_asns', []))}",
        f"  - Origin Nations: {', '.join(evidence.telemetry_summary.get('countries', []))}",
        "-" * 80,
        "TRANSACTION CHRONOLOGY:"
    ])

    for idx, tx in enumerate(evidence.transactions, 1):
        lines.extend([
            f"  [TX {idx}] TxID: {tx['txid']} | Block Time: {tx['timestamp']}",
            f"         Inputs : {', '.join(tx['input_addresses'])} (Total: {sum(tx['input_amounts']):.6f} BTC)",
            f"         Outputs: {', '.join(tx['output_addresses'])} (Total: {sum(tx['output_amounts']):.6f} BTC)",
            f"         Fee    : {tx['fee_btc']:.8f} BTC | Script: {tx['script_type']}",
            f"         Relay  : IP {tx['relay_ip']} | {tx['node_type']} | ASN: {tx['asn']}"
        ])

    lines.append("=" * 80)
    report_text = "\n".join(lines)
    
    return Response(
        content=report_text,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=dossier_{candidate_id}.txt"}
    )
