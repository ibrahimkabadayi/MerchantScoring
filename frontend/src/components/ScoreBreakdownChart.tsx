import type { ScoreBreakdown } from "../types";

interface ScoreBreakdownChartProps {
  breakdown: ScoreBreakdown;
}

const LABELS: { key: keyof ScoreBreakdown; label: string; color: string }[] = [
  { key: "digital_readiness", label: "Digital Readiness", color: "#6366f1" },
  { key: "growth_momentum", label: "Growth Momentum", color: "#10b981" },
  { key: "reachability", label: "Reachability", color: "#f59e0b" },
  { key: "sector_fit", label: "Sector Fit", color: "#ec4899" },
];

export default function ScoreBreakdownChart({
  breakdown,
}: ScoreBreakdownChartProps) {
  return (
    <div className="space-y-3">
      {LABELS.map(({ key, label, color }) => {
        const value = breakdown[key];
        return (
          <div key={key}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-medium">{label}</span>
              <span className="font-bold" style={{ color }}>
                {value.toFixed(0)}
              </span>
            </div>
            <div className="h-2 bg-[var(--color-surface)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full score-bar-fill"
                style={{
                  width: `${value}%`,
                  backgroundColor: color,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
