"""Coarse geometric heuristic for wheelie/stunt riding, not a trained
classifier. A wheelie lifts the front wheel and tilts the bike steeply
backward, which makes the motorcycle's bounding box noticeably taller and
narrower than normal riding.

Two different validation paths feed two different confidence guards:

- Still images (detect_stunt_riding): validated against a real wheelie
  photo and 8 unrelated sample photos — only the wheelie photo's primary
  motorcycle crosses both the aspect-ratio AND frame-dominance thresholds.
  A single frame has no temporal signal to lean on, so it also requires the
  motorcycle to dominate the frame (close-up framing), and reports a
  deliberately capped, sub-acceptance confidence.

- Video (detect_stunt_events): real footage is shot from much farther back
  than a close-up photo, so the frame-dominance threshold above never fires
  on video — verified directly against real stunt footage, where the
  genuine wheelie segments only ever filled 2-10% of the frame, far under
  the still-image bar. Video has a different, stronger signal available
  instead: temporal persistence. A single odd-angle frame is noise (an
  isolated single-frame hit in real test footage, surrounded on both sides
  by normal-riding frames, is exactly the false positive this guards
  against); a wheelie sustained across multiple consecutive sampled frames
  is real. So video drops the frame-dominance requirement and instead
  requires the aspect ratio to hold for several frames in a row.
"""

STUNT_ASPECT_MIN = 1.3
STUNT_AREA_FRACTION_MIN = 0.10
STUNT_REPORTED_CONFIDENCE_CAP = 0.55

VIDEO_STUNT_MIN_AREA_FRACTION = 0.015
VIDEO_STUNT_GAP_TOLERANCE_SEC = 2.5
VIDEO_STUNT_MIN_HITS = 2
VIDEO_STUNT_CONFIDENCE_CAP = 0.6


def _largest_motorcycle_geometry(detections: list[dict], frame_width: int, frame_height: int):
    motorcycles = [d for d in detections if d["category"] == "Two-Wheeler"]
    if not motorcycles:
        return None

    largest = max(
        motorcycles,
        key=lambda d: (d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1]),
    )
    x1, y1, x2, y2 = largest["box"]
    box_w, box_h = x2 - x1, y2 - y1
    if box_w <= 0 or box_h <= 0:
        return None

    frame_area = frame_width * frame_height
    return {
        "det": largest,
        "aspect": box_h / box_w,
        "area_fraction": (box_w * box_h) / frame_area,
    }


def detect_stunt_riding(detections: list[dict], frame_width: int, frame_height: int) -> list[dict]:
    geo = _largest_motorcycle_geometry(detections, frame_width, frame_height)
    if not geo:
        return []

    if geo["aspect"] >= STUNT_ASPECT_MIN and geo["area_fraction"] >= STUNT_AREA_FRACTION_MIN:
        return [
            {
                "violation_type": "Stunt Riding",
                "confidence": min(geo["det"]["confidence"], STUNT_REPORTED_CONFIDENCE_CAP),
                "box": geo["det"]["box"],
            }
        ]
    return []


def detect_stunt_in_video_frame(detections: list[dict], frame_width: int, frame_height: int) -> dict | None:
    """Single-frame check for the video pipeline — same aspect signal,
    but a much lower area floor (just enough to reject specks/noise) since
    real footage is shot from farther back. Returns the raw hit; the
    caller (detect_stunt_events) is responsible for requiring this to
    persist across multiple frames before treating it as real."""
    geo = _largest_motorcycle_geometry(detections, frame_width, frame_height)
    if not geo:
        return None
    if geo["aspect"] >= STUNT_ASPECT_MIN and geo["area_fraction"] >= VIDEO_STUNT_MIN_AREA_FRACTION:
        return {"confidence": geo["det"]["confidence"], "box": geo["det"]["box"]}
    return None


def detect_stunt_events(frame_hits: list[tuple[float, dict]]) -> list[dict]:
    """Group per-frame stunt hits (timestamp_sec, hit) into discrete events:
    consecutive hits within VIDEO_STUNT_GAP_TOLERANCE_SEC of each other
    belong to the same event, and an event needs at least
    VIDEO_STUNT_MIN_HITS hits to survive — filters out the single-frame
    noise case described above while keeping genuine multi-second bursts.
    """
    if not frame_hits:
        return []

    frame_hits = sorted(frame_hits, key=lambda fh: fh[0])
    events: list[list[tuple[float, dict]]] = [[frame_hits[0]]]
    for ts, hit in frame_hits[1:]:
        if ts - events[-1][-1][0] <= VIDEO_STUNT_GAP_TOLERANCE_SEC:
            events[-1].append((ts, hit))
        else:
            events.append([(ts, hit)])

    results = []
    for event in events:
        if len(event) < VIDEO_STUNT_MIN_HITS:
            continue
        best_ts, best_hit = max(event, key=lambda fh: fh[1]["confidence"])
        results.append(
            {
                "start_time": event[0][0],
                "end_time": event[-1][0],
                "best_time": best_ts,
                "best_hit": best_hit,
                "hit_count": len(event),
                "confidence": min(best_hit["confidence"], VIDEO_STUNT_CONFIDENCE_CAP),
            }
        )
    return results
