"""
Transaction Lookup Route.
"""
from fastapi import APIRouter, HTTPException
from backend.app.services.data_service import data_service
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
