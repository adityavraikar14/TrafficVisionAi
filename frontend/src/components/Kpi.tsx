import type { ReactNode } from "react";
import CountUp from "./CountUp";

const ACCENTS: Record<string, string> = {
  primary: "var(--color-tv-primary)",
  success: "var(--color-tv-success)",
  violation: "var(--color-tv-violation)",
  warning: "var(--color-tv-warning)",
  info: "var(--color-tv-info)",
};

interface Props {
  label: string;
  value: number;
  decimals?: number;
  suffix?: string;
  subtext: string;
  icon: ReactNode;
  tone?: keyof typeof ACCENTS;
}

export default function Kpi({ label, value, decimals = 0, suffix = "", subtext, icon, tone = "primary" }: Props) {
  const accent = ACCENTS[tone];
  return (
    <div className="tv-kpi p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-extrabold uppercase tracking-wider text-tv-muted">{label}</div>
          <div className="mt-2 text-[30px] font-black tracking-tight text-white">
            <CountUp value={value} decimals={decimals} suffix={suffix} />
          </div>
        </div>
        <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-lg shrink-0">
          {icon}
        </div>
      </div>
      <div className="mt-2 text-[13px] font-semibold text-tv-muted flex items-center gap-1.5">
        <span style={{ color: accent }} className="text-base leading-none">●</span>
        {subtext}
      </div>
    </div>
  );
}
