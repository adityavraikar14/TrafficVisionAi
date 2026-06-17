from fastapi import APIRouter, HTTPException

from app.models.schemas import StatusUpdate
from app.services.evidence_service import list_violations, update_status

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.get("")
def get_evidence(search: str | None = None, limit: int = 200):
    return list_violations(search=search, limit=limit)


@router.patch("/{violation_id}/status")
def patch_status(violation_id: str, body: StatusUpdate):
    record = update_status(violation_id, body.status)
    if not record:
        raise HTTPException(404, "Violation not found")
    return record
