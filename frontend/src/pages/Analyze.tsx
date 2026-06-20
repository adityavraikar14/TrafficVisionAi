import { useRef, useState } from "react";
import { UploadCloud, ScanSearch, ShieldAlert, BadgeCheck, Sliders } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { Chip, StatusChip, formatConfidence } from "../components/Chip";
import { analyzeImage, mediaUrl, type DetectionResponse, type ZoneCalibration } from "../api/client";

const DEFAULT_ZONES: ZoneCalibration = {
  enableSignalZone: false,
  stopLineY: 60,
  signalState: "red",
  enableParkingZone: false,
  zoneTop: 55,
  zoneBottom: 90,
  zoneLeft: 0,
  zoneRight: 30,
};

export default function Analyze() {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DetectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [zones, setZones] = useState<ZoneCalibration>(DEFAULT_ZONES);
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
      const res = await analyzeImage(file, zones);
      setResult(res);
    } catch {
      setError("Analysis failed. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="🔍 Live Detection" subtitle="AI-powered violation detection and evidence-grade record">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xl font-black text-tv-text">Detection Console</div>
          <p className="text-tv-muted text-sm mt-1">Upload a traffic image to run helmet, triple-riding, red-light/stop-line, and illegal-parking detection.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="tv-pill">YOLOv8 Helmet Model</span>
          <span className="tv-pill">EasyOCR Plate Extraction</span>
          <span className="tv-pill">Zone-Calibrated Rules</span>
        </div>
      </div>

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
          <div className="font-bold text-tv-text">Click or drop a traffic image (JPG / PNG)</div>
          <div className="text-tv-muted text-sm">Runs locally against your FastAPI detection backend</div>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onPick(f);
            }}
          />
        </div>
      </Card>

      {preview && !result && (
        <Card title="Violation Zone Calibration (Optional)" badge="Per-Camera Setup">
          <p className="text-tv-muted text-sm mb-3">
            Red-light/stop-line and illegal-parking detection need to know where the stop line and
            restricted zone are for this camera — calibrate them below, or skip and only run helmet +
            triple-riding detection.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="relative rounded-xl overflow-hidden border border-tv-border">
              <img src={preview} className="w-full h-auto block" />
              {zones.enableSignalZone && (
                <div
                  className="absolute left-0 w-full border-t-2 border-white/90 flex items-center"
                  style={{ top: `${zones.stopLineY}%` }}
                >
                  <span className="bg-white text-black text-[10px] font-bold px-1.5 py-0.5 -translate-y-1/2">Stop Line</span>
                </div>
              )}
              {zones.enableParkingZone && (
                <div
                  className="absolute border-2 border-tv-warning bg-tv-warning/15"
                  style={{
                    top: `${zones.zoneTop}%`,
                    left: `${zones.zoneLeft}%`,
                    width: `${zones.zoneRight - zones.zoneLeft}%`,
                    height: `${zones.zoneBottom - zones.zoneTop}%`,
                  }}
                >
                  <span className="bg-tv-warning text-black text-[10px] font-bold px-1.5 py-0.5">No-Parking Zone</span>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-5">
              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-tv-text cursor-pointer">
                  <input
                    type="checkbox"
                    checked={zones.enableSignalZone}
                    onChange={(e) => setZones({ ...zones, enableSignalZone: e.target.checked })}
                  />
                  <Sliders size={14} /> Enable Stop-Line / Red-Light Check
                </label>
                {zones.enableSignalZone && (
                  <div className="mt-3 flex flex-col gap-3 pl-1">
                    <div>
                      <div className="flex justify-between text-xs text-tv-muted mb-1">
                        <span>Stop line position</span><span>{zones.stopLineY}%</span>
                      </div>
                      <input
                        type="range" min={0} max={100} value={zones.stopLineY}
                        onChange={(e) => setZones({ ...zones, stopLineY: Number(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-tv-muted">Signal state</span>
                      <select
                        value={zones.signalState}
                        onChange={(e) => setZones({ ...zones, signalState: e.target.value as ZoneCalibration["signalState"] })}
                        className="bg-tv-bg-soft border border-tv-border rounded-lg px-2 py-1 text-sm text-tv-text"
                      >
                        <option value="red">Red</option>
                        <option value="yellow">Yellow</option>
                        <option value="green">Green</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-tv-text cursor-pointer">
                  <input
                    type="checkbox"
                    checked={zones.enableParkingZone}
                    onChange={(e) => setZones({ ...zones, enableParkingZone: e.target.checked })}
                  />
                  <Sliders size={14} /> Enable Illegal-Parking Zone Check
                </label>
                {zones.enableParkingZone && (
                  <div className="mt-3 grid grid-cols-2 gap-3 pl-1">
                    {(["zoneTop", "zoneBottom", "zoneLeft", "zoneRight"] as const).map((key) => (
                      <div key={key}>
                        <div className="flex justify-between text-xs text-tv-muted mb-1">
                          <span>{key.replace("zone", "")}</span><span>{zones[key]}%</span>
                        </div>
                        <input
                          type="range" min={0} max={100} value={zones[key]}
                          onChange={(e) => setZones({ ...zones, [key]: Number(e.target.value) })}
                          className="w-full"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {preview && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Card title="Original Image">
            <img src={preview} className="rounded-xl w-full object-contain max-h-[420px]" />
          </Card>
          <Card title="Detection Result">
            {result ? (
              <img src={mediaUrl(result.annotated_image_url)} className="rounded-xl w-full object-contain max-h-[420px]" />
            ) : (
              <div className="border border-dashed border-tv-border rounded-2xl py-16 text-center text-tv-muted font-semibold">
                {loading ? "Analyzing image…" : "Run AI Analysis to see detection output"}
              </div>
            )}
          </Card>
        </div>
      )}

      {preview && !result && (
        <button
          onClick={runAnalysis}
          disabled={loading}
          className="self-start flex items-center gap-2 bg-gradient-to-br from-tv-primary to-tv-primary/85 text-white font-bold px-5 py-3 rounded-xl hover:-translate-y-0.5 transition disabled:opacity-60"
        >
          <ScanSearch size={18} />
          {loading ? "Analyzing…" : "Run AI Analysis"}
        </button>
      )}

      {error && <Card>{error}</Card>}

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Kpi
              label="Violations Detected"
              value={result.violations.length}
              subtext="Across all detection rules"
              icon={<ShieldAlert size={18} />}
              tone="violation"
            />
            <Kpi
              label="Vehicles Detected"
              value={result.vehicles_detected}
              subtext={`${result.helmet_checks_performed} helmet check(s) performed`}
              icon={<ScanSearch size={18} />}
              tone="info"
            />
            <Kpi
              label="Vehicle Number"
              value={0}
              subtext={result.vehicle_number}
              icon={<BadgeCheck size={18} />}
              tone="success"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card title="Image Preprocessing">
              <div className="flex flex-col gap-2 text-sm">
                <PreRow label="Shadow removal (illumination normalization)" active={result.preprocessing.shadow_correction} />
                <PreRow label="Low-light correction (CLAHE)" active={result.preprocessing.low_light_correction} />
                <PreRow label="Rain streak attenuation (directional morphology)" active={result.preprocessing.rain_correction} />
                <PreRow label="Denoise (bilateral filter)" active={result.preprocessing.denoise_applied} />
                <PreRow label="Motion-blur correction (Wiener deconvolution)" active={result.preprocessing.motion_blur_correction} />
                <div className="grid grid-cols-2 gap-1 text-tv-muted text-xs mt-2 pt-2 border-t border-tv-border">
                  <span>Brightness: {result.preprocessing.brightness_score}</span>
                  <span>Sharpness: {result.preprocessing.sharpness_score}</span>
                  <span>Shadow spread: {result.preprocessing.shadow_spread_score}</span>
                  <span>Rain streak density: {result.preprocessing.rain_streak_score}</span>
                </div>
              </div>
            </Card>
            <Card title="Road User Detection" badge={`${result.road_users.total_road_users} Detected`}>
              {Object.keys(result.road_users.counts).length === 0 ? (
                <div className="text-tv-muted text-sm">No vehicles or pedestrians detected.</div>
              ) : (
                <div className="flex flex-col gap-2">
                  {Object.entries(result.road_users.counts).map(([cat, count]) => (
                    <div key={cat} className="flex justify-between text-sm border-b border-tv-border py-1.5 last:border-0">
                      <span className="text-tv-text font-semibold">{cat}</span>
                      <span className="tv-chip tv-chip--blue">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {result.is_compliant ? (
            <Card title="Compliance Result">
              <Chip text="Compliant" variant="green" />
              <div className="mt-3 text-tv-text/85 font-semibold">✅ No violations found in this image.</div>
            </Card>
          ) : (
            <Card title="Digital Evidence Cards" badge={`${result.violations.length} Found`}>
              <div className="flex flex-col gap-3">
                {result.violations.map((v) => (
                  <div key={v.violation_id} className="border border-tv-violation/25 bg-tv-violation/5 rounded-2xl p-4 grid grid-cols-2 gap-3">
                    <div className="col-span-2 flex items-center justify-between">
                      <span className="font-black text-tv-text text-sm">{v.violation_id}</span>
                      <span className="text-tv-muted text-xs">Recorded — see Evidence Center to review</span>
                    </div>
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
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </Layout>
  );
}

function PreRow({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-tv-muted">{label}</span>
      <span className={`tv-chip ${active ? "tv-chip--green" : "tv-chip--blue"}`}>
        {active ? "Applied" : "Not needed"}
      </span>
    </div>
  );
}
