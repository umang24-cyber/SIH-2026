"""
Live Dynamic Ingestion & Real-Time ML Correlation Routes.
Supports CSV, JSON, and XML payload ingestion on the fly without server restart.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from backend.app.models.schemas import (
    IngestTransactionRequest,
    IngestResultResponse,
    IngestBatchResponse,
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
        predicted_typology=typology,
        typology_confidence=round(typ_conf, 4),
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

    wallets_before = len(data_service.unique_wallets)
    indexed_count = data_service.add_transactions_batch(records)
    wallets_after = len(data_service.unique_wallets)

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
        total_ingested=indexed_count,
        scenario_ids=scenario_ids[:10],
        unique_wallets_added=max(0, wallets_after - wallets_before),
        sample_txids=sample_txids,
        message=f"Successfully ingested {indexed_count} transactions across {len(scenario_ids)} scenario clusters from '{file.filename}'."
    )
