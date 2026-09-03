"""
Transaction Lookup & Financial Flow Decomposition Routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.models.schemas import TransactionResponse

router = APIRouter(tags=["Transaction"])

@router.get("/transaction/{txid}", response_model=TransactionResponse)
def get_transaction(txid: int):
    """
    Retrieve full dual-layer transaction record:
    On-chain multi-I/O UTXO array state fused with pre-block P2P network telemetry.
    """
    tx = data_service.get_transaction(txid)
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction ID {txid} not found in database."
        )
    return tx

@router.get("/transaction/{txid}/flow")
def get_transaction_flow(txid: int) -> Dict[str, Any]:
    """
    Financial Flow & Entity Decomposition:
    Returns structured inputs, entity cluster IDs, fee distribution, and outputs
    for Sankey / visual flow mapping.
    """
    tx = data_service.txid_map.get(txid)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {txid} not found.")

    in_addrs = tx.get("input_addresses", [])
    in_amts = tx.get("input_amounts", [])
    out_addrs = tx.get("output_addresses", [])
    out_amts = tx.get("output_amounts", [])
    fee_btc = float(tx.get("fee_btc", 0.0))

    total_in = sum(in_amts)
    total_out = sum(out_amts)

    inputs_structured = []
    for addr, amt in zip(in_addrs, in_amts):
        root = clustering_service.dsu.find(addr) if clustering_service.is_clustered else addr
        inputs_structured.append({
            "address": addr,
            "amount_btc": round(float(amt), 8),
            "entity_cluster_id": f"entity_{root[:12]}" if clustering_service.is_clustered else "unknown"
        })

    outputs_structured = []
    for addr, amt in zip(out_addrs, out_amts):
        root = clustering_service.dsu.find(addr) if clustering_service.is_clustered else addr
        outputs_structured.append({
            "address": addr,
            "amount_btc": round(float(amt), 8),
            "entity_cluster_id": f"entity_{root[:12]}" if clustering_service.is_clustered else "unknown"
        })

    return {
        "txid": txid,
        "timestamp": str(tx.get("timestamp", "")),
        "scenario_id": str(tx.get("scenario_id", "")),
        "script_type": str(tx.get("script_type", "P2PKH")),
        "total_input_btc": round(total_in, 8),
        "total_output_btc": round(total_out, 8),
        "fee_btc": round(fee_btc, 8),
        "fee_ratio_percent": round((fee_btc / max(0.00001, total_in)) * 100.0, 4),
        "inputs": inputs_structured,
        "outputs": outputs_structured,
        "network_telemetry": {
            "relay_ip": str(tx.get("relay_ip", "")),
            "node_type": str(tx.get("node_type", "residential")),
            "country_code": str(tx.get("country_code", "US")),
            "asn": str(tx.get("asn", "")),
            "propagation_delta_ms": float(tx.get("propagation_delta_ms", 0.0))
        }
    }
