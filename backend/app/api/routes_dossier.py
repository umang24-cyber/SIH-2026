"""
Law Enforcement Agency (LEA) Investigation Dossier API Routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from backend.app.services.dossier_service import dossier_service

router = APIRouter(prefix="/api/dossier", tags=["LEA Dossier Generator"])

@router.get("/{txid}")
def get_dossier_json(txid: int):
    """
    Returns a structured Section 91 Cr.P.C. / FIU-IND Forensic Investigation Dossier as JSON.
    """
    res = dossier_service.generate_dossier(txid)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{txid}/html", response_class=HTMLResponse)
def get_dossier_html(txid: int):
    """
    Returns a print-ready, official HTML Law Enforcement Investigation Report for 1-click PDF download.
    """
    html_content = dossier_service.generate_html_dossier(txid)
    if "Error:" in html_content:
        raise HTTPException(status_code=404, detail=f"Transaction {txid} not found")
    return HTMLResponse(content=html_content, status_code=200)
