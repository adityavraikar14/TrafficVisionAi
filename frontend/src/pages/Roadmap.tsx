import Layout from "../components/Layout";
import Card from "../components/Card";
import { Chip } from "../components/Chip";

const FEATURES = [
  {
    icon: "🦺",
    title: "Seatbelt Non-Compliance",
    desc: "Requires footage of the windshield-visible cabin from outside the vehicle. Every public dataset we evaluated (5+ sources) is captured from in-cabin, driver-facing cameras for fleet-monitoring use cases — confirmed via direct testing to not transfer to an exterior detection pipeline. A known hard problem in the field (windshield glare/angle/tint), not a gap we can close by trying another off-the-shelf dataset.",
  },
  {
    icon: "🛺",
    title: "Auto-Rickshaw / Indian Vehicle Classes",
    desc: "COCO's standard classes don't include auto-rickshaw, e-rickshaw, or tempo — common on Indian roads. Needs a custom-labeled dataset and a dedicated training cycle.",
  },
  {
    icon: "📊",
    title: "Predictive Violation Analytics",
    desc: "Forecast violation hotspots by time-of-day and location using historical trend data already captured in Analytics.",
  },
];

export default function Roadmap() {
  return (
    <Layout title="🚀 Future Scope" subtitle="Next-generation capabilities for scalable smart-city enforcement">
      <Chip text="Prototype Roadmap" variant="yellow" />
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {FEATURES.map((f) => (
          <Card key={f.title}>
            <div className="w-12 h-12 rounded-2xl bg-tv-primary/15 border border-tv-primary/35 flex items-center justify-center text-2xl">
              {f.icon}
            </div>
            <div className="font-black text-tv-text text-[16px] mt-3.5">{f.title}</div>
            <div className="text-tv-muted text-sm leading-relaxed mt-2.5">{f.desc}</div>
            <div className="mt-4">
              <Chip text="Coming Soon" variant="yellow" />
            </div>
          </Card>
        ))}
      </div>
      <Card title="Deployment Vision">
        <p className="text-tv-text/85 font-semibold leading-relaxed">
          TrafficVision AI is built as a modular enforcement platform: detection models, OCR, evidence
          packaging, analytics, and city operations are independent services that can be extended without
          disrupting the existing backend pipeline.
        </p>
      </Card>
    </Layout>
  );
}
