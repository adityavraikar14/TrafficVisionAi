# TrafficVision AI — Complete Project Summary

**From Detection to Digital Evidence.** An AI-powered traffic-violation detection and evidence-generation platform: upload a photo or video, the system runs it through real preprocessing and detection models, generates court-ready annotated evidence, and routes it to a human officer who verifies it and can issue a real, QR-verified e-challan. Built end-to-end and actually deployed — not a notebook demo.

---

## 1. High-Level Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│   React Frontend │ ──────▶│   FastAPI Backend     │────────▶│  SQLite Database │
│   (Vercel)       │  HTTPS │   (Hugging Face Space,│         │  (file-based,     │
│                  │◀────── │    Dockerized)        │◀────────│   on-disk)        │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
                                       │
                                       ├── YOLOv8 ×5 (helmet, plate, general, pose; seatbelt unused)
                                       ├── EasyOCR (plate text)
                                       ├── OpenCV (preprocessing + classical CV fallbacks)
                                       ├── ByteTrack (multi-frame video tracking)
                                       ├── ffmpeg (Instant Replay clip extraction)
                                       └── ReportLab + qrcode (e-challan PDF generation)
```

The frontend and backend are two **separately deployed services** that talk over a real HTTP API — not a monolith, not mock JSON.

---

## 2. Full Tech Stack

### Frontend
| Tech | Purpose |
|---|---|
| React 19 + TypeScript | Entire console UI |
| Vite | Build tool / dev server |
| Tailwind CSS v4 | All styling — custom design tokens, no UI kit |
| React Router v7 | Routing, with `ProtectedRoute` auth-gating every page except Login |
| Axios | HTTP client — interceptors attach the officer's bearer token to every request, auto-redirect to `/login` on 401 |
| Recharts | Pie/bar/line charts (Dashboard, Analytics) |
| React-Leaflet + Leaflet | Live India risk map |
| Framer Motion | Card entrance animations |
| Lucide React | Icon set |

### Backend
| Tech | Purpose |
|---|---|
| FastAPI (Python) | The entire REST API |
| Uvicorn | ASGI server |
| SQLite | Database — raw SQL, no ORM, single file on disk |
| Pydantic | Request/response schema validation |

### Computer Vision / ML
| Tech | Purpose |
|---|---|
| Ultralytics YOLOv8 | Object detection framework — **5 separate models**, not one general-purpose model (see §4) |
| EasyOCR | License-plate text recognition |
| OpenCV (cv2) | All classical-CV work: CLAHE, Wiener deconvolution, Canny edge detection, morphological filtering, brightness thresholding, contour detection |
| ByteTrack | Multi-object tracking across video frames (via Ultralytics' built-in tracker) |
| NumPy | Array/image math underlying all of the above |

### Video & Document Generation
| Tech | Purpose |
|---|---|
| ffmpeg (subprocess) | Instant Replay — frame-accurate clip extraction, re-encoded to browser-playable H.264/AAC |
| ReportLab | Generates the actual e-challan PDF |
| qrcode | Scannable verification QR code embedded in every challan |

### DevOps / Deployment
| Tech | Purpose |
|---|---|
| Docker | Backend is fully containerized |
| Hugging Face Spaces | Backend hosting (free CPU tier, 16GB RAM) |
| Vercel | Frontend hosting, auto-redeploys on every GitHub push |
| Git LFS | Tracks all model weights (`.pt`), sample images, and sample videos |
| GitHub | Single source of truth feeding both deploy targets |

---

## 3. End-to-End Pipeline (what happens to one uploaded photo)

1. **Upload** — `POST /api/detect/image` receives the file, saves the original to `storage/uploads/`.
2. **Preprocessing** (`preprocessing_service.py`) — see §5 below. Runs unconditionally, but each individual correction only *applies* if its own per-image quality score crosses a threshold.
3. **Detection** — the enhanced image is fed through whichever models the violation type needs (see §4). Ultralytics is given raw BGR arrays directly (a subtle but real bug: feeding it RGB silently swaps channels and degrades every confidence score — fixed by keeping BGR end-to-end).
4. **Plate OCR** (`ocr_service.py` + `plate_service.py`) — see §6.
5. **Evidence generation** (`annotation_service.py`) — bounding boxes, labels, and confidence scores are burned directly onto a copy of the *original* (not preprocessed) image, scaled proportionally to image size so labels don't either vanish on tiny images or overlap into illegible blobs on crowded scenes.
6. **Database write** (`evidence_service.create_violation_record`) — a row is inserted into `violations` with a unique `TV-####` ID, GPS-tagged city (randomly assigned from a 29-city pool for demo purposes), and an ISO timestamp. Status starts as `Pending Review`.
7. **Officer review** — the violation sits in Evidence Center until a logged-in officer opens it, looks at the real evidence, and explicitly Verifies or Rejects it (see §9).
8. **E-Challan** — only after Verification, a real PDF can be generated (see §10).

---

## 4. Violation Types — what's real, what's a heuristic

| Violation | Detection method | Status |
|---|---|---|
| **Helmet Non-Compliance** | Custom-trained YOLOv8 model (`helmet_best.pt`), classes `With Helmet` / `Without Helmet`, gated at ≥40% confidence (`HELMET_MIN_CONFIDENCE`) | Real, trained model |
| **Triple Riding** | General detector finds the motorcycle + nearby people; `yolov8n-pose.pt` checks each nearby person's hip-to-ankle compression ratio to classify seated vs. standing — only *seated* people count as riders, so bystanders near a parked bike don't get miscounted. 3+ confirmed seated riders on one motorcycle = violation | Real, trained models + geometric posture rule |
| **Stop-Line / Red-Light Violation** | Officer calibrates a stop-line position + signal state (red/yellow/green) per camera; system checks whether a detected vehicle's box crosses or sits past that line while the signal is red | Real geometry check against an operator-calibrated zone (same setup pattern real installed traffic cameras use) |
| **Illegal Parking** | Officer calibrates a no-parking rectangle per camera; system checks bounding-box overlap ratio (≥45%) between a vehicle and that zone | Real geometry check, operator-calibrated |
| **Wrong-Side Driving** | Video only. ByteTrack tracks every vehicle across the clip; system computes each vehicle's net movement angle and compares it to an officer-marked "correct direction" angle. >120° deviation = violation. Evidence frame draws the *actual* measured travel-path arrow next to the marked-correct-direction arrow | Real — multi-frame tracking + real angle math |
| **Stunt / Wheelie Riding (photo)** | No trained classifier exists for this (no labeled dataset). Geometric heuristic: the dominant motorcycle's bounding box must be unusually tall/narrow (aspect ratio ≥1.3) **and** dominate the frame (≥10% of frame area) — validated against 9 real test photos with zero false positives. Confidence deliberately capped at 55% | Heuristic, not a trained model — explicitly flagged as an officer-review candidate, never auto-confirmed |
| **Stunt / Wheelie Riding (video) + Instant Replay** | Same aspect-ratio signal, but the frame-dominance requirement is dropped (real footage is shot from much farther away than a close-up photo, so it never fires) and replaced with **temporal persistence** — the aspect ratio must hold across multiple consecutive ByteTrack-sampled frames, which filters out single-frame noise (verified directly against real footage). On a confirmed event, ffmpeg extracts the actual 6–10 second clip from the uploaded video for the officer to scrub through — see §11 | Heuristic + real video clip extraction, confidence capped at 60% |
| **Seatbelt Non-Compliance** | A model was trained (`seat-belt.pt`) but **not shipped** — every public dataset available was shot from an in-cabin, driver-facing camera; it doesn't transfer to this app's exterior, third-person traffic-camera use case. Confirmed by direct testing, not assumed | Honestly documented as a known limitation, not faked |
| **Auto-Rickshaw / Indian vehicle classes** | Not in COCO's 80 standard classes; would need a custom-labeled dataset | Documented future scope |

---

## 5. Image Preprocessing Pipeline (`backend/app/services/preprocessing_service.py`)

Runs on every uploaded image before detection. Each correction is **conditional** — applied only if that specific defect is actually measured above a threshold, not blindly applied to every photo:

- **Shadow / uneven-lighting correction** — estimates "shadow spread" (the spatial variance of local brightness — a smooth lighting gradient has a small spread; a real shadow or harsh directional light has a large one). If above threshold, applies an illumination-normalization pass that targets the smooth multiplicative lighting gradient specifically — **blended in at only 30% strength**, because full-strength correction was found (via direct testing) to flip a correctly-detected "Without Helmet" into a false "With Helmet" on a real photo.
- **Low-light correction** — CLAHE (Contrast-Limited Adaptive Histogram Equalization), `clipLimit=2.5`, `tileGridSize=(8,8)`.
- **Rain-streak removal** — classical (pre-deep-learning) single-image rain removal: isolates a high-frequency "detail layer," suppresses the thin-vertical-streak structures characteristic of rain, recombines.
- **Motion-blur correction** — Wiener deconvolution: estimates the actual blur angle from image gradients, builds a motion point-spread-function kernel at that angle, deconvolves each color channel, then applies a light polish pass to deal with the inevitably imperfect kernel estimate.
- **Denoise** — generic sensor-noise smoothing, separate from the rain-specific pass.

The preprocessing report (shown live in the UI) returns which corrections were actually applied and the underlying measured scores (brightness, sharpness, shadow spread, rain-streak density) — not just a boolean "enhanced: true".

---

## 6. License Plate Recognition (`ocr_service.py` + `plate_service.py`)

Three independent localization strategies, tried in order, before giving up:

1. **Trained plate detector** (`plate-best.pt`) — a real bounding box, ≥35% confidence.
2. **Classical edge-density contour method** — Canny edge detection + morphological closing on the lower portion of the frame, filtered by plausible plate aspect ratio (1.8–6.0) and area ratio.
3. **Classical brightness-threshold contour method** — a *second, independent* signal added specifically because the edge-density method was found (via direct testing) to fragment real plate text into illegible character-stroke slivers on some photos. Indian plates are characteristically white/yellow backgrounds; thresholding for bright rectangular blobs catches plates the edge method misses entirely, with zero false positives introduced across the existing test set.
4. **Fixed lower-center crop** — last-resort fallback if neither localization method finds anything.

Once a candidate region is found, the crop is **upscaled** to a target height (EasyOCR is unreliable on tiny crops — a real plate read went from 12% confidence/garbled to exact and confident after upscaling + sharpening), padded by 8px (to avoid clipping the last character), and read with EasyOCR restricted to an uppercase-letter/digit charset only.

A read is only accepted if it **both**:
- Matches the real Indian plate regex (`^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4}$`)
- Clears a minimum OCR confidence (40%) — added after catching a 14%-confidence misread that happened to coincidentally match the format pattern.

If nothing qualifies, the system honestly returns `"Not Clearly Visible"` rather than guessing.

---

## 7. Repeat-Offender Detection

A live SQL aggregate, not a stored/cached value: every violation row carries a `repeat_count` computed via a correlated subquery counting how many other violations share the exact same `vehicle_number` (excluding the `"Not Clearly Visible"` placeholder, since an unreadable plate can't be confidently matched to anything). Surfaced as a "🔁 Repeat ×N" badge in Evidence Center and the Review Modal the moment it crosses 2.

---

## 8. Officer Authentication

Built from scratch — no third-party auth provider:
- `POST /api/auth/login` checks hardcoded credentials (`officer1` / `TrafficPolice@123`), returns an in-memory session token.
- `require_officer` FastAPI dependency gates every state-changing endpoint (`PATCH .../status`, `POST .../review`) — requires `Authorization: Bearer <token>`.
- The frontend wraps every route except `/login` in a `ProtectedRoute`, attaches the token to every request via an Axios interceptor, and auto-clears/redirects on a 401.
- Login is a shared station-terminal account, not a per-officer login — so every review action *also* requires the actual reviewing officer to type their name + badge ID at the point of decision (see §9), which is what actually gets logged for accountability, not the shared login identity.

---

## 9. Officer Review Workflow + Audit Trail

- **Evidence Center**: every violation, searchable by ID/plate/type/city/status, with KPI tiles (Pending / Verified / Rejected / Avg Confidence) computed live from the current result set.
- **Review Modal**: shows the original + annotated image side-by-side (or the Instant Replay video, if present), vehicle/confidence/city/timestamp, and a repeat-offender badge if applicable. An officer **cannot** Verify or Reject a record with no attached image/video — there's no "trust the AI blindly" path; if a record (e.g. synthetic demo seed data) has no evidence attached, the buttons are disabled with an explanation.
- Verify/Reject requires the officer's name + badge ID (remembered in localStorage between sessions for convenience, but always editable since the next reviewer may be different).
- **`review_log` table**: one row per decision (not overwritten on re-review) — violation ID, decision, officer name, badge ID, optional notes, timestamp. This is the permanent accountability record.
- **Review History page**: every decision ever made, searchable by officer name/badge/violation ID — built specifically so a future escalation ("why was this approved?") can be traced to exactly who decided it and when.

---

## 10. E-Challan Generation (`challan_service.py`)

Only generatable for a `Verified` violation (`GET /api/evidence/{id}/challan.pdf` returns 400 otherwise — same "can't act without evidence" principle applied consistently). The PDF (built with ReportLab, not a static template) includes:
- Violation ID, vehicle number, violation type, detection confidence, location, detected-at timestamp
- A repeat-offender note if applicable
- An **indicative fine amount** from a fixed schedule (`FINE_SCHEDULE` in `config.py` — e.g. ₹1000 for Helmet Non-Compliance, ₹500 for Illegal Parking), explicitly labeled as illustrative/non-legally-binding
- The verifying officer's name, badge ID, decision, and timestamp (pulled from `review_log`)
- The actual annotated evidence image, embedded
- A **QR code** (via the `qrcode` library) encoding a verification string — challan ID, officer, and decision timestamp

---

## 11. Instant Replay (video pipeline, `detect_video.py` + `stunt_service.py` + `video_clip_service.py`)

When a video is analyzed (Wrong-Side Driving page), the same pipeline now *also* checks every sampled frame for sustained stunt-riding geometry (see §4). When a real multi-frame event is confirmed:
1. The best (highest-confidence) frame becomes the annotated cover image, labeled with the same capped confidence reported on the violation record (not the raw, higher motorcycle-detection confidence — these are deliberately different numbers, and showing the wrong one would overstate certainty).
2. `ffmpeg` extracts a **real 6–10 second clip** from the actual uploaded video, padded symmetrically around the detected event window, re-encoded to a standard H.264/AAC mp4 so it plays back in any browser regardless of the source file's original codec.
3. The clip is stored and attached to the violation record (`evidence_video_path` column), and rendered as a scrubbable `<video>` player in the Review Modal, Evidence Center, and the Video Analysis result cards — so the officer reviews the actual moment, not just a single frame with a number attached to it.

Validated against real footage (an actual news clip of a Hyderabad stunt-riding arrest): 3 genuine events detected, all clips valid and correctly timed, zero false positives, and a real isolated single-frame noise case in that footage was correctly filtered out by the temporal-persistence requirement.

---

## 12. Analytics, Dashboard & Smart City Map

- **Dashboard**: live KPIs (total violations, helmet violations, triple riding, compliance rate, pending reviews, rejected, avg confidence), a violation-type pie chart, a 7-day trend line (violations vs. reviewed), and a "Highest Risk City" panel with the actual last-violation timestamp for that city — not a static screenshot.
- **Analytics**: category breakdowns, growth-rate KPI, bar + pie charts, all computed from the same live `/api/analytics/summary` endpoint.
- **Smart City Map**: every violation plotted on a real Leaflet map of India, color-coded by risk level, with a city-wise summary table including each city's last-violation date.
- **Reports**: one-click CSV export of the full evidence ledger.

---

## 13. Database Schema (SQLite, `backend/storage/trafficvision.db`)

**`violations`**
```
id, violation_id (TV-####), vehicle_number, violation_type, confidence,
status (Pending Review / Verified / Rejected / Escalated), city, location,
lat, lon, original_image_path, annotated_image_path, evidence_video_path,
source (upload / video / seed), created_at
```

**`review_log`**
```
id, violation_id, decision, officer_name, officer_badge_id, notes, reviewed_at
```

Schema migrations (e.g. adding `evidence_video_path` to an already-existing database) are handled defensively at startup via `PRAGMA table_info` checks + `ALTER TABLE`, so existing deployments don't break when new columns are introduced.

---

## 14. API Reference

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/auth/login` | Officer login, returns session token |
| `POST` | `/api/detect/image` | Run the full image pipeline on an uploaded photo |
| `POST` | `/api/detect/video` | Run wrong-side-driving + stunt detection on an uploaded video |
| `GET` | `/api/evidence` | List/search violations (includes live `repeat_count`) |
| `GET` | `/api/evidence/history` | List/search the officer review audit trail |
| `PATCH` | `/api/evidence/{id}/status` | Direct status update (officer-gated) |
| `POST` | `/api/evidence/{id}/review` | Submit a Verify/Reject decision with officer identity (officer-gated) |
| `GET` | `/api/evidence/{id}/challan.pdf` | Generate/download the e-challan (Verified-only) |
| `GET` | `/api/analytics/summary` | All dashboard/analytics aggregates |
| `GET` | `/api/reports/export.csv` | CSV export of the evidence ledger |
| `GET` | `/api/health` | Health check |
| `GET` | `/` | Friendly service status (so the bare backend URL doesn't look broken) |

---

## 15. Frontend Pages

`Login` · `Dashboard` · `Analyze` (Live Detection — image pipeline) · `VideoAnalysis` (Wrong-Side Driving + Stunt/Instant Replay) · `EvidenceCenter` · `ReviewHistory` · `Analytics` · `SmartCityMap` · `Reports` · `Roadmap` (Future Scope) · `About`

---

## 16. Real Bugs Found & Fixed During Development

These weren't theoretical — each was caught by testing against real photos/videos and verified fixed against the *whole* test set, not just the one case that exposed it:

- BGR/RGB channel swap silently degrading every detection's confidence
- Triple-riding false positives from bystanders standing near a parked bike (fixed with pose-based seated/standing check)
- Full-strength shadow-removal preprocessing flipping a correct "Without Helmet" into a false "With Helmet" (fixed by blending at 30%)
- Plate OCR accepting a 14%-confidence lucky-format misread as truth (fixed with a confidence floor)
- Plate crops too small/clipped for reliable OCR (fixed with upscaling, sharpening, padding)
- Vehicle-merge logic chaining unrelated parked vehicles into one fake "mega-vehicle," causing a false Triple Riding violation on pedestrians (fixed by requiring genuine box overlap, not just proximity)
- Annotation text oversized/illegible on small images, and overlapping into unreadable blobs in dense multi-vehicle scenes (fixed with size-proportional scaling + label-collision avoidance)
- Stop-line/plate-detection edge-density method fragmenting real plate text into unreadable slivers on certain photos (fixed with an independent brightness-based fallback)
- Helmet model confidently misclassifying dark/black hair as a helmet on certain photos — root-caused via a rejected texture-heuristic experiment that disproved itself with data; documented as a real model-accuracy limitation needing retraining, not patched with a fragile workaround
- Stunt-detection aspect-ratio heuristic confounded by camera angle (a normal front-on photo produces the same tall/narrow box as a wheelie) — caught using the *same test photo's own background vehicle* before shipping, fixed by adding a frame-dominance requirement for photos and a temporal-persistence requirement for video
- Video-evidence label showing the raw motorcycle-detection confidence instead of the deliberately capped stunt-confidence — caught by direct visual inspection of the generated evidence frame

---

## 17. Known Limitations (intentionally not hidden)

- **Seatbelt detection** — trained but not shipped; available datasets don't transfer to this app's camera angle.
- **Auto-rickshaw / Indian vehicle classes** — not in standard COCO classes, needs a custom dataset.
- **Stunt detection** — a validated geometric heuristic, not a trained classifier; explicitly capped confidence and framed as an officer-review candidate.
- **Demo data persistence** — both deploy targets (Hugging Face Spaces free tier, in particular) have ephemeral storage; the app auto-reseeds demo data on a fresh database, but real uploads/reviews made in one session don't survive a container restart.
- **City assignment** — for demonstration purposes, violations are assigned a random city from a 29-city pool rather than real GPS metadata (no real camera network exists to source this from yet).
