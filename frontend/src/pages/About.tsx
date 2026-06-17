import Layout from "../components/Layout";
import Card from "../components/Card";
import { Chip } from "../components/Chip";

const SECTIONS = [
  { title: "Problem Statement", body: "Manual traffic enforcement is slow, inconsistent, and difficult to audit. Smart-city deployments need automated detection, reliable evidence capture, and review workflows that traffic police can trust." },
  { title: "TrafficVision AI Solution", body: "TrafficVision AI converts camera images into digital evidence: YOLOv8 detects helmet non-compliance and triple riding, EasyOCR extracts vehicle identifiers, and a FastAPI + React command center presents review-ready enforcement records backed by a real database." },
  { title: "Architecture", body: "Camera input → YOLO helmet + general detection → rule-based triple-riding logic → OCR vehicle extraction → SQLite evidence persistence → REST API → React command-center dashboards." },
  { title: "Technology Stack", body: "Frontend: React + Vite + TailwindCSS + Recharts + Leaflet • Backend: FastAPI + SQLite • Detection: Ultralytics YOLOv8 • OCR: EasyOCR • Training: Google Colab (GPU)." },
  { title: "Performance Evaluation", body: "Model performance is evaluated using Ultralytics' built-in validation: mAP50, mAP50-95, Precision, Recall, and F1-score on a held-out validation split." },
  { title: "Future Vision", body: "Extend from helmet + triple-riding compliance to the full violation set (seatbelt, wrong-side, red-light, stop-line, illegal parking), automated challan workflows, and predictive enforcement planning." },
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
              <p className="text-white/85 font-semibold leading-relaxed">{s.body}</p>
            </Card>
          ))}
        </div>
        <div className="flex flex-col gap-4">
          <Card title="Technology Stack">
            <div className="flex flex-col gap-2.5">
              {STACK.map(([label, desc]) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
                  <div>
                    <div className="font-extrabold text-white text-sm">{label}</div>
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
