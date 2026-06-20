# TrafficVision AI — Demo Script

*Tone: confident, conversational, a little proud. You're not reading a feature list — you're showing off something that actually works. Pause after each "wow" beat and let the screen do the talking.*

---

## 0. Cold Open (10 seconds, before you even open the laptop)

> "Every Indian city already has thousands of traffic cameras. The problem was never the cameras — it's that nobody's watching them in real time, and even when a violation gets caught, there's no system turning that footage into something a court or a challan can actually use. That's what we built. Not a toy detector — a full pipeline from a raw camera frame to a signed, QR-verified digital challan."

*[Open the Vercel link. Let it sit on the login page for a second.]*

---

## 1. Login — "This isn't a demo toy, it's a console"

> "First thing — this isn't a public website anyone can spam. It's an officer console. You log in as a duty officer, badge and all, the same way you'd log into any enforcement terminal at a station."

*[Type in officer1 / TrafficPolice@123, log in.]*

> "And that's not cosmetic — every single action this system takes later, someone's name and badge ID gets attached to it. You'll see why that matters in a minute."

---

## 2. Dashboard — "The 10-second version of everything"

> "This is the view a station in-charge would actually live in. Total violations, helmet non-compliance, triple riding, compliance rate — all computed live from the database, not hardcoded numbers."

*[Point at the KPI row.]*

> "Pending Reviews, Verified, Rejected — these three numbers are the heartbeat of the whole system. Every detection starts as 'Pending,' and stays a draft until a human officer looks at the evidence and makes the call. The AI never gets the final word — it just does the looking."

*[Scroll to the violation distribution pie + city risk panel.]*

> "And this isn't just 'Mumbai has the most violations' — see the date stamp? Highest Risk City, as of today, with the actual last-violation timestamp for that city. This updates itself every time a new detection lands — it's not a static screenshot."

---

## 3. Live Detection — "Watch what happens to one photo"

> "This is the core of the system. I'm going to upload one photo and walk you through everything that happens to it before you ever see a result — because there's a lot happening that's invisible in most 'AI detection' demos."

*[Upload a photo — pick one with a visible violation and plate.]*

### Step 1 — Image Preprocessing
> "Before any detection model even sees this image, it goes through a real preprocessing pipeline — not a placeholder. The system measures shadow spread, brightness, rain-streak density, and motion blur on the raw image, and only applies a correction if that specific problem is actually detected."

*[Point at the Preprocessing Report card after results load.]*

> "Shadow correction — that's an illumination-normalization pass that targets uneven lighting specifically, blended at 30% strength so it never overcorrects a perfectly fine photo. Low-light correction is CLAHE — adaptive histogram equalization. Rain-streak removal uses a classical morphological filter that isolates thin vertical streak structures and suppresses them before they confuse the detector. And if the photo's motion-blurred — say, a fast-moving bike — we run Wiener deconvolution: we estimate the actual motion blur angle from the image gradients, build a motion kernel, and deconvolve it back out."

> "None of this is decorative. We found a real bug during testing where full-strength shadow removal flipped a correctly-detected 'without helmet' into a false 'with helmet' — so now it only blends in at 30%, and only when the shadow score crosses a real threshold."

### Step 2 — Detection
> "Now the actual models run. We're not using one model for everything — that's a rookie mistake. There's a custom-trained YOLOv8 model just for helmet compliance, a separate general detector for classifying vehicles and pedestrians, and a pose-estimation model that we use specifically to solve a problem most triple-riding detectors get wrong."

*[Point at road user detections / bounding boxes.]*

> "Watch — every box you see has a real confidence score next to it. We don't show a violation unless it clears a minimum confidence bar. That bar exists because we caught the model accepting low-confidence lucky guesses early on, and decided that's not acceptable for something that could become a legal document."

### Step 3 — Triple Riding (if relevant)
> "Triple riding sounds simple — count heads on a bike — but bystanders standing near a parked bike kept getting miscounted as riders. So we run pose estimation on every nearby person, check their knee angle, and only count someone as a 'rider' if their posture says seated, not standing. That one fix alone killed a whole category of false positives."

### Step 4 — Plate Recognition
> "And this is the part everyone gets wrong in academic projects — plate reading. We don't just throw the whole photo at OCR and hope. There's a trained plate detector first. If that finds nothing, we fall back to a classical edge-density contour method. If *that* finds nothing either, we fall back to a second, completely different signal — brightness thresholding, because Indian plates are characteristically white or yellow backgrounds, which edge-detection alone can miss entirely. Three independent attempts, in order, before we give up."

*[Point at the plate number in the result, if read.]*

> "And only after we get a real OCR read that matches the actual Indian plate format — two letters, two digits, two letters, four digits — and clears a confidence threshold, do we accept it. A low-confidence guess that happens to *look* like a plate format isn't good enough — we had that exact bug and fixed it."

### Step 5 — Evidence Generation
> "The moment a violation is confirmed, the system generates an annotated evidence image — bounding boxes, labels, confidence scores burned directly onto the photo — and stores it with a unique violation ID, GPS-tagged city, and an exact timestamp, in a real database. Not in memory. Not lost on refresh."

---

## 4. Wrong-Side Driving — "This is where it gets real video intelligence"

*[Navigate to Wrong-Side Driving.]*

> "Stills can only tell you so much. For wrong-side driving, you need movement — so this is the one feature that runs on actual video, frame by frame."

*[Set the correct-direction angle slider, upload a clip.]*

> "Before running it, you mark which direction traffic is *supposed* to flow on this road — same as a real camera installer would configure once per intersection. Then we track every vehicle across the entire clip using ByteTrack, a real multi-object tracker, not just frame-by-frame detection — it maintains identity for each vehicle as it moves."

*[Let it process, show result.]*

> "Watch the evidence frame it generates — see that arrow? That's not decoration. The red arrow is the vehicle's *actual* measured travel path across the video, calculated from its tracked positions frame to frame. The green arrow in the corner is the direction you marked as correct. If the angle between those two arrows is more than 120 degrees, that's a real wrong-side violation — and the system shows you the exact geometry, not just a label saying 'wrong way.' You can see *why* it was flagged."

---

## 5. Evidence Center — "Where AI hands off to a human"

*[Navigate to Evidence Center.]*

> "Every violation the AI has ever flagged lands here, and this is the part most hackathon projects skip entirely — what happens *after* detection."

*[Click a Pending row.]*

> "Click any pending case, and you get the full evidence package — original photo next to the annotated one, vehicle number, confidence, timestamp. The officer reviewing this isn't trusting a black box — they're looking at exactly what the AI saw."

*[Point at the officer name/badge fields.]*

> "Before they can act, they identify themselves — name and badge ID — because this is a shared station terminal, and 'the AI flagged it' isn't accountability. 'Officer Rao, badge 4521, reviewed and verified it at 10:42 AM' is."

*[Click Verify.]*

> "Verify, and watch — instantly, a downloadable e-challan generates. Real PDF, with the annotated evidence photo embedded, the fine amount, the officer's name and badge, and a QR code that encodes the verification details. This isn't 'we detected a violation' — this is 'here's a document you could actually hand someone.'"

*[Point at the Repeat badge if visible.]*

> "And see this — 'Repeat ×3'? That's not manually flagged. The system cross-references every violation's plate number against every other violation in the database, live. Same plate showing up a third time gets surfaced automatically, right at the point an officer is deciding how seriously to treat it."

---

## 6. Review History — "The audit trail nobody else built"

*[Navigate to Review History.]*

> "Every single Verify or Reject decision ever made lives here permanently — who made it, their badge ID, when, and any notes they left. If this ever gets escalated — a citizen disputes a fine, an internal review happens — there's a complete, unforgeable paper trail of exactly which officer made which call and why. Most prototypes stop at 'detected.' We built all the way through to 'accountable.'"

---

## 7. Analytics & Smart City Map — "Now zoom out"

*[Navigate to Analytics.]*

> "Zooming out from individual cases — violation trends over time, category breakdowns, growth rate, all computed from real stored data."

*[Navigate to Smart City Map.]*

> "And this is the bird's-eye view — every violation plotted on an actual map of India, color-coded by risk level, with the highest-risk city and its last-violation timestamp shown live. This is what a state transport department would actually want to look at every morning to decide where to deploy more enforcement."

---

## 8. Stunt Riding + Instant Replay — "The one we're proud of for a different reason"

*[Upload sample_images/stunt-video.mp4 on the Wrong-Side Driving page — yes, the same video pipeline does both checks in one pass.]*

> "One more thing — stunt and wheelie detection. We didn't have a labeled dataset to train a classifier for this, so instead of faking it, we built a real geometric signal: a wheelie tilts the bike back and lifts the front wheel, which makes its bounding box noticeably taller and narrower than normal riding."

> "On a single photo, that's all we have to go on, so we also require the bike to dominate the frame — a close-up shot — and we report it at a deliberately capped, sub-acceptance confidence, because one frame alone shouldn't make the final call."

> "But video gives us something a photo never can: *time*. We tested this against real footage — actual news coverage of a Hyderabad stunt-riding arrest — and found the frame-dominance rule never fires on video, because real footage is shot from much further away. So for video, we use a stronger signal instead: the aspect ratio has to hold for *multiple consecutive sampled frames in a row*. A single odd-angle frame is noise — we proved that directly, an isolated one-frame false read in this exact footage got filtered out automatically. A wheelie sustained for a second or more is real."

*[Let the result load — point at the violation card.]*

> "And here's the part that actually answers the question every officer would ask: 'how do I know the AI didn't just imagine this?' Watch — instead of one annotated still frame, the system clips the real 6-to-10 seconds of footage around the moment it detected, using ffmpeg, frame-accurate, from the actual uploaded video. This is Instant Replay."

*[Click into the violation in Evidence Center — the player loads.]*

> "The officer doesn't take our word for it. They scrub through the actual clip themselves, exactly like reviewing dashcam footage, before they decide Verify or Reject. We're not asking anyone to trust a confidence score — we're showing them the moment."

---

## 9. Future Scope — "We know exactly where the edges are"

*[Navigate to Roadmap.]*

> "And honestly — this page matters as much as any feature page. Seatbelt detection: every public dataset we tested was shot from inside the cabin, not from an external traffic camera, so it doesn't transfer, and we'd rather say that clearly than ship something that quietly fails. Auto-rickshaws aren't in standard detection classes yet. Predictive analytics is next. We're not pretending this is finished — we're showing you exactly what's real today and what's deliberately not."

---

## 10. Closing

> "So to recap what you just watched: a real preprocessing pipeline that adapts per-image, five specialized detection models instead of one generic one, three-tier plate recognition with classical CV fallbacks, pose-based false-positive filtering, real multi-frame video tracking for both wrong-side driving and stunt detection, Instant Replay clips so an officer reviews actual footage instead of a single frame, a full officer-review workflow with a permanent audit trail, automatic repeat-offender detection, and auto-generated e-challans with QR verification — all backed by a real database, not mock JSON, and all of it actually deployed and live right now, not running off my laptop. From a single photo to an officer-signed digital challan. That's TrafficVision AI."

*[Beat. Let it land. Don't keep talking after this line.]*

---

## Tech Stack — say this if a judge asks "what did you actually build this with?"

**Frontend**
- **React 19 + TypeScript** — the whole console UI
- **Vite** — build tooling
- **Tailwind CSS v4** — every page's styling, custom design tokens (no UI kit)
- **React Router v7** — client-side routing, with the auth-gate (`ProtectedRoute`) wrapping every page except Login
- **Axios** — API client, with interceptors that attach the officer's auth token to every request and auto-redirect to login on a 401
- **Recharts** — Dashboard/Analytics charts (pie, bar, line)
- **React-Leaflet + Leaflet** — the live India risk map
- **Framer Motion** — card entrance animations
- **Lucide React** — icon set

**Backend**
- **FastAPI** (Python) — the entire API
- **Uvicorn** — ASGI server
- **SQLite** — the database. No ORM, raw SQL, on purpose — small enough to be transparent, real enough to persist everything (violations, review audit log, repeat-offender aggregates)
- **Pydantic** — request/response schemas

**Computer Vision / ML — five separate models, not one**
- **Ultralytics YOLOv8** trained/fine-tuned for: helmet compliance (`helmet_best.pt`), license plates (`plate-best.pt`); stock `yolov8s.pt` for general vehicle/pedestrian detection; `yolov8n-pose.pt` for the rider-posture check that filters out bystanders from triple-riding counts
- **EasyOCR** — plate text recognition, gated by a confidence threshold + a regex match against the real Indian plate format before any read is accepted
- **OpenCV** — every classical-CV piece: CLAHE low-light correction, Wiener deconvolution for motion blur, Canny edge detection and brightness-threshold contour detection (the two independent plate-localization fallbacks), rain-streak morphological filtering
- **ByteTrack** (via Ultralytics' built-in tracker) — multi-object tracking across video frames, used for both Wrong-Side Driving and the stunt-detection temporal-persistence check
- **NumPy** — the underlying array math for all of the above

**Video & Document Generation**
- **ffmpeg** (subprocess) — Instant Replay: frame-accurate clip extraction, re-encoded to browser-playable H.264/AAC regardless of the source video's original codec
- **ReportLab** — generates the actual e-challan PDF (not a template screenshot — real generated text, embedded evidence image, layout)
- **qrcode** — the scannable verification QR code embedded in every challan

**Auth**
- Built from scratch, not a third-party auth provider — a login endpoint, an in-memory session token, and a `require_officer` dependency gating every state-changing endpoint (review decisions, status updates)

**DevOps & Deployment — this is genuinely live, not a localhost demo**
- **Docker** — the backend is fully containerized
- **Hugging Face Spaces** — backend hosting, free CPU tier
- **Vercel** — frontend hosting, auto-redeploys on every GitHub push
- **Git LFS** — tracks every model weight, sample image, and sample video so the repo itself stays clean
- **GitHub** — single source of truth feeding both deploy targets

---

## Quick reference — what to say if a judge asks "is this real or hardcoded?"

| Feature | Answer |
|---|---|
| Preprocessing | Real — measures shadow/brightness/rain/blur per-image, only corrects what's actually detected |
| Helmet / Triple Riding | Real trained models + pose-based posture filtering |
| Plate OCR | Real — trained detector → edge-CV fallback → brightness-CV fallback → EasyOCR with confidence + regex gating |
| Wrong-Side Driving | Real — ByteTrack multi-frame tracking, angle math against operator-marked direction |
| Stop-Line / Red-Light / Parking | Real geometry checks against operator-calibrated zones (same pattern real installed cameras use — one-time per-camera setup) |
| Stunt Riding (photo) | A real geometric heuristic (aspect ratio + frame dominance), not a trained model — explicitly capped confidence, framed as officer-review candidate |
| Stunt Riding (video) + Instant Replay | Real — temporal persistence across consecutive ByteTrack-sampled frames, real ffmpeg clip extraction from the actual uploaded footage, not a generated/faked video |
| Repeat Offender | Real live SQL aggregate on plate number, not mocked |
| E-Challan | Real PDF generation (ReportLab) with embedded evidence image + real QR code (qrcode lib) |
| Officer Review / Audit Trail | Real — persisted to SQLite, every decision logged with officer identity + timestamp |
| Seatbelt detection | Honestly not shipped — documented limitation, not faked |
| Deployment | Real — Docker container on Hugging Face Spaces (backend) + Vercel (frontend), not running off a laptop |
