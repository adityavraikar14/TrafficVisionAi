import random
from datetime import datetime

from app.core.db import get_conn
from app.core.config import CITY_SEED


def _new_violation_id(conn) -> str:
    row = conn.execute("SELECT MAX(id) AS m FROM violations").fetchone()
    next_seq = (row["m"] or 1000) + 1
    return f"TV-{next_seq}"


def create_violation_record(
    *,
    vehicle_number: str,
    violation_type: str,
    confidence: float,
    original_image_path: str | None,
    annotated_image_path: str | None,
    source: str = "upload",
    evidence_video_path: str | None = None,
) -> dict:
    city = random.choice(CITY_SEED)
    with get_conn() as conn:
        violation_id = _new_violation_id(conn)
        created_at = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO violations (
                violation_id, vehicle_number, violation_type, confidence, status,
                city, location, lat, lon, original_image_path, annotated_image_path,
                evidence_video_path, source, created_at
            ) VALUES (?, ?, ?, ?, 'Pending Review', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                violation_id,
                vehicle_number,
                violation_type,
                confidence,
                city["city"],
                f"{city['city']} Live Detection Zone",
                city["lat"],
                city["lon"],
                original_image_path,
                annotated_image_path,
                evidence_video_path,
                source,
                created_at,
            ),
        )
        row = conn.execute(
            "SELECT * FROM violations WHERE violation_id = ?", (violation_id,)
        ).fetchone()
        return dict(row)


REPEAT_COUNT_SELECT = """
    SELECT v.*, (
        SELECT COUNT(*) FROM violations v2
        WHERE v2.vehicle_number = v.vehicle_number
          AND v.vehicle_number IS NOT NULL
          AND v.vehicle_number != 'Not Clearly Visible'
    ) AS repeat_count
    FROM violations v
"""


def list_violations(search: str | None = None, limit: int = 200) -> list[dict]:
    query = REPEAT_COUNT_SELECT
    params: tuple = ()
    if search:
        like = f"%{search.lower()}%"
        query += """
            WHERE lower(v.violation_id) LIKE ?
               OR lower(v.vehicle_number) LIKE ?
               OR lower(v.violation_type) LIKE ?
               OR lower(v.city) LIKE ?
               OR lower(v.status) LIKE ?
        """
        params = (like, like, like, like, like)
    query += " ORDER BY v.created_at DESC LIMIT ?"
    params = params + (limit,)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_violation(violation_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            REPEAT_COUNT_SELECT + " WHERE v.violation_id = ?", (violation_id,)
        ).fetchone()
        return dict(row) if row else None


def update_status(violation_id: str, status: str) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE violations SET status = ? WHERE violation_id = ?",
            (status, violation_id),
        )
        row = conn.execute(
            "SELECT * FROM violations WHERE violation_id = ?", (violation_id,)
        ).fetchone()
        return dict(row) if row else None
