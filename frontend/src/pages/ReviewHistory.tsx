import { useEffect, useState } from "react";
import { Search, History as HistoryIcon } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { Chip } from "../components/Chip";
import { fetchReviewHistory, type ReviewHistoryEntry } from "../api/client";

export default function ReviewHistory() {
  const [rows, setRows] = useState<ReviewHistoryEntry[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => {
      fetchReviewHistory(query || undefined).then(setRows).catch(() => setRows([]));
    }, 250);
    return () => clearTimeout(handle);
  }, [query]);

  const verifiedCount = rows.filter((r) => r.decision === "Verified").length;
  const rejectedCount = rows.filter((r) => r.decision === "Rejected").length;

  return (
    <Layout title="🕘 Review History" subtitle="Audit trail of every officer decision — who reviewed what, and when">
      <div>
        <div className="text-xl font-black text-tv-text">Officer Decision Log</div>
        <p className="text-tv-muted text-sm mt-1">
          Every Verify/Reject action is recorded here with the reviewing officer's name and badge ID,
          so any future escalation can be traced back to exactly who approved or rejected a record.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Kpi label="Total Reviews" value={rows.length} subtext="All recorded decisions" icon={<HistoryIcon size={18} />} tone="primary" />
        <Kpi label="Verified" value={verifiedCount} subtext="Confirmed violations" icon={<HistoryIcon size={18} />} tone="success" />
        <Kpi label="Rejected" value={rejectedCount} subtext="False positives cleared" icon={<HistoryIcon size={18} />} tone="violation" />
      </div>

      <Card>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-tv-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Violation ID, Officer Name, or Badge ID"
            className="w-full bg-tv-bg-soft/70 border border-tv-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-tv-text outline-none focus:border-tv-primary/55"
          />
        </div>
      </Card>

      <Card title="Review Records" badge={`${rows.length} Total`}>
        {rows.length === 0 ? (
          <div className="border border-dashed border-tv-border rounded-2xl py-12 text-center text-tv-muted font-semibold">
            No review history yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-tv-muted text-[11px] uppercase tracking-wide border-b border-tv-border">
                  <th className="py-2 pr-4">Violation ID</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Decision</th>
                  <th className="py-2 pr-4">Officer Name</th>
                  <th className="py-2 pr-4">Badge ID</th>
                  <th className="py-2 pr-4">Notes</th>
                  <th className="py-2 pr-4">Reviewed At</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-b border-tv-border">
                    <td className="py-2.5 pr-4 font-bold text-tv-text">{r.violation_id}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.violation_type}</td>
                    <td className="py-2.5 pr-4">
                      <Chip text={r.decision} variant={r.decision === "Verified" ? "green" : "gray"} />
                    </td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.officer_name}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.officer_badge_id}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{r.notes || "—"}</td>
                    <td className="py-2.5 pr-4 text-tv-muted">{new Date(r.reviewed_at).toLocaleString()}</td>
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
