import { useEffect, useState } from "react";
import { Search, FolderSearch, Hourglass, BadgeCheck, Target } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { StatusChip, formatConfidence } from "../components/Chip";
import { fetchEvidence, exportReportUrl, type Violation } from "../api/client";

export default function EvidenceCenter() {
  const [rows, setRows] = useState<Violation[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => {
      fetchEvidence(query || undefined).then(setRows).catch(() => setRows([]));
    }, 250);
    return () => clearTimeout(handle);
  }, [query]);

  const pending = rows.filter((r) => r.status === "Pending Review").length;
  const verified = rows.filter((r) => r.status === "Verified").length;
  const avgConf = rows.length ? rows.reduce((s, r) => s + r.confidence, 0) / rows.length : 0;

  return (
    <Layout title="📋 Evidence Center" subtitle="Digital evidence ledger for enforcement, verification, and escalation">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xl font-black text-white">Evidence Review Queue</div>
          <p className="text-tv-muted text-sm mt-1">Searchable command-center ledger for digital violation records.</p>
        </div>
        <a href={exportReportUrl} className="tv-pill hover:border-tv-primary/50">⬇️ Export CSV</a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Evidence Records" value={rows.length} subtext="Total searchable queue" icon={<FolderSearch size={18} />} tone="violation" />
        <Kpi label="Pending Review" value={pending} subtext="Requires officer action" icon={<Hourglass size={18} />} tone="warning" />
        <Kpi label="Verified" value={verified} subtext="Reviewed and confirmed" icon={<BadgeCheck size={18} />} tone="success" />
        <Kpi label="Avg Confidence" value={avgConf * 100} decimals={1} suffix="%" subtext="Detection reliability" icon={<Target size={18} />} tone="success" />
      </div>

      <Card>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-tv-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Violation ID, Vehicle Number, Type, City, or Status"
            className="w-full bg-tv-bg-soft/70 border border-tv-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-white outline-none focus:border-tv-primary/55"
          />
        </div>
      </Card>

      <Card title="Evidence Records" badge={`${rows.length} Total`}>
        {rows.length === 0 ? (
          <div className="border border-dashed border-white/15 rounded-2xl py-12 text-center text-tv-muted font-semibold">
            No matching evidence records found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-tv-muted text-[11px] uppercase tracking-wide border-b border-tv-border">
                  <th className="py-2 pr-4">Violation ID</th>
                  <th className="py-2 pr-4">Vehicle</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Confidence</th>
                  <th className="py-2 pr-4">City</th>
                  <th className="py-2 pr-4">Timestamp</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.violation_id} className="border-b border-white/5 hover:bg-white/3">
                    <td className="py-2.5 pr-4 font-bold text-white">{r.violation_id}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.vehicle_number || "—"}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.violation_type}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{formatConfidence(r.confidence)}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.city}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{new Date(r.created_at).toLocaleString()}</td>
                    <td className="py-2.5 pr-4"><StatusChip status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </Layout>
  );
}
