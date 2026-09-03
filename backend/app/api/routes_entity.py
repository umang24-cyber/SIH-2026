"""
Entity / Wallet Forensics Route.
"""
from fastapi import APIRouter, HTTPException
from backend.app.services.data_service import data_service
from backend.app.models.schemas import EntityResponse

router = APIRouter(tags=["Entity"])

@router.get("/entity/{address}", response_model=EntityResponse)
def get_entity_profile(address: str):
    """
    Retrieve wallet activity profile, financial volume, transaction counts,
    and exchange status computed dynamically from the master dataset.
    """
    entity = data_service.get_entity(address)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Bitcoin address '{address}' not found in forensic ledger."
        )
    return entity
