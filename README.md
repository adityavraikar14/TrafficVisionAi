# TrafficVision AI

**From Detection to Digital Evidence**

An AI-powered traffic violation detection and evidence-generation platform.
Upload a traffic image, calibrate a stop-line / no-parking zone if needed,
and the system runs real-time detection across helmet compliance, triple
riding, stop-line/red-light violations, and illegal parking — extracts
the vehicle plate via OCR, and generates a searchable digital evidence
record. Visualized in a command-center web dashboard with a live India
risk map.

## Architecture

```
backend/                 FastAPI service
  app/
    api/routes/          detect.py, evidence.py, analytics.py, reports.py
    services/
      detection_service.py     model loading (helmet, general COCO, pose)
      preprocessing_service.py adaptive low-light/denoise/sharpen correction
      vehicle_service.py       road-user classification + box de-duplication
      pose_service.py          seated-vs-standing posture check (pose model)
      triple_riding_service.py rule-based triple-riding logic
      zone_service.py          stop-line/red-light + illegal-parking geometry
      ocr_service.py           plate text extraction (EasyOCR)
      plate_service.py         classical-CV plate region localization
      annotation_service.py    draws all violations/zones on the evidence image
      evidence_service.py      SQLite persistence
      analytics_service.py     aggregation for dashboards
    core/                config.py, db.py (SQLite)
    main.py
  storage/                uploads/ (originals), evidence/ (annotated images), trafficvision.db

frontend/                React + Vite + TailwindCSS + Recharts + Leaflet
  src/
    pages/                Dashboard, Analyze, EvidenceCenter, Analytics,
                          SmartCityMap, Reports, Roadmap, About
    components/           Layout, Sidebar, Header, Card, Kpi, Chip, charts
    api/client.ts

models/                   helmet_best.pt, yolov8n.pt (stock COCO), yolov8n-pose.pt
datasets/                 training data — gitignored, regenerate via scripts/prepare_dataset.py
scripts/                  prepare_dataset.py, evaluate_helmet_model.py
reports/                  helmet_model_metrics.json (precision/recall/F1/mAP)
```

Detection pipeline: `image upload → adaptive preprocessing → YOLOv8 helmet
detection + stock-YOLO road-user detection (de-duplicated) → pose-based
seated-rider check → triple-riding / stop-line / red-light / illegal-parking
rules → CV-based plate localization + OCR → annotated evidence image →
SQLite record → REST API → React dashboards`

## Running locally

Two servers, run in separate terminals.

**Backend** (FastAPI, port 8000):
```
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
or just double-click `backend/run.bat` on Windows.

**Frontend** (Vite dev server, port 5173):
```
cd frontend
npm install
npm run dev
```
or double-click `frontend/run.bat`.

Then open **http://localhost:5173**. The Vite dev server proxies `/api`
and `/storage` requests to the backend automatically (see
`frontend/vite.config.ts`).

The database seeds itself with 14 days of demo violation data on first
run (`backend/app/core/db.py`) so the dashboards aren't empty before you
upload your first real image. Every image you analyze on the **Live
Detection** page adds real records on top of that seed data.

## What's real vs. roadmap

| Feature | Status |
|---|---|
| Image preprocessing (low light, blur, noise) | Real, adaptive (CLAHE/denoise/sharpen applied only when needed) |
| Vehicle & road-user detection + classification | Real, with confidence scores and box de-duplication |
| Helmet non-compliance | Real (YOLOv8, `models/helmet_best.pt`) |
| Triple riding | Real — rule-based box geometry + pose-based seated/standing check, no training needed |
| Stop-line / red-light violation | Real, operator-calibrated per camera (stop-line position + signal state set per upload) |
| Illegal parking | Real, operator-calibrated restricted zone (single-image overlap check, not video dwell-time) |
| License plate detection + OCR | Real — classical-CV plate region localization + EasyOCR, falls back to a fixed crop if no candidate region is found |
| Evidence generation (annotated image + metadata) | Real, SQLite-backed |
| Analytics, trends, CSV export | Real |
| Performance evaluation (Precision/Recall/F1/mAP) | Real — see `reports/helmet_model_metrics.json`, regenerate via `scripts/evaluate_helmet_model.py` |
| Seatbelt non-compliance, wrong-side driving | Not implemented — seatbelt needs a trained classifier (no dataset yet), wrong-side needs multi-frame tracking (single images can't show direction of travel). See the **Future Scope** page in the app. |

## Next steps (training)

The helmet model should be retrained on Colab GPU using the existing
`datasets/helmet_yolo` split (prepared by `scripts/prepare_dataset.py`)
on more varied, real-world street scenes — current validation metrics
(97% mAP50) are strong on held-out data from the same distribution, but
the model under-detects on busier, more cluttered street photos. A
plate-detector model needs a new annotated dataset (none exists yet)
before the classical-CV localization can be replaced with a trained
detection box.
