import { useEffect, useState } from "react";
import { FileDown, FileText, Printer } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { fetchSummary, exportReportUrl, type AnalyticsSummary } from "../api/client";

export default function Reports() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    fetchSummary().then(setData).catch(() => setData(null));
  }, []);

  return (
    <Layout title="🧾 Reports" subtitle="Generate and export enforcement reports for review and audit">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card title="Evidence Export">
          <p className="text-tv-muted text-sm leading-relaxed">
            Export the full evidence ledger as a CSV file — every recorded violation with vehicle number,
            confidence score, status, city, and timestamp. Ready for audit trails or hand-off to enforcement teams.
          </p>
          <a
            href={exportReportUrl}
            className="mt-4 inline-flex items-center gap-2 bg-gradient-to-br from-tv-primary/30 to-tv-primary/10 border border-tv-primary/40 text-white font-bold px-5 py-3 rounded-xl hover:-translate-y-0.5 transition"
          >
            <FileDown size={18} /> Download CSV Report
          </a>
        </Card>

        <Card title="Summary Snapshot">
          {data ? (
            <div className="flex flex-col gap-2.5 text-sm">
              <Row label="Total Violations" value={data.total_violations} />
              <Row label="Helmet Non-Compliance" value={data.helmet_violations} />
              <Row label="Triple Riding Cases" value={data.triple_riding_cases} />
              <Row label="Pending Review" value={data.pending_reviews} />
              <Row label="Verified" value={data.verified} />
              <Row label="Escalated" value={data.escalated} />
              <Row label="Compliance Rate" value={`${data.compliance_rate}%`} />
            </div>
          ) : (
            <div className="text-tv-muted text-sm">Loading…</div>
          )}
        </Card>
      </div>

      <Card title="Reporting Standards">
        <ul className="text-tv-muted text-sm leading-7 list-disc pl-5">
          <li>Every export preserves original detection metadata and confidence scores.</li>
          <li>Officer verification is required before a record can be escalated.</li>
          <li>Reports are generated directly from the live evidence database — never mock data.</li>
        </ul>
        <div className="flex gap-3 mt-4">
          <span className="tv-pill"><FileText size={14} className="inline mr-1" /> Auditable</span>
          <span className="tv-pill"><Printer size={14} className="inline mr-1" /> Print-Ready</span>
        </div>
      </Card>
    </Layout>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
      <span className="text-tv-muted font-semibold">{label}</span>
      <span className="text-white font-black">{value}</span>
    </div>
  );
}
