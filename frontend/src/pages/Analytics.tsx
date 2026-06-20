import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { AlertTriangle, ShieldAlert, TrendingUp, Hourglass } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import Kpi from "../components/Kpi";
import { fetchSummary, type AnalyticsSummary } from "../api/client";
import { CHART_COLORS, TOOLTIP_STYLE, AXIS_STYLE } from "../components/charts";

const TYPE_COLORS = [CHART_COLORS.violation, CHART_COLORS.warning, "#f59e0b", CHART_COLORS.info, CHART_COLORS.muted];

export default function Analytics() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    fetchSummary().then(setData).catch(() => setData(null));
  }, []);

  if (!data) {
    return (
      <Layout title="📊 Analytics & Insights" subtitle="City-level violation intelligence">
        <Card>Loading analytics…</Card>
      </Layout>
    );
  }

  const pieData = Object.entries(data.by_type).map(([name, value]) => ({ name, value }));
  const barData = pieData;
  const growth = data.trend.length >= 2 && data.trend[0].violations > 0
    ? (((data.trend[data.trend.length - 1].violations - data.trend[0].violations) / data.trend[0].violations) * 100)
    : 0;

  return (
    <Layout title="📊 Analytics & Insights" subtitle="City-level violation intelligence and enforcement prioritization">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Total Violations" value={data.total_violations} subtext="All categories" icon={<AlertTriangle size={18} />} tone="violation" />
        <Kpi label="Helmet Cases" value={data.helmet_violations} subtext="Largest category" icon={<ShieldAlert size={18} />} tone="violation" />
        <Kpi label="Growth Trend" value={growth} decimals={1} suffix="%" subtext="Last 7 days" icon={<TrendingUp size={18} />} tone="success" />
        <Kpi label="Review Load" value={data.pending_reviews} subtext="Pending evidence" icon={<Hourglass size={18} />} tone="warning" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card title="Violation Distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
                {pieData.map((_, i) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} stroke="#ffffff" strokeWidth={2} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Category Insights">
          <div className="flex flex-col gap-2.5">
            {pieData.map((p) => (
              <div key={p.name} className="flex justify-between items-center border-b border-tv-border py-2.5 last:border-0">
                <div>
                  <div className="font-extrabold text-tv-text text-sm">{p.name}</div>
                  <div className="text-tv-muted text-xs mt-0.5">Share of total enforcement load</div>
                </div>
                <span className="tv-chip tv-chip--yellow">{p.value} Cases</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card title="Traffic Violation Overview">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData}>
              <CartesianGrid stroke="rgba(15,23,42,0.08)" />
              <XAxis dataKey="name" tick={AXIS_STYLE} angle={-12} textAnchor="end" height={60} />
              <YAxis tick={AXIS_STYLE} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {barData.map((_, i) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Violation Trend Over Time">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.trend}>
              <CartesianGrid stroke="rgba(15,23,42,0.08)" />
              <XAxis dataKey="date" tick={AXIS_STYLE} />
              <YAxis tick={AXIS_STYLE} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Line type="monotone" dataKey="violations" stroke={CHART_COLORS.primary} strokeWidth={3} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </Layout>
  );
}
