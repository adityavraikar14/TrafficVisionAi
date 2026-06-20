from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from app.core.security import require_officer
from app.models.schemas import ReviewSubmission, StatusUpdate
from app.services.challan_service import generate_challan_pdf
from app.services.evidence_service import get_violation, list_violations, update_status
from app.services.review_service import get_latest_review, list_review_history, record_review

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.get("")
def get_evidence(search: str | None = None, limit: int = 200):
    return list_violations(search=search, limit=limit)


@router.get("/history")
def get_review_history(search: str | None = None, limit: int = 200):
    return list_review_history(search=search, limit=limit)


@router.patch("/{violation_id}/status")
def patch_status(violation_id: str, body: StatusUpdate, _: None = Depends(require_officer)):
    record = update_status(violation_id, body.status)
    if not record:
        raise HTTPException(404, "Violation not found")
    return record


@router.get("/{violation_id}/challan.pdf")
def get_challan(violation_id: str):
    violation = get_violation(violation_id)
    if not violation:
        raise HTTPException(404, "Violation not found")
    if violation["status"] != "Verified":
        raise HTTPException(400, "An e-challan can only be issued for a Verified violation.")

    review = get_latest_review(violation_id)
    if not review:
        raise HTTPException(400, "No review record found for this violation.")

    pdf_bytes = generate_challan_pdf(violation, review)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={violation_id}_challan.pdf"},
    )


@router.post("/{violation_id}/review")
def submit_review(violation_id: str, body: ReviewSubmission, _: None = Depends(require_officer)):
    try:
        record = record_review(
            violation_id,
            body.decision,
            body.officer_name,
            body.officer_badge_id,
            body.notes,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not record:
        raise HTTPException(404, "Violation not found")
    return record
