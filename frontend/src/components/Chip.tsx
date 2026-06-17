type Variant = "red" | "green" | "yellow" | "orange" | "blue";

export function Chip({ text, variant }: { text: string; variant: Variant }) {
  return <span className={`tv-chip tv-chip--${variant}`}>{text}</span>;
}

export function StatusChip({ status }: { status: string }) {
  const s = status.toLowerCase();
  let variant: Variant = "blue";
  if (s.includes("pending")) variant = "red";
  else if (s.includes("verified") || s.includes("reviewed")) variant = "green";
  else if (s.includes("escalated")) variant = "orange";
  return <Chip text={`● ${status}`} variant={variant} />;
}

export function formatConfidence(conf: number): string {
  return `${(conf * 100).toFixed(2)}%`;
}
