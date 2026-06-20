import { useRef, useState } from "react";
import { UploadCloud, ScanSearch, Navigation, Car, PlayCircle } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { Chip, StatusChip, formatConfidence } from "../components/Chip";
import { analyzeVideo, mediaUrl, type VideoDetectionResponse } from "../api/client";

export default function VideoAnalysis() {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [angle, setAngle] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VideoDetectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const onPick = (f: File) => {
    setFile(f);
    setResult(null);
    setError(null);
    setPreview(URL.createObjectURL(f));
  };

  const runAnalysis = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeVideo(file, angle);
      setResult(res);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Video analysis failed. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="🚗 Wrong-Side Driving" subtitle="Multi-frame vehicle tracking for direction-of-travel violations">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xl font-black text-tv-text">Video Detection Console</div>
          <p className="text-tv-muted text-sm mt-1">
            Upload a short traffic clip and mark the correct direction of travel for this road segment.
            Vehicles are tracked across frames (ByteTrack) and flagged if their net movement deviates
            sharply from the marked direction.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="tv-pill">Multi-Frame Tracking</span>
          <span className="tv-pill">Max 60s clips</span>
        </div>
      </div>

      <Card className="border-tv-warning/30">
        <div className="flex gap-3 items-start">
          <span className="text-xl">⚠️</span>
          <div className="text-sm text-tv-muted leading-relaxed">
            <span className="text-tv-text font-bold">Built for fixed/pole-mounted traffic cameras, not dashcams.</span>{" "}
            Direction-of-travel is computed as straight-line movement across a static frame. Footage from
            a moving vehicle (dashcam, handheld) has camera motion mixed into every vehicle's apparent
            movement, which this logic isn't designed to separate out — results on that kind of footage
            won't be reliable.
          </div>
        </div>
      </Card>

      <Card>
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) onPick(f);
          }}
          className="border border-dashed border-tv-primary/35 bg-tv-bg-soft/60 rounded-2xl py-10 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-tv-primary/60 transition"
        >
          <UploadCloud size={32} className="text-tv-primary" />
          <div className="font-bold text-tv-text">Click or drop a traffic video (MP4 / AVI / MOV)</div>
          <div className="text-tv-muted text-sm">Short clips work best — up to 30 seconds</div>
          <input
            ref={inputRef}
            type="file"
            accept="video/mp4,video/x-msvideo,video/quicktime,video/x-matroska"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onPick(f);
            }}
          />
        </div>
      </Card>

      {preview && !result && (
        <Card title="Direction Calibration" badge="Per-Camera Setup">
          <p className="text-tv-muted text-sm mb-3">
            Mark which way traffic should legally flow on this road segment. Vehicles tracked moving
            more than 120° away from this direction get flagged.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="relative rounded-xl overflow-hidden border border-tv-border bg-black">
              <video src={preview} controls className="w-full h-auto block max-h-[320px]" />
              <div className="absolute top-3 right-3 flex flex-col items-center gap-1 bg-black/40 rounded-xl p-2">
                <Navigation
                  size={28}
                  className="text-tv-success"
                  style={{ transform: `rotate(${angle + 90}deg)`, transition: "transform 120ms ease" }}
                />
                <span className="text-[10px] font-bold text-tv-success">Correct Direction</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-tv-muted mb-1">
                <span>Correct direction angle</span><span>{angle}°</span>
              </div>
              <input
                type="range" min={0} max={359} value={angle}
                onChange={(e) => setAngle(Number(e.target.value))}
                className="w-full"
              />
              <div className="text-tv-muted text-xs mt-2 leading-relaxed">
                0° = rightward across the frame, 90° = downward (toward camera), 180° = leftward, 270° = upward (away from camera).
                Match this to the direction vehicles should legally be moving.
              </div>
            </div>
          </div>
        </Card>
      )}

      {preview && !result && (
        <button
          onClick={runAnalysis}
          disabled={loading}
          className="self-start flex items-center gap-2 bg-gradient-to-br from-tv-primary to-tv-primary/85 text-white font-bold px-5 py-3 rounded-xl hover:-translate-y-0.5 transition disabled:opacity-60"
        >
          <ScanSearch size={18} />
          {loading ? "Tracking vehicles… this can take a moment" : "Run Video Analysis"}
        </button>
      )}

      {error && <Card>{error}</Card>}

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Kpi label="Vehicles Tracked" value={result.vehicles_tracked} subtext="Unique tracked vehicles" icon={<Car size={18} />} tone="info" />
            <Kpi label="Frames Processed" value={result.frames_processed} subtext={`${result.video_duration_sec}s clip`} icon={<ScanSearch size={18} />} tone="primary" />
            <Kpi label="Violations Detected" value={result.violations.length} subtext="Wrong-side driving cases" icon={<Navigation size={18} />} tone="violation" />
          </div>

          {result.is_compliant ? (
            <Card title="Compliance Result">
              <Chip text="Compliant" variant="green" />
              <div className="mt-3 text-tv-text/85 font-semibold">✅ No vehicles found traveling against the marked direction.</div>
            </Card>
          ) : (
            <Card title="Digital Evidence Cards" badge={`${result.violations.length} Found`}>
              <div className="flex flex-col gap-4">
                {result.violations.map((v) => (
                  <div key={v.violation_id} className="border border-tv-violation/25 bg-tv-violation/5 rounded-2xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-black text-tv-text text-sm">{v.violation_id}</span>
                      <span className="text-tv-muted text-xs">Recorded — see Evidence Center to review</span>
                    </div>
                    {v.evidence_video_path ? (
                      <div className="mb-3">
                        <div className="flex items-center gap-1.5 text-tv-violation text-[11px] font-bold mb-1.5">
                          <PlayCircle size={14} /> Instant Replay
                        </div>
                        <video src={mediaUrl(v.evidence_video_path)} controls loop className="rounded-xl w-full max-h-[360px] bg-black" />
                      </div>
                    ) : (
                      <img src={mediaUrl(v.annotated_image_path)} className="rounded-xl w-full max-h-[360px] object-contain mb-3" />
                    )}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="font-black text-tv-text text-sm">Vehicle Number</div>
                        <div className="text-tv-muted text-sm mt-1">{v.vehicle_number}</div>
                      </div>
                      <div>
                        <div className="font-black text-tv-text text-sm">Confidence</div>
                        <div className="text-tv-muted text-sm mt-1">{formatConfidence(v.confidence)}</div>
                      </div>
                      <div>
                        <div className="font-black text-tv-text text-sm">Violation Type</div>
                        <div className="text-tv-muted text-sm mt-1">{v.violation_type}</div>
                      </div>
                      <div className="flex items-end">
                        <StatusChip status={v.status} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </Layout>
  );
}
