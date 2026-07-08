import type { Merchant } from "../types";
import { CATEGORY_LABELS, TIER_COLORS, type Tier } from "../types";

interface LeadListProps {
  merchants: Merchant[];
  selectedId: string | null;
  onSelect: (merchant: Merchant) => void;
  loading: boolean;
  total: number;
}

function TierBadge({ tier }: { tier: string }) {
  const color = TIER_COLORS[tier as Tier] ?? "#6b7280";
  return (
    <span
      className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
      style={{ backgroundColor: `${color}20`, color }}
    >
      {tier}
    </span>
  );
}

function ScoreRing({ score }: { score: number }) {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 70 ? "var(--color-tier-high)" : score >= 45 ? "var(--color-tier-medium)" : "var(--color-tier-low)";

  return (
    <div className="relative w-12 h-12 flex-shrink-0">
      <svg width="48" height="48" className="-rotate-90">
        <circle cx="24" cy="24" r={radius} fill="none" stroke="var(--color-surface-lighter)" strokeWidth="3" />
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-xs font-bold"
        style={{ color }}
      >
        {score.toFixed(0)}
      </span>
    </div>
  );
}

export default function LeadList({
  merchants,
  selectedId,
  onSelect,
  loading,
  total,
}: LeadListProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="glass-card p-3 animate-pulse">
            <div className="flex gap-3">
              <div className="w-12 h-12 rounded-full bg-[var(--color-surface-lighter)]" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-[var(--color-surface-lighter)] rounded w-3/4" />
                <div className="h-3 bg-[var(--color-surface-lighter)] rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="text-xs text-slate-400 mb-2 px-1">
        Showing {merchants.length} of {total} leads
      </div>
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
        {merchants.map((m) => (
          <button
            key={m.place_id}
            id={`lead-${m.place_id}`}
            onClick={() => onSelect(m)}
            className={`w-full text-left glass-card p-3 transition-all duration-200 hover:border-[var(--color-accent)] cursor-pointer ${
              selectedId === m.place_id
                ? "border-[var(--color-accent)] bg-[rgba(99,102,241,0.1)]"
                : ""
            }`}
          >
            <div className="flex items-center gap-3">
              <ScoreRing score={m.moka_fit_score ?? 0} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <h3 className="text-sm font-semibold text-white truncate">
                    {m.name}
                  </h3>
                  <TierBadge tier={m.priority_tier ?? "LOW"} />
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span>{CATEGORY_LABELS[m.category] ?? m.category}</span>
                  <span>·</span>
                  <span>{m.district}</span>
                  {m.rating && (
                    <>
                      <span>·</span>
                      <span>⭐ {m.rating}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </button>
        ))}
        {merchants.length === 0 && (
          <div className="text-center text-slate-500 py-8">
            No merchants match your filters.
          </div>
        )}
      </div>
    </div>
  );
}
