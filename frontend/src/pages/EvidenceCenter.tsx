import { useEffect, useState } from "react";
import { Search, FolderSearch, Hourglass, BadgeCheck, Target, ShieldX, PlayCircle } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { Chip, StatusChip, formatConfidence } from "../components/Chip";
import ReviewModal from "../components/ReviewModal";
import { fetchEvidence, exportReportUrl, challanUrl, type Violation } from "../api/client";

export default function EvidenceCenter() {
  const [rows, setRows] = useState<Violation[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Violation | null>(null);

  const reload = () => fetchEvidence(query || undefined).then(setRows).catch(() => setRows([]));

  useEffect(() => {
    const handle = setTimeout(reload, 250);
    return () => clearTimeout(handle);
  }, [query]);

  const pending = rows.filter((r) => r.status === "Pending Review").length;
  const verified = rows.filter((r) => r.status === "Verified").length;
  const rejected = rows.filter((r) => r.status === "Rejected").length;
  const avgConf = rows.length ? rows.reduce((s, r) => s + r.confidence, 0) / rows.length : 0;

  return (
    <Layout title="📋 Evidence Center" subtitle="Digital evidence ledger for enforcement, verification, and escalation">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xl font-black text-tv-text">Evidence Review Queue</div>
          <p className="text-tv-muted text-sm mt-1">Searchable command-center ledger for digital violation records.</p>
        </div>
        <a href={exportReportUrl} className="tv-pill hover:border-tv-primary/50">⬇️ Export CSV</a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Kpi label="Evidence Records" value={rows.length} subtext="Total searchable queue" icon={<FolderSearch size={18} />} tone="primary" />
        <Kpi label="Pending Review" value={pending} subtext="Requires officer action" icon={<Hourglass size={18} />} tone="warning" />
        <Kpi label="Verified" value={verified} subtext="Reviewed and confirmed" icon={<BadgeCheck size={18} />} tone="success" />
        <Kpi label="Rejected" value={rejected} subtext="False positives cleared" icon={<ShieldX size={18} />} tone="violation" />
        <Kpi label="Avg Confidence" value={avgConf * 100} decimals={1} suffix="%" subtext="Detection reliability" icon={<Target size={18} />} tone="success" />
      </div>

      <Card>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-tv-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Violation ID, Vehicle Number, Type, City, or Status"
            className="w-full bg-tv-bg-soft/70 border border-tv-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-tv-text outline-none focus:border-tv-primary/55"
          />
        </div>
      </Card>

      <Card title="Evidence Records" badge={`${rows.length} Total`}>
        {rows.length === 0 ? (
          <div className="border border-dashed border-tv-border rounded-2xl py-12 text-center text-tv-muted font-semibold">
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
                  <th className="py-2 pr-4">Challan</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={r.violation_id}
                    onClick={() => setSelected(r)}
                    className="border-b border-tv-border hover:bg-black/3 cursor-pointer"
                  >
                    <td className="py-2.5 pr-4 font-bold text-tv-text">{r.violation_id}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">
                      <div className="flex items-center gap-2">
                        <span>{r.vehicle_number || "—"}</span>
                        {(r.repeat_count ?? 0) >= 2 && <Chip text={`🔁 Repeat ×${r.repeat_count}`} variant="orange" />}
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 text-tv-muted">
                      <div className="flex items-center gap-2">
                        <span>{r.violation_type}</span>
                        {r.evidence_video_path && (
                          <span title="Instant Replay available" className="inline-flex items-center gap-1 text-tv-violation text-[11px] font-bold">
                            <PlayCircle size={13} /> Replay
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 text-tv-muted">{formatConfidence(r.confidence)}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.city}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{new Date(r.created_at).toLocaleString()}</td>
                    <td className="py-2.5 pr-4"><StatusChip status={r.status} /></td>
                    <td className="py-2.5 pr-4">
                      {r.status === "Verified" ? (
                        <a
                          href={challanUrl(r.violation_id)}
                          onClick={(e) => e.stopPropagation()}
                          className="tv-pill hover:border-tv-primary/50 text-[11px]"
                        >
                          📄 Download
                        </a>
                      ) : (
                        <span className="text-tv-muted text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selected && (
        <ReviewModal
          violation={selected}
          onClose={() => setSelected(null)}
          onDone={() => {
            setSelected(null);
            reload();
          }}
        />
      )}
    </Layout>
  );
}
