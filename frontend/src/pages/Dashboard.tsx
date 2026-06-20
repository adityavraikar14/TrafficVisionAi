import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { AlertTriangle, Car, ShieldCheck, ClipboardList, Camera, FileCheck2, ShieldX } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { Chip, StatusChip, formatConfidence } from "../components/Chip";
import { fetchSummary, type AnalyticsSummary } from "../api/client";
import { CHART_COLORS, TOOLTIP_STYLE, AXIS_STYLE } from "../components/charts";

const TYPE_COLORS = [
  CHART_COLORS.violation,
  CHART_COLORS.warning,
  "#f59e0b",
  CHART_COLORS.info,
  CHART_COLORS.muted,
];

export default function Dashboard() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    fetchSummary().then(setData).catch(() => setData(null));
  }, []);

  if (!data) {
    return (
      <Layout title="🚦 TrafficVision AI" subtitle="From Detection to Digital Evidence">
        <Card>Loading live enforcement data…</Card>
      </Layout>
    );
  }

  const pieData = Object.entries(data.by_type).map(([name, value]) => ({ name, value }));
  const topCities = data.city_breakdown.slice(0, 4);
  const maxCity = topCities[0]?.total || 1;

  return (
    <Layout title="🚦 TrafficVision AI" subtitle="From Detection to Digital Evidence">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xl font-black text-tv-text">Executive Dashboard</div>
          <p className="text-tv-muted text-sm mt-1">Real-time traffic enforcement posture across the smart-city operating grid.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="tv-pill">Live Backend Data</span>
          <span className="tv-pill">Auto-Refreshed</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-7 gap-4">
        <Kpi label="Total Violations" value={data.total_violations} subtext="All recorded cases" icon={<AlertTriangle size={18} />} tone="violation" />
        <Kpi label="Helmet Violations" value={data.helmet_violations} subtext="Non-compliance count" icon={<ShieldCheck size={18} />} tone="warning" />
        <Kpi label="Triple Riding" value={data.triple_riding_cases} subtext="Rule-based detection" icon={<Car size={18} />} tone="info" />
        <Kpi label="Compliance Rate" value={data.compliance_rate} decimals={1} suffix="%" subtext="Helmet adherence" icon={<FileCheck2 size={18} />} tone="success" />
        <Kpi label="Pending Reviews" value={data.pending_reviews} subtext="Evidence queue" icon={<ClipboardList size={18} />} tone="warning" />
        <Kpi label="Rejected" value={data.rejected} subtext="Officer-cleared false positives" icon={<ShieldX size={18} />} tone="violation" />
        <Kpi label="Avg Confidence" value={data.average_confidence * 100} decimals={1} suffix="%" subtext="Detection reliability" icon={<Camera size={18} />} tone="primary" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.25fr_0.75fr] gap-5">
        <Card title="Violation Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2}>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} stroke="#ffffff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 12, fontWeight: 600, color: "#334155" }} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="City Risk Pulse">
          {topCities.length === 0 ? (
            <div className="text-tv-muted text-sm">No city data yet.</div>
          ) : (
            <>
              <div className="text-center pb-2">
                <div className="text-[12px] font-extrabold text-tv-muted tracking-wide">
                  HIGHEST RISK CITY · {new Date().toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                </div>
                <div className="text-[28px] font-black text-tv-text mt-2">
                  {topCities[0].city} – {topCities[0].total} Violations
                </div>
                {topCities[0].last_violation_at && (
                  <div className="text-tv-muted text-xs mt-1">
                    Last violation: {new Date(topCities[0].last_violation_at).toLocaleString()}
                  </div>
                )}
              </div>
              <div className="tv-divider" />
              {topCities.map((c) => (
                <div key={c.city} className="mt-3.5">
                  <div className="flex justify-between text-[13px] font-extrabold text-tv-text">
                    <span>{c.city}</span>
                    <span>{c.total}</span>
                  </div>
                  <div className="h-2 bg-black/6 rounded-full overflow-hidden mt-1.5">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(c.total / maxCity) * 100}%`,
                        background: `linear-gradient(90deg, ${CHART_COLORS.violation}, rgba(220,38,38,0.35))`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </>
          )}
        </Card>
      </div>

      <Card title="Violation Trend Over Time">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data.trend}>
            <CartesianGrid stroke="rgba(15,23,42,0.08)" />
            <XAxis dataKey="date" tick={AXIS_STYLE} />
            <YAxis tick={AXIS_STYLE} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 12, fontWeight: 600, color: "#334155" }} />
            <Line type="monotone" dataKey="violations" stroke={CHART_COLORS.violation} strokeWidth={3} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="reviewed" stroke={CHART_COLORS.success} strokeWidth={3} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Recent Enforcement Activity">
        <div className="flex flex-col gap-2.5">
          {data.recent.length === 0 && <div className="text-tv-muted text-sm">No violations recorded yet — run an analysis on the Live Detection page.</div>}
          {data.recent.map((v) => (
            <div key={v.violation_id} className="tv-card p-3.5 flex justify-between gap-3 flex-wrap">
              <div className="min-w-[220px]">
                <div className="font-black text-tv-text text-[15px]">{v.violation_id}</div>
                <div className="text-tv-muted text-[13px] font-semibold mt-1">Vehicle: {v.vehicle_number || "Unknown"}</div>
                <div className="text-tv-muted text-[12px] mt-0.5">{v.violation_type}</div>
              </div>
              <div className="flex items-center gap-2 flex-wrap justify-end">
                <Chip text={formatConfidence(v.confidence)} variant="yellow" />
                <StatusChip status={v.status} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </Layout>
  );
}
