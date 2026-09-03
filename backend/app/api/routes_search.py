"""
Universal Forensic Search Route.
Allows investigators to query by address, txid, IP, ASN, or scenario.
"""
from fastapi import APIRouter, Query
from typing import List, Dict, Any
from backend.app.services.data_service import data_service

router = APIRouter(tags=["Search"])

@router.get("/search")
def search_ledger(
    q: str = Query(..., min_length=2, description="Search query: Address, TxID, IP, ASN, or Scenario ID"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Universal forensic query engine:
    - If q is an integer, searches txid
    - If q is a Bitcoin address, returns wallet activity and associated transactions
    - If q is an IP (e.g. 38.148...), returns associated broadcasted transactions
    - If q is an ASN (e.g. AS55836), returns infrastructure transactions
    - If q is a scenario ID (e.g. peel_001), returns scenario members
    """
    query = q.strip()
    results: Dict[str, Any] = {
        "query": query,
        "match_type": "UNKNOWN",
        "matches": []
    }

    # 1. Check if integer TxID
    if query.isdigit():
        txid = int(query)
        tx = data_service.get_transaction(txid)
        if tx:
            results["match_type"] = "TRANSACTION"
            results["matches"].append(tx.model_dump())
            return results

    # 2. Check if Bitcoin Wallet Address
    if query in data_service.unique_wallets or data_service.get_entity(query):
        entity = data_service.get_entity(query)
        if entity:
            results["match_type"] = "WALLET"
            results["matches"].append(entity.model_dump())
            return results

    # 3. Check if Scenario ID
    if query in data_service.scenario_tx_map:
        txids = data_service.scenario_tx_map[query][:limit]
        results["match_type"] = "SCENARIO"
        results["matches"] = [
            data_service.get_transaction(t).model_dump()
            for t in txids
            if data_service.get_transaction(t)
        ]
        return results

    # 4. Search by IP or ASN substring
    ip_or_asn_matches = []
    for txid, tx in data_service.txid_map.items():
        if query.lower() in str(tx.get("relay_ip", "")).lower() or query.lower() in str(tx.get("asn", "")).lower():
            ip_or_asn_matches.append(txid)
            if len(ip_or_asn_matches) >= limit:
                break
                
    if ip_or_asn_matches:
        results["match_type"] = "TELEMETRY"
        results["matches"] = [
            data_service.get_transaction(t).model_dump()
            for t in ip_or_asn_matches
            if data_service.get_transaction(t)
        ]
        return results

    return results
