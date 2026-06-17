import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.evidence_service import list_violations

router = APIRouter(prefix="/api/reports", tags=["reports"])

COLUMNS = [
    "violation_id",
    "vehicle_number",
    "violation_type",
    "confidence",
    "status",
    "city",
    "location",
    "created_at",
]


@router.get("/export.csv")
def export_csv():
    rows = list_violations(limit=10000)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trafficvision_evidence_report.csv"},
    )
