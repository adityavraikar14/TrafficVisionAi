from collections import defaultdict
from datetime import datetime, timedelta

from app.core.db import get_conn


def summary() -> dict:
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM violations").fetchall()]

    total = len(rows)
    helmet = sum(1 for r in rows if r["violation_type"] == "Helmet Non-Compliance")
    triple = sum(1 for r in rows if r["violation_type"] == "Triple Riding")
    pending = sum(1 for r in rows if r["status"] == "Pending Review")
    verified = sum(1 for r in rows if r["status"] == "Verified")
    escalated = sum(1 for r in rows if r["status"] == "Escalated")
    rejected = sum(1 for r in rows if r["status"] == "Rejected")
    avg_conf = (sum(r["confidence"] for r in rows) / total) if total else 0.0

    by_type: dict = defaultdict(int)
    for r in rows:
        by_type[r["violation_type"]] += 1

    by_city: dict = defaultdict(lambda: {"total": 0, "helmet": 0, "triple_riding": 0, "illegal_parking": 0, "last_violation_at": None})
    for r in rows:
        city = r["city"] or "Unknown"
        by_city[city]["total"] += 1
        if r["violation_type"] == "Helmet Non-Compliance":
            by_city[city]["helmet"] += 1
        elif r["violation_type"] == "Triple Riding":
            by_city[city]["triple_riding"] += 1
        elif r["violation_type"] == "Illegal Parking":
            by_city[city]["illegal_parking"] += 1
        if not by_city[city]["last_violation_at"] or r["created_at"] > by_city[city]["last_violation_at"]:
            by_city[city]["last_violation_at"] = r["created_at"]

    city_breakdown = [
        {
            "city": city,
            "total": stats["total"],
            "helmet": stats["helmet"],
            "triple_riding": stats["triple_riding"],
            "illegal_parking": stats["illegal_parking"],
            "last_violation_at": stats["last_violation_at"],
            "lat": next((r["lat"] for r in rows if r["city"] == city and r["lat"]), None),
            "lon": next((r["lon"] for r in rows if r["city"] == city and r["lon"]), None),
        }
        for city, stats in by_city.items()
    ]
    city_breakdown.sort(key=lambda c: c["total"], reverse=True)

    trend = _trend(rows, days=7)
    recent = sorted(rows, key=lambda r: r["created_at"], reverse=True)[:8]

    return {
        "total_violations": total,
        "helmet_violations": helmet,
        "triple_riding_cases": triple,
        "pending_reviews": pending,
        "verified": verified,
        "escalated": escalated,
        "rejected": rejected,
        "average_confidence": round(avg_conf, 4),
        "compliance_rate": round(100 - (helmet / total * 100), 1) if total else 100.0,
        "by_type": by_type,
        "city_breakdown": city_breakdown,
        "trend": trend,
        "recent": recent,
    }


def _trend(rows: list[dict], days: int) -> list[dict]:
    buckets = {}
    today = datetime.now().date()
    for offset in range(days - 1, -1, -1):
        d = today - timedelta(days=offset)
        buckets[d.isoformat()] = {"date": d.strftime("%d %b"), "violations": 0, "reviewed": 0}

    for r in rows:
        try:
            d = datetime.fromisoformat(r["created_at"]).date().isoformat()
        except ValueError:
            continue
        if d in buckets:
            buckets[d]["violations"] += 1
            if r["status"] in ("Verified", "Escalated", "Rejected"):
                buckets[d]["reviewed"] += 1

    return list(buckets.values())
