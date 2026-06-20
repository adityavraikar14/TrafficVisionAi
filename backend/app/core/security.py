import secrets

from fastapi import Header, HTTPException

from app.core.config import OFFICER_USERNAME, OFFICER_PASSWORD, OFFICER_NAME

SESSION_TOKEN = secrets.token_hex(24)


def check_credentials(username: str, password: str) -> str | None:
    if username == OFFICER_USERNAME and password == OFFICER_PASSWORD:
        return OFFICER_NAME
    return None


def require_officer(authorization: str | None = Header(default=None)) -> None:
    if authorization != f"Bearer {SESSION_TOKEN}":
        raise HTTPException(401, "Officer login required.")
