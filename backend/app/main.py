from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import CORS_ORIGINS, UPLOADS_DIR, EVIDENCE_DIR, STORAGE_DIR
from app.core.db import init_db
from app.api.routes import detect, detect_video, evidence, analytics, reports, auth

app = FastAPI(title="TrafficVision AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/storage/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")

app.include_router(detect.router)
app.include_router(detect_video.router)
app.include_router(evidence.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(auth.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TrafficVision AI backend"}


@app.get("/")
def root():
    return {
        "service": "TrafficVision AI backend",
        "status": "running",
        "note": "This is the API server. The web app is the separately-deployed frontend.",
        "docs": "/docs",
        "health": "/api/health",
    }
