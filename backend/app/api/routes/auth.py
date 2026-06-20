from fastapi import APIRouter, HTTPException

from app.core.security import SESSION_TOKEN, check_credentials
from app.models.schemas import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest):
    officer_name = check_credentials(body.username, body.password)
    if not officer_name:
        raise HTTPException(401, "Invalid username or password.")
    return {"token": SESSION_TOKEN, "officer_name": officer_name}
