interface Props {
  title: string;
  subtitle: string;
}

export default function Header({ title, subtitle }: Props) {
  return (
    <div className="sticky top-0 z-30 -mx-6 -mt-6 px-6 pt-6 pb-4 backdrop-blur-xl bg-tv-bg/85 border-b border-tv-border">
      <div className="tv-card flex items-center justify-between gap-4 px-5 py-4 flex-wrap">
        <div className="flex items-center gap-4 min-w-[260px]">
          <div className="w-11 h-11 rounded-2xl bg-[radial-gradient(circle_at_30%_20%,rgba(251,191,36,0.36),rgba(251,191,36,0.08))] border border-tv-primary/35 flex items-center justify-center text-xl shrink-0">
            🚦
          </div>
          <div>
            <span className="tv-pill">From Detection to Digital Evidence</span>
            <div className="mt-1.5 text-[28px] font-black tracking-tight text-white">{title}</div>
            <div className="text-tv-muted text-sm font-semibold mt-0.5">{subtitle}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span className="tv-pill border-tv-success/35">
            <span className="w-2 h-2 rounded-full bg-tv-success tv-status-pulse" />
            System Online
          </span>
          <span className="tv-pill">AI-Powered Smart Traffic Enforcement Platform</span>
        </div>
      </div>
    </div>
  );
}
