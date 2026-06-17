import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ScanSearch,
  FolderSearch,
  BarChart3,
  Map,
  FileText,
  Rocket,
  Info,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Executive Dashboard", icon: LayoutDashboard },
  { to: "/analyze", label: "Live Detection", icon: ScanSearch },
  { to: "/evidence", label: "Evidence Center", icon: FolderSearch },
  { to: "/analytics", label: "Analytics & Insights", icon: BarChart3 },
  { to: "/map", label: "Smart City Map", icon: Map },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/roadmap", label: "Future Scope", icon: Rocket },
  { to: "/about", label: "About", icon: Info },
];

export default function Sidebar() {
  return (
    <aside className="w-[260px] shrink-0 h-screen sticky top-0 bg-tv-sidebar border-r border-tv-border flex flex-col">
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="w-10 h-10 rounded-2xl bg-tv-primary/15 border border-tv-primary/35 flex items-center justify-center text-xl">
          🚦
        </div>
        <div>
          <div className="font-black text-[15px] text-white leading-tight">TrafficVision AI</div>
          <div className="text-[11px] text-tv-muted leading-tight mt-0.5">Smart-city enforcement console</div>
        </div>
      </div>
      <div className="tv-divider mx-4" />
      <nav className="flex-1 overflow-y-auto px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => `tv-nav-item ${isActive ? "active" : ""}`}
          >
            <Icon size={16} strokeWidth={2.4} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4">
        <div className="tv-card px-3 py-3">
          <div className="text-[12px] font-bold text-white">System Status</div>
          <div className="mt-2 flex items-center gap-2 text-[11px] font-semibold text-tv-muted">
            <span className="w-2 h-2 rounded-full bg-tv-success tv-status-pulse" />
            Backend Online
          </div>
        </div>
      </div>
    </aside>
  );
}
