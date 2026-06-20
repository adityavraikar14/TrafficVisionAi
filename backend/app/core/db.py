import sqlite3
import random
from contextlib import contextmanager
from datetime import datetime, timedelta

from app.core.config import DB_PATH, SEED_DEMO_DATA, CITY_SEED

SCHEMA = """
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id TEXT UNIQUE NOT NULL,
    vehicle_number TEXT,
    violation_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending Review',
    city TEXT,
    location TEXT,
    lat REAL,
    lon REAL,
    original_image_path TEXT,
    annotated_image_path TEXT,
    source TEXT NOT NULL DEFAULT 'upload',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    officer_name TEXT NOT NULL,
    officer_badge_id TEXT NOT NULL,
    notes TEXT,
    reviewed_at TEXT NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) AS c FROM violations").fetchone()["c"]
        if count == 0 and SEED_DEMO_DATA:
            _seed_demo_data(conn)


def _seed_demo_data(conn) -> None:
    violation_types = [
        ("Helmet Non-Compliance", 0.55),
        ("Triple Riding", 0.18),
        ("Illegal Parking", 0.14),
        ("Stunt Riding", 0.07),
        ("Wrong-Side Driving", 0.06),
    ]
    statuses = ["Pending Review", "Verified", "Escalated"]
    plate_prefixes = ["MH-12", "DL-08", "KA-01", "TS-09", "TN-07", "MH-14"]

    now = datetime.now()
    rows = []
    seq = 1000
    for day_offset in range(13, -1, -1):
        day = now - timedelta(days=day_offset)
        daily_count = random.randint(4, 11)
        for _ in range(daily_count):
            city = random.choice(CITY_SEED)
            vtype = random.choices(
                [v[0] for v in violation_types],
                weights=[v[1] for v in violation_types],
            )[0]
            seq += 1
            confidence = round(random.uniform(0.62, 0.97), 2)
            status = random.choices(statuses, weights=[0.45, 0.4, 0.15])[0]
            plate = f"{random.choice(plate_prefixes)}{random.choice('ABCDEFGH')}{random.choice('ABCDEFGH')}{random.randint(1000,9999)}"
            timestamp = day.replace(
                hour=random.randint(6, 22), minute=random.randint(0, 59)
            )
            rows.append(
                (
                    f"TV-{seq}",
                    plate,
                    vtype,
                    confidence,
                    status,
                    city["city"],
                    f"{city['city']} Demo Zone",
                    city["lat"] + random.uniform(-0.05, 0.05),
                    city["lon"] + random.uniform(-0.05, 0.05),
                    None,
                    None,
                    "seed",
                    timestamp.isoformat(),
                )
            )

    conn.executemany(
        """
        INSERT INTO violations (
            violation_id, vehicle_number, violation_type, confidence, status,
            city, location, lat, lon, original_image_path, annotated_image_path,
            source, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
