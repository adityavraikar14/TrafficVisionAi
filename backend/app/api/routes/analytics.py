from fastapi import APIRouter

from app.services.analytics_service import summary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary():
    return summary()
