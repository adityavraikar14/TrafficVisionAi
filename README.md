---
title: TrafficVision AI
emoji: 🚦
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

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

## Running locally (after cloning this repo)

### Prerequisites
- **Python 3.11** (3.9–3.12 also work)
- **Node.js 18+** and npm
- **ffmpeg** on your system `PATH` — needed for the Instant Replay (stunt-detection video clip) feature
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **Git LFS** — this repo's model weights (`models/*.pt`) and sample media (`sample_images/`) are tracked via Git LFS. Install it once before cloning: https://git-lfs.com, then `git lfs install`. If you already cloned without it, run `git lfs pull` inside the repo afterward.

### 1. Clone
```
git clone https://github.com/adityavraikar14/TrafficVisionAi.git
cd TrafficVisionAi
```

### 2. Backend (FastAPI, port 8000) — first terminal
```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
The first request after startup is slow (loading 5 YOLOv8 models + EasyOCR into memory); everything after that is fast.

### 3. Frontend (Vite dev server, port 5173) — second terminal
```
cd frontend
npm install
npm run dev
```

### 4. Open it
Go to **http://localhost:5173** — the Vite dev server automatically proxies `/api` and `/storage` requests to the backend (see `frontend/vite.config.ts`), so no extra config is needed.

**Login**: `officer1` / `TrafficPolice@123`

The database seeds itself with demo violation data on first run (`backend/app/core/db.py`) so the dashboards aren't empty before you upload anything. Try **Live Detection** with a photo from `sample_images/`, or **Wrong-Side Driving** with `sample_images/stunt-video.mp4` to see Instant Replay.

## What's real vs. roadmap

| Feature | Status |
|---|---|
| Image preprocessing (low light, blur, noise) | Real, adaptive (CLAHE/denoise/sharpen applied only when needed) |
| Vehicle & road-user detection + classification | Real, with confidence scores and box de-duplication |
| Helmet non-compliance | Real (YOLOv8, `models/helmet_best.pt`) |
| Triple riding | Real — rule-based box geometry + pose-based seated/standing check, no training needed |
| Stop-line / red-light violation | Real, operator-calibrated per camera (stop-line position + signal state set per upload) |
| Illegal parking | Real, operator-calibrated restricted zone (single-image overlap check, not video dwell-time) |
| Wrong-side driving | Real — the one violation that genuinely needs video (direction of travel isn't recoverable from a single frame). Multi-frame ByteTrack tracking + direction-vs-marked-correct-angle comparison. `/video-analysis` page, max 60s clips |
| License plate detection | Real — trained YOLOv8 detector (`models/plate-best.pt`, 98.6% precision / 94.6% recall / 97% mAP50 on its validation split), falls back to classical-CV region localization if the model finds nothing |
| License plate OCR | Real — EasyOCR + regex validation on the detected plate region |
| Evidence generation (annotated image + metadata) | Real, SQLite-backed |
| Analytics, trends, CSV export | Real |
| Performance evaluation (Precision/Recall/F1/mAP + latency) | Real for all 4 active models — see `reports/*.json`, regenerate via `scripts/evaluate_*.py` |
| Seatbelt non-compliance | **Not implemented** — trained a classifier, then a detector, on 5+ public datasets; every one is captured from in-cabin driver-facing cameras (fleet-monitoring use case), which doesn't transfer to our exterior-camera pipeline. Confirmed via direct testing (model confidently mis-classified all 3 real test cases), not assumed. A genuinely hard, recognized problem in the field (windshield glare/angle/tint) — see **Future Scope** in the app |
| Auto-rickshaw / Indian vehicle classes | Not implemented — deferred, needs a custom-labeled dataset (not in COCO's 80 classes) |

## Next steps (training)

The helmet model should be retrained on Colab GPU using the existing
`datasets/helmet_yolo` split (prepared by `scripts/prepare_dataset.py`)
on more varied, real-world street scenes — current validation metrics
(97% mAP50) are strong on held-out data from the same distribution, but
the model under-detects on busier, more cluttered street photos.

Seatbelt and auto-rickshaw detection both need a dataset that doesn't
appear to exist publicly yet (exterior, third-person vehicle photos —
not in-cabin crops, and not COCO's 80 classes, respectively). Either
would need custom data collection/labeling before a training cycle
could start.
