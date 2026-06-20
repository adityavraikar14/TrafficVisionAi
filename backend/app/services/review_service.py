from datetime import datetime

from app.core.db import get_conn
from app.services.evidence_service import REPEAT_COUNT_SELECT

VALID_DECISIONS = {"Verified", "Rejected"}


def record_review(
    violation_id: str,
    decision: str,
    officer_name: str,
    officer_badge_id: str,
    notes: str | None,
) -> dict | None:
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {VALID_DECISIONS}")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM violations WHERE violation_id = ?", (violation_id,)
        ).fetchone()
        if not existing:
            return None

        reviewed_at = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO review_log (
                violation_id, decision, officer_name, officer_badge_id, notes, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (violation_id, decision, officer_name, officer_badge_id, notes, reviewed_at),
        )
        conn.execute(
            "UPDATE violations SET status = ? WHERE violation_id = ?",
            (decision, violation_id),
        )
        row = conn.execute(
            REPEAT_COUNT_SELECT + " WHERE v.violation_id = ?", (violation_id,)
        ).fetchone()
        return dict(row)


def get_latest_review(violation_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM review_log WHERE violation_id = ? ORDER BY reviewed_at DESC LIMIT 1",
            (violation_id,),
        ).fetchone()
        return dict(row) if row else None


def list_review_history(search: str | None = None, limit: int = 200) -> list[dict]:
    query = """
        SELECT
            r.id, r.violation_id, r.decision, r.officer_name, r.officer_badge_id,
            r.notes, r.reviewed_at,
            v.violation_type, v.vehicle_number, v.city
        FROM review_log r
        JOIN violations v ON v.violation_id = r.violation_id
    """
    params: tuple = ()
    if search:
        like = f"%{search.lower()}%"
        query += """
            WHERE lower(r.violation_id) LIKE ?
               OR lower(r.officer_name) LIKE ?
               OR lower(r.officer_badge_id) LIKE ?
        """
        params = (like, like, like)
    query += " ORDER BY r.reviewed_at DESC LIMIT ?"
    params = params + (limit,)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
