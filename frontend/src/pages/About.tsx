import Layout from "../components/Layout";
import Card from "../components/Card";
import { Chip } from "../components/Chip";

const SECTIONS = [
  { title: "Problem Statement", body: "Manual traffic enforcement is slow, inconsistent, and difficult to audit. Smart-city deployments need automated detection, reliable evidence capture, and review workflows that traffic police can trust." },
  { title: "TrafficVision AI Solution", body: "TrafficVision AI converts camera images and video into digital evidence: real detection across helmet compliance, triple riding, stop-line/red-light violations, illegal parking, and wrong-side driving, plus a trained license plate detector and OCR — all backed by a real database, not mock data." },
  { title: "Architecture", body: "Camera input → adaptive preprocessing → YOLO helmet + general detection → pose-verified triple-riding / zone-calibrated stop-line·red-light·parking rules → CV-based plate localization + OCR → SQLite evidence persistence → REST API → React command-center dashboards. Wrong-side driving is the one violation routed through a separate video + multi-frame tracking pipeline, since direction of travel isn't recoverable from a single frame." },
  { title: "Technology Stack", body: "Frontend: React + Vite + TailwindCSS + Recharts + Leaflet • Backend: FastAPI + SQLite • Detection: Ultralytics YOLOv8 • OCR: EasyOCR • Training: Google Colab (GPU)." },
  { title: "Performance Evaluation", body: "Model performance is evaluated using Ultralytics' built-in validation: mAP50, mAP50-95, Precision, Recall, and F1-score on a held-out validation split, plus measured inference latency — for every active model (helmet, general detector, pose, plate detector), not just one." },
  { title: "Future Vision", body: "Seatbelt non-compliance and auto-rickshaw/Indian-vehicle classes remain open — see Future Scope for why, including a known camera-angle limitation we found through direct testing rather than assumption. Beyond that: repeat-offender tracking, predictive hotspot analytics, and automated challan workflows." },
];

const STACK = [
  ["React + Vite", "Premium command-center UI"],
  ["TailwindCSS", "Dark theme, glassmorphism design system"],
  ["FastAPI", "Real-time detection + evidence API"],
  ["YOLOv8", "Helmet + vehicle/person detection"],
  ["EasyOCR", "Vehicle plate extraction"],
  ["SQLite", "Evidence persistence"],
  ["Recharts + Leaflet", "Analytics and India risk map"],
];

export default function About() {
  return (
    <Layout title="ℹ️ About" subtitle="TrafficVision AI — From Detection to Digital Evidence">
      <div className="grid grid-cols-1 xl:grid-cols-[1.7fr_1fr] gap-5">
        <div className="flex flex-col gap-4">
          {SECTIONS.map((s) => (
            <Card key={s.title} title={s.title}>
              <p className="text-tv-text/85 font-semibold leading-relaxed">{s.body}</p>
            </Card>
          ))}
        </div>
        <div className="flex flex-col gap-4">
          <Card title="Technology Stack">
            <div className="flex flex-col gap-2.5">
              {STACK.map(([label, desc]) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-tv-border last:border-0">
                  <div>
                    <div className="font-extrabold text-tv-text text-sm">{label}</div>
                    <div className="text-tv-muted text-xs mt-0.5">{desc}</div>
                  </div>
                  <span className="tv-chip tv-chip--blue">Active</span>
                </div>
              ))}
            </div>
          </Card>
          <Chip text="Built for Smart Cities" variant="yellow" />
        </div>
      </div>
    </Layout>
  );
}
