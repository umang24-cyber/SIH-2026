"""Investigation summary API routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from backend.app.services.dossier_service import dossier_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.data_service import data_service

router = APIRouter(prefix="/api/dossier", tags=["LEA Dossier Generator"])

def _resolve_txid(target: str) -> int:
    target_str = str(target).strip()
    if target_str.upper().startswith("TX:"):
        target_str = target_str[3:].strip()
    elif target_str.upper().startswith("TX_"):
        target_str = target_str[3:].strip()
    if target_str.isdigit():
        return int(target_str)
    # Check if target is a candidate alert ID
    evidence = typology_detector.get_evidence(target_str)
    if evidence and evidence.transactions:
        return int(evidence.transactions[0]["txid"])
    for alert in typology_detector.detected_alerts:
        if alert.candidate_id == target_str and alert.member_txids:
            return int(alert.member_txids[0])
    # Check if target is a scenario_id or custom cluster
    scenario_txids = data_service.get_scenario_txids(target_str)
    if scenario_txids:
        return int(scenario_txids[0])
    raise HTTPException(status_code=404, detail=f"Target '{target}' is neither a valid numeric TXID, recognized Scenario ID, nor Candidate ID.")

@router.get("/saved/list")
def get_saved_dossiers_list():
    """
    Returns a list of saved system-generated investigative summaries.
    """
    from backend.app.services.db_service import db_service
    return db_service.list_all_dossiers()

@router.get("/{txid}")
def get_dossier_json(txid: str):
    """
    Returns a structured forensic investigative summary as JSON.
    Accepts either an integer TXID or a candidate ID string (e.g. cand_ransom_...).
    """
    numeric_txid = _resolve_txid(txid)
    res = dossier_service.generate_dossier(numeric_txid)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{txid}/html", response_class=HTMLResponse)
def get_dossier_html(txid: str):
    """
    Returns a print-ready HTML investigative summary for 1-click PDF download.
    Accepts either an integer TXID or a candidate ID string.
    """
    numeric_txid = _resolve_txid(txid)
    html_content = dossier_service.generate_html_dossier(numeric_txid)
    if "Error:" in html_content:
        raise HTTPException(status_code=404, detail=f"Transaction {numeric_txid} not found")
    return HTMLResponse(content=html_content, status_code=200)
