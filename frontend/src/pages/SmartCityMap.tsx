import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { fetchSummary, type AnalyticsSummary, type CityBreakdown } from "../api/client";
import { CHART_COLORS } from "../components/charts";

function riskColor(total: number, max: number) {
  const ratio = max ? total / max : 0;
  if (ratio > 0.75) return CHART_COLORS.violation;
  if (ratio > 0.5) return CHART_COLORS.warning;
  if (ratio > 0.25) return CHART_COLORS.info;
  return CHART_COLORS.success;
}

export default function SmartCityMap() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    fetchSummary().then(setData).catch(() => setData(null));
  }, []);

  const cities: CityBreakdown[] = (data?.city_breakdown || []).filter((c) => c.lat && c.lon);
  const maxTotal = Math.max(1, ...cities.map((c) => c.total));

  return (
    <Layout title="🗺 Smart City Map" subtitle="India-wide city risk visualization for traffic enforcement prioritization">
      <div className="grid grid-cols-1 xl:grid-cols-[1.6fr_1fr] gap-5">
        <Card title="India Violation Heatmap" className="p-2">
          <MapContainer center={[22.9734, 78.6569]} zoom={5} style={{ height: 560, width: "100%", borderRadius: 16 }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap &copy; CARTO'
            />
            {cities.map((c) => (
              <CircleMarker
                key={c.city}
                center={[c.lat as number, c.lon as number]}
                radius={8 + (c.total / maxTotal) * 22}
                pathOptions={{
                  color: riskColor(c.total, maxTotal),
                  fillColor: riskColor(c.total, maxTotal),
                  fillOpacity: 0.55,
                  weight: 2,
                }}
              >
                <Popup>
                  <b>{c.city}</b><br />
                  Total Violations: {c.total}<br />
                  Helmet: {c.helmet} • Triple Riding: {c.triple_riding} • Parking: {c.illegal_parking}
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </Card>

        <div className="flex flex-col gap-5">
          <Card title="Highest Risk City">
            {cities.length === 0 ? (
              <div className="text-tv-muted text-sm">No city data yet.</div>
            ) : (
              <>
                <div className="text-center">
                  <div className="text-[12px] font-extrabold text-tv-muted tracking-wide">HIGHEST RISK CITY</div>
                  <div className="text-[26px] font-black text-white mt-2">{cities[0].city} – {cities[0].total} Violations</div>
                  <div className="text-tv-muted text-sm mt-1.5">
                    Helmet: {cities[0].helmet} • Triple Riding: {cities[0].triple_riding} • Parking: {cities[0].illegal_parking}
                  </div>
                </div>
                <div className="tv-divider" />
                {cities.map((c) => (
                  <div key={c.city} className="mt-3">
                    <div className="flex justify-between text-[13px] font-extrabold text-white">
                      <span>{c.city}</span><span>{c.total}</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden mt-1.5">
                      <div className="h-full rounded-full" style={{ width: `${(c.total / maxTotal) * 100}%`, background: riskColor(c.total, maxTotal) }} />
                    </div>
                  </div>
                ))}
              </>
            )}
          </Card>

          <Card title="Risk Legend">
            {[
              { label: "Critical", color: CHART_COLORS.violation, desc: "75%+ of peak load" },
              { label: "High", color: CHART_COLORS.warning, desc: "50–75% of peak load" },
              { label: "Elevated", color: CHART_COLORS.info, desc: "25–50% of peak load" },
              { label: "Moderate", color: CHART_COLORS.success, desc: "Below 25% of peak load" },
            ].map((l) => (
              <div key={l.label} className="flex justify-between items-center py-2.5 border-b border-white/5 last:border-0">
                <div>
                  <div className="font-extrabold text-white text-sm">{l.label}</div>
                  <div className="text-tv-muted text-xs mt-0.5">{l.desc}</div>
                </div>
                <span className="w-3 h-3 rounded-full" style={{ background: l.color, boxShadow: `0 0 12px ${l.color}` }} />
              </div>
            ))}
          </Card>
        </div>
      </div>

      <Card title="City-Wise Violation Summary">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-tv-muted text-[11px] uppercase tracking-wide border-b border-tv-border">
                <th className="py-2 pr-4">City</th>
                <th className="py-2 pr-4">Total</th>
                <th className="py-2 pr-4">Helmet</th>
                <th className="py-2 pr-4">Triple Riding</th>
                <th className="py-2 pr-4">Illegal Parking</th>
              </tr>
            </thead>
            <tbody>
              {cities.map((c) => (
                <tr key={c.city} className="border-b border-white/5">
                  <td className="py-2.5 pr-4 font-bold text-white">{c.city}</td>
                  <td className="py-2.5 pr-4 text-tv-muted">{c.total}</td>
                  <td className="py-2.5 pr-4 text-tv-muted">{c.helmet}</td>
                  <td className="py-2.5 pr-4 text-tv-muted">{c.triple_riding}</td>
                  <td className="py-2.5 pr-4 text-tv-muted">{c.illegal_parking}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Layout>
  );
}
