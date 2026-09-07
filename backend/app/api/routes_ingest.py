"""
Live Dynamic Ingestion & Real-Time ML Correlation Routes.
Supports CSV, JSON, and XML payload ingestion on the fly without server restart.
"""
import json
import logging
import math
from collections import defaultdict
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from backend.app.models.schemas import (
    IngestCorrelationResponse,
    IngestTransactionRequest,
    IngestResultResponse,
    IngestBatchResponse,
    IngestScenarioAnalysis,
    FeatureAttribution,
)
from backend.app.services.data_service import data_service
from backend.app.services.ml_service import ml_service
from backend.app.services.anomaly_service import anomaly_service
from backend.app.ingestion.parser import (
    normalize_transaction_dict,
    parse_json_payload,
    parse_csv_bytes,
    parse_xml_bytes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["Live Ingestion & Correlation Engine"])

# Frozen training feature artifacts contain no scenario with fewer than three
# transactions. This is a disclosure threshold, not a scoring gate.
MIN_TRAINING_SCENARIO_TX_COUNT = 3

# Scenario-level ML results from custom uploads.  The graph view reads this
# cache so it can display real model risk when available and an explicit
# unavailable state otherwise.
scenario_ml_analysis: Dict[str, IngestScenarioAnalysis] = {}

# Pre-packaged authentic test samples for 1-click demonstration
SAMPLE_TEMPLATES = {
    "ransomware": {
        "txid": 881920041,
        "timestamp": "2026-09-06 14:22:10",
        "relay_timestamp": "2026-09-06 14:22:08",
        "input_addresses": ["1AtB5eWkX36d4YtQ99vK8h7G4xN19mK7p"],
        "output_addresses": ["1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b", "1Vp4Qw98mNtK32bRx87hG21yE94xC65pK"],
        "input_amounts": [12.45],
        "output_amounts": [12.4485, 0.001],
        "fee_btc": 0.0005,
        "script_type": "P2PKH",
        "scenario_id": "live_ransomware_probe",
        "relay_ip": "185.220.101.44",
        "relay_port": 9050,
        "node_type": "bulletproof_host",
        "country_code": "RU",
        "asn": "AS49981",
        "isp": "WorldStream B.V. Bulletproof Relay",
        "propagation_delta_ms": 2150.0,
    },
    "peeling_chain": {
        "txid": 992019342,
        "timestamp": "2026-09-06 15:10:00",
        "relay_timestamp": "2026-09-06 15:09:59",
        "input_addresses": ["1PeelOriginSource99281hKx38v92"],
        "output_addresses": ["1PeelHopOneTarget99281hKx38v92", "1PeelChangeAddressCarry99281hK"],
        "input_amounts": [50.0],
        "output_amounts": [1.5, 48.4998],
        "fee_btc": 0.0002,
        "script_type": "P2PKH",
        "scenario_id": "live_peeling_sequence",
        "relay_ip": "194.26.29.112",
        "relay_port": 8333,
        "node_type": "vpn_proxy",
        "country_code": "PA",
        "asn": "AS60068",
        "isp": "Datacenter Transit Proxy",
        "propagation_delta_ms": 680.0,
    },
    "mixing": {
        "txid": 771029341,
        "timestamp": "2026-09-06 16:05:30",
        "relay_timestamp": "2026-09-06 16:05:29",
        "input_addresses": [
            "1MixInputPartyA_981729381kKx",
            "1MixInputPartyB_881729382bBx",
            "1MixInputPartyC_771729383cCx",
            "1MixInputPartyD_661729384dDx"
        ],
        "output_addresses": [
            "1MixEqualOut1_991827391aAx",
            "1MixEqualOut2_881827392bBx",
            "1MixEqualOut3_771827393cCx",
            "1MixEqualOut4_661827394dDx"
        ],
        "input_amounts": [0.55, 0.53, 0.54, 0.56],
        "output_amounts": [0.50, 0.50, 0.50, 0.50],
        "fee_btc": 0.0004,
        "script_type": "P2SH",
        "scenario_id": "live_coinjoin_round",
        "relay_ip": "104.244.76.13",
        "relay_port": 8333,
        "node_type": "tor_exit_node",
        "country_code": "DE",
        "asn": "AS200651",
        "isp": "Tor Relay Exit Operator",
        "propagation_delta_ms": 1420.0,
    },
    "licit": {
        "txid": 551029482,
        "timestamp": "2026-09-06 17:00:15",
        "relay_timestamp": "2026-09-06 17:00:15",
        "input_addresses": ["1LicitConsumerWallet88291kKx99"],
        "output_addresses": ["1LicitMerchantStorefront77291aA", "1LicitChangeWallet88291kKx99"],
        "input_amounts": [0.15],
        "output_amounts": [0.045, 0.1049],
        "fee_btc": 0.0001,
        "script_type": "P2WPKH",
        "scenario_id": "live_licit_purchase",
        "relay_ip": "73.189.44.201",
        "relay_port": 8333,
        "node_type": "residential",
        "country_code": "US",
        "asn": "AS7922",
        "isp": "Comcast Cable Communications",
        "propagation_delta_ms": 85.0,
    }
}


def _analyze_uploaded_scenario(
    scenario_id: str,
    scenario_txs: List[Dict[str, Any]],
) -> IngestScenarioAnalysis:
    """Run the existing scenario-level V7 and Isolation Forest paths."""
    base = {
        "scenario_id": scenario_id,
        "transaction_count": len(scenario_txs),
        "feature_count": 46,
        "sample_size_warning": (
            "Custom sample / distribution-shifted input — small sample size may reduce prediction reliability."
            if len(scenario_txs) < MIN_TRAINING_SCENARIO_TX_COUNT
            else None
        ),
    }

    try:
        # This is the production serving feature path.  The explicit finite
        # check prevents invalid model input from being presented as a score.
        feature_dict = ml_service._feature_dict(scenario_txs)
        invalid_features = [
            name for name, value in feature_dict.items()
            if not math.isfinite(float(value))
        ]
        if invalid_features:
            return IngestScenarioAnalysis(
                **base,
                analysis_status="UNAVAILABLE",
                analysis_message=(
                    "Production feature extraction produced invalid values for: "
                    + ", ".join(invalid_features)
                ),
            )

        ml_result = ml_service.score_candidate(
            scenario_txs,
            candidate_id=scenario_id,
        )
        if ml_result.get("error"):
            return IngestScenarioAnalysis(
                **base,
                analysis_status="UNAVAILABLE",
                analysis_message=f"ML analysis failed: {ml_result['error']}",
            )

        anomaly_score = None
        anomaly_label = None
        anomaly_message = ""
        try:
            anomaly_result = anomaly_service.score_scenario(scenario_txs)
            anomaly_score = anomaly_result.get("anomaly_score")
            anomaly_label = anomaly_result.get("anomaly_label")
        except Exception as exc:
            logger.warning(
                "Could not compute anomaly score for uploaded scenario %s: %s",
                scenario_id,
                exc,
            )
            anomaly_message = f"Anomaly analysis unavailable: {exc}"

        return IngestScenarioAnalysis(
            **base,
            analysis_status="AVAILABLE",
            analysis_message=(
                "Scored by the existing V7 binary and typology XGBoost models "
                "using the manifest-aligned 46-feature scenario vector."
            ),
            risk_score=ml_result.get("risk_score"),
            is_illicit=ml_result.get("is_illicit"),
            binary_confidence=ml_result.get("binary_confidence"),
            predicted_typology=ml_result.get("typology"),
            typology_confidence=ml_result.get("typology_confidence"),
            typology_explanation=ml_result.get("typology_explanation", ""),
            anomaly_score=anomaly_score,
            anomaly_label=anomaly_label,
            anomaly_message=anomaly_message,
            top_shap_attributions=[
                FeatureAttribution(**item)
                for item in ml_result.get("binary_shap", [])
            ],
            typology_shap_attributions=[
                FeatureAttribution(**item)
                for item in ml_result.get("typology_shap", [])
            ],
        )
    except Exception as exc:
        logger.exception("Uploaded scenario ML analysis failed for %s", scenario_id)
        return IngestScenarioAnalysis(
            **base,
            analysis_status="UNAVAILABLE",
            analysis_message=f"ML analysis unavailable: {exc}",
        )


@router.get("/sample")
def get_ingest_sample(
    typology: Optional[str] = Query("ransomware", description="Sample type: ransomware, peeling_chain, mixing, licit")
):
    """
    Returns authentic, pre-correlated synthetic test payloads for demonstration.
    """
    key = (typology or "ransomware").lower()
    if key not in SAMPLE_TEMPLATES:
        key = "ransomware"
    return SAMPLE_TEMPLATES[key]


@router.post("/transaction", response_model=IngestResultResponse)
def ingest_single_transaction(payload: Dict[str, Any] = Body(...)):
    """
    Ingest a single Bitcoin transaction with correlated dual-layer telemetry.
    Dynamically updates the in-memory database and computes real-time ML risk scoring + SHAP.
    """
    try:
        record = normalize_transaction_dict(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid transaction payload: {exc}")

    # 1. Index dynamically into in-memory store
    data_service.add_transaction(record)

    # 2. Run real-time ML inference
    ml_eval = ml_service.predict_risk([record])
    risk_score = float(ml_eval.get("risk_score", 0.0))
    is_illicit = bool(ml_eval.get("is_illicit", False))
    binary_conf = float(ml_eval.get("binary_confidence", 0.0))
    typology = str(ml_eval.get("typology", "normal"))
    typ_conf = float(ml_eval.get("typology_confidence", 0.0))

    # 3. Compute SHAP feature attributions
    top_shap = []
    try:
        raw_shap = ml_service.explain_binary_features([record], top_n=3)
        top_shap = [FeatureAttribution(**item) for item in raw_shap]
    except Exception as exc:
        logger.warning(f"Could not compute live SHAP for tx {record['txid']}: {exc}")

    # 4. Compute Isolation Forest anomaly score
    anomaly_score = None
    anomaly_label = None
    try:
        sc_id = record["scenario_id"]
        anom_res = anomaly_service.score_scenario_id(sc_id)
        if anom_res:
            anomaly_score = anom_res.get("anomaly_score")
            anomaly_label = anom_res.get("anomaly_label")
    except Exception as exc:
        logger.warning(f"Could not compute live anomaly score for tx {record['txid']}: {exc}")

    return IngestResultResponse(
        status="SUCCESS",
        message=f"Transaction {record['txid']} ingested and correlated successfully into scenario '{record['scenario_id']}'.",
        txid=record["txid"],
        scenario_id=record["scenario_id"],
        primary_wallet=record["input_addresses"][0] if record["input_addresses"] else "unknown",
        risk_score=round(risk_score, 4),
        is_illicit=is_illicit,
        binary_confidence=round(binary_conf, 4),
        predicted_typology=typology if is_illicit else None,
        typology_confidence=round(typ_conf, 4) if is_illicit else None,
        anomaly_score=anomaly_score,
        anomaly_label=anomaly_label,
        top_shap_attributions=top_shap,
        dossier_available=True,
    )


@router.post("/file", response_model=IngestBatchResponse)
async def ingest_file_upload(file: UploadFile = File(...)):
    """
    Upload and ingest custom bulk metadata in CSV, JSON, or XML format.
    Dynamically merges all records into the live database without restarting the engine.
    """
    content = await file.read()
    filename = (file.filename or "").lower()

    records: List[Dict[str, Any]] = []

    try:
        if filename.endswith(".csv"):
            records = parse_csv_bytes(content)
        elif filename.endswith(".xml"):
            records = parse_xml_bytes(content)
        elif filename.endswith(".json"):
            json_data = json.loads(content.decode("utf-8"))
            records = parse_json_payload(json_data)
        else:
            # Try auto-detect
            try:
                records = parse_csv_bytes(content)
            except Exception:
                try:
                    records = parse_json_payload(json.loads(content.decode("utf-8")))
                except Exception:
                    records = parse_xml_bytes(content)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse upload file '{file.filename}': {exc}"
        )

    if not records:
        raise HTTPException(status_code=400, detail="No valid transactions discovered in file.")

    input_records = len(records)

    # Calculate duplicates inside the uploaded file itself
    unique_txids = set()
    unique_records_list = []
    duplicate_records_in_file = 0

    for r in records:
        tid = r["txid"]
        if tid in unique_txids:
            duplicate_records_in_file += 1
        else:
            unique_txids.add(tid)
            unique_records_list.append(r)

    unique_records = len(unique_records_list)

    # Calculate duplicates already indexed
    already_indexed = sum(1 for r in unique_records_list if r["txid"] in data_service.txid_map)

    duplicate_records = duplicate_records_in_file + already_indexed
    newly_indexed_records = unique_records - already_indexed

    wallets_before = len(data_service.unique_wallets)
    indexed_count = data_service.add_transactions_batch(unique_records_list)
    wallets_after = len(data_service.unique_wallets)

    grouped_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in unique_records_list:
        grouped_records[str(record["scenario_id"])].append(record)

    scenario_results = []
    for scenario_id, scenario_txs in grouped_records.items():
        analysis = _analyze_uploaded_scenario(scenario_id, scenario_txs)
        scenario_ml_analysis[scenario_id] = analysis
        scenario_results.append(analysis)

    seen_scenarios = set()
    scenario_ids = []
    for r in records:
        sc = r.get("scenario_id")
        if sc and sc not in seen_scenarios:
            seen_scenarios.add(sc)
            scenario_ids.append(sc)
    sample_txids = [r["txid"] for r in records[:5]]

    # Record forensic audit trail
    try:
        from backend.app.services.db_service import db_service
        file_ext = filename.split(".")[-1] if "." in filename else "unknown"
        db_service.log_ingestion_audit(file.filename or "upload_file", file_ext, indexed_count, scenario_ids)
    except Exception as exc:
        logger.warning(f"Could not log upload audit to SQLite: {exc}")

    return IngestBatchResponse(
        status="SUCCESS",
        input_records=input_records,
        unique_records=unique_records,
        newly_indexed_records=newly_indexed_records,
        duplicate_records=duplicate_records,
        total_ingested=indexed_count,
        scenario_ids=scenario_ids[:10],
        unique_wallets_added=max(0, wallets_after - wallets_before),
        sample_txids=sample_txids,
        scenario_results=scenario_results,
        message=f"Successfully ingested {indexed_count} transactions across {len(scenario_ids)} scenario clusters from '{file.filename}'."
    )


@router.get("/scenario/{scenario_id}/analysis", response_model=IngestScenarioAnalysis)
def get_uploaded_scenario_analysis(scenario_id: str):
    """Return cached or on-demand scenario ML analysis."""
    cached = scenario_ml_analysis.get(scenario_id)
    if cached:
        return cached

    txids = data_service.get_scenario_txids(scenario_id)
    if not txids:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    scenario_txs = [
        data_service.txid_map[txid]
        for txid in txids
        if txid in data_service.txid_map
    ]
    if not scenario_txs:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' has no indexed transactions.")

    analysis = _analyze_uploaded_scenario(scenario_id, scenario_txs)
    scenario_ml_analysis[scenario_id] = analysis
    return analysis


@router.post("/correlate", response_model=IngestCorrelationResponse)
async def ingest_correlate(
    ledger_file: UploadFile = File(...),
    network_file: UploadFile = File(...)
):
    """
    Dual-stream correlation endpoint (FULL OUTER JOIN).
    Accepts explicit ledger and network streams, correlates by txid,
    and indexes the unified graph.
    """
    try:
        ledger_content = await ledger_file.read()
        network_content = await network_file.read()

        ledger_records = parse_csv_bytes(ledger_content)
        network_records = parse_csv_bytes(network_content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse files: {exc}")

    ledger_input_records = len(ledger_records)
    network_input_records = len(network_records)
    input_records = ledger_input_records + network_input_records

    ledger_map = {}
    ledger_dups_in_file = 0
    for r in ledger_records:
        tid = str(r["txid"])
        if tid in ledger_map:
            ledger_dups_in_file += 1
        else:
            ledger_map[tid] = r

    network_map = {}
    network_dups_in_file = 0
    for r in network_records:
        tid = str(r["txid"])
        if tid in network_map:
            network_dups_in_file += 1
        else:
            network_map[tid] = r

    matched_txids = set(ledger_map.keys()) & set(network_map.keys())
    ledger_only = set(ledger_map.keys()) - matched_txids
    network_only = set(network_map.keys()) - matched_txids

    merged_records = []
    # Merge matches (network telemetry fields added to ledger)
    for txid in matched_txids:
        merged = ledger_map[txid].copy()
        # Ensure we don't overwrite primary ledger keys accidentally, just add telemetry
        for k, v in network_map[txid].items():
            if k not in merged or merged[k] is None or str(merged[k]) == "":
                merged[k] = v
        merged_records.append(merged)

    # Add unmatched
    for txid in ledger_only:
        merged_records.append(ledger_map[txid])

    for txid in network_only:
        merged_records.append(network_map[txid])

    unique_records = len(merged_records)
    already_indexed = sum(1 for r in merged_records if r["txid"] in data_service.txid_map)
    duplicate_records = ledger_dups_in_file + network_dups_in_file + already_indexed
    newly_indexed_records = unique_records - already_indexed

    # Index into data_service
    indexed_count = data_service.add_transactions_batch(merged_records)

    # Analyze scenarios
    grouped_records = defaultdict(list)
    for record in merged_records:
        if record.get("scenario_id"):
            grouped_records[str(record["scenario_id"])].append(record)

    scenario_results = []
    seen_scenarios = []
    for scenario_id, scenario_txs in grouped_records.items():
        seen_scenarios.append(scenario_id)
        analysis = _analyze_uploaded_scenario(scenario_id, scenario_txs)
        scenario_ml_analysis[scenario_id] = analysis
        scenario_results.append(analysis)

    total_uploaded = len(ledger_map) + len(network_map)
    correlation_rate = (len(matched_txids) / max(len(ledger_map), len(network_map))) if total_uploaded > 0 else 0.0

    return IngestCorrelationResponse(
        status="SUCCESS",
        message="Two-stream correlation complete.",
        input_records=input_records,
        unique_records=unique_records,
        newly_indexed_records=newly_indexed_records,
        duplicate_records=duplicate_records,
        ledger_records=len(ledger_map),
        network_records=len(network_map),
        matched_records=len(matched_txids),
        ledger_only_records=len(ledger_only),
        network_only_records=len(network_only),
        unmatched_ledger=len(ledger_only),
        unmatched_network=len(network_only),
        correlation_rate=round(correlation_rate, 4),
        scenarios_analyzed=seen_scenarios[:10],
        scenario_results=scenario_results
    )
