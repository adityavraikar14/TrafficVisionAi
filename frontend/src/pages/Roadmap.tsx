import Layout from "../components/Layout";
import Card from "../components/Card";
import { Chip } from "../components/Chip";

const FEATURES = [
  { icon: "🦺", title: "Seatbelt Non-Compliance", desc: "Per-class detection requiring a dedicated annotated dataset and training cycle." },
  { icon: "↩️", title: "Wrong-Side Driving", desc: "Needs vehicle tracking (ByteTrack/DeepSORT) plus lane-direction calibration per camera." },
  { icon: "🚦", title: "Red-Light Violation", desc: "Needs stop-line calibration and signal-state input synced with vehicle crossing detection." },
  { icon: "🛑", title: "Stop-Line Violation", desc: "Shares the stop-line calibration groundwork with red-light detection." },
  { icon: "🅿️", title: "Illegal Parking (Video)", desc: "Stationary-vehicle dwell-time heuristic on video streams inside a marked restricted zone." },
  { icon: "🔁", title: "Repeat Offender Tracking", desc: "Cross-reference plate numbers across violations to flag repeat offenders automatically." },
  { icon: "📊", title: "Predictive Violation Analytics", desc: "Forecast violation hotspots by time-of-day and location using historical trend data." },
  { icon: "📄", title: "E-Challan Integration", desc: "Connect verified evidence packages directly to digital challan issuance workflows." },
];

export default function Roadmap() {
  return (
    <Layout title="🚀 Future Scope" subtitle="Next-generation capabilities for scalable smart-city enforcement">
      <Chip text="Prototype Roadmap" variant="yellow" />
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {FEATURES.map((f) => (
          <Card key={f.title}>
            <div className="w-12 h-12 rounded-2xl bg-tv-primary/15 border border-tv-primary/35 flex items-center justify-center text-2xl">
              {f.icon}
            </div>
            <div className="font-black text-white text-[16px] mt-3.5">{f.title}</div>
            <div className="text-tv-muted text-sm leading-relaxed mt-2.5">{f.desc}</div>
            <div className="mt-4">
              <Chip text="Coming Soon" variant="yellow" />
            </div>
          </Card>
        ))}
      </div>
      <Card title="Deployment Vision">
        <p className="text-white/85 font-semibold leading-relaxed">
          TrafficVision AI is built as a modular enforcement platform: detection models, OCR, evidence
          packaging, analytics, and city operations are independent services that can be extended without
          disrupting the existing backend pipeline.
        </p>
      </Card>
    </Layout>
  );
}
