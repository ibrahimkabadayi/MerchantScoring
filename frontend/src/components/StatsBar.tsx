import type { StatsResponse } from "../types";

interface StatsBarProps {
  stats: StatsResponse | null;
  loading: boolean;
}

export default function StatsBar({ stats, loading }: StatsBarProps) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card p-4 animate-pulse">
            <div className="h-4 bg-[var(--color-surface-lighter)] rounded w-20 mb-2" />
            <div className="h-8 bg-[var(--color-surface-lighter)] rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: "Total Leads",
      value: stats.total_merchants,
      color: "text-white",
      icon: "📊",
    },
    {
      label: "High Priority",
      value: stats.high_count,
      color: "text-[var(--color-tier-high)]",
      icon: "🟢",
    },
    {
      label: "Medium Priority",
      value: stats.medium_count,
      color: "text-[var(--color-tier-medium)]",
      icon: "🟡",
    },
    {
      label: "Avg Score",
      value: stats.avg_score.toFixed(1),
      color: "text-[var(--color-accent-light)]",
      icon: "⚡",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="glass-card p-4 hover:border-[var(--color-accent)] transition-colors duration-200"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{card.icon}</span>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">
              {card.label}
            </span>
          </div>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
