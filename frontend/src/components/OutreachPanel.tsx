import { useState } from "react";
import type { Merchant, OutreachResponse } from "../types";
import { CATEGORY_LABELS, TIER_COLORS, type Tier } from "../types";
import { generateOutreach } from "../api/client";
import ScoreBreakdownChart from "./ScoreBreakdownChart";

interface OutreachPanelProps {
  merchant: Merchant | null;
  onClose: () => void;
}

export default function OutreachPanel({ merchant, onClose }: OutreachPanelProps) {
  const [outreach, setOutreach] = useState<OutreachResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!merchant) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        <div className="text-center">
          <p className="text-4xl mb-3">🎯</p>
          <p className="text-sm">Select a merchant from the list or map</p>
          <p className="text-xs mt-1 text-slate-600">
            to view details and generate outreach
          </p>
        </div>
      </div>
    );
  }

  const tier = (merchant.priority_tier ?? "LOW") as Tier;
  const tierColor = TIER_COLORS[tier];
  const score = merchant.moka_fit_score ?? 0;

  const handleGenerate = async () => {
    setLoading(true);
    setOutreach(null);
    setCopied(false);
    try {
      const result = await generateOutreach(merchant.place_id);
      setOutreach(result);
    } catch (err) {
      console.error("Outreach generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (outreach) {
      await navigator.clipboard.writeText(outreach.message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="h-full flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-bold text-white truncate">{merchant.name}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span
              className="text-xs font-bold uppercase px-2 py-0.5 rounded-full"
              style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
            >
              {tier}
            </span>
            <span className="text-xs text-slate-400">
              {CATEGORY_LABELS[merchant.category] ?? merchant.category}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 transition-colors"
          aria-label="Close panel"
        >
          ✕
        </button>
      </div>

      {/* Big Score */}
      <div className="text-center mb-4">
        <div
          className="text-5xl font-extrabold"
          style={{ color: tierColor }}
        >
          {score.toFixed(1)}
        </div>
        <div className="text-xs text-slate-400 mt-1">Moka Fit Score</div>
      </div>

      {/* Score Breakdown */}
      {merchant.score_breakdown && (
        <div className="glass-card p-4 mb-4">
          <h3 className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-3">
            Score Breakdown
          </h3>
          <ScoreBreakdownChart breakdown={merchant.score_breakdown} />
        </div>
      )}

      {/* Details */}
      <div className="glass-card p-4 mb-4">
        <h3 className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-3">
          Business Details
        </h3>
        <div className="space-y-2 text-sm">
          <DetailRow label="District" value={merchant.district ?? "N/A"} />
          <DetailRow label="Rating" value={merchant.rating ? `⭐ ${merchant.rating} (${merchant.review_count} reviews)` : "N/A"} />
          <DetailRow label="Price Level" value={merchant.price_level ? "💰".repeat(merchant.price_level) : "N/A"} />
          <DetailRow label="Website" value={merchant.has_website ? "✅ Yes" : "❌ No"} />
          <DetailRow label="Phone" value={merchant.has_phone ? "✅ Yes" : "❌ No"} />
        </div>
      </div>

      {/* Outreach */}
      <div className="flex-1 flex flex-col min-h-0">
        <button
          id="btn-generate-outreach"
          onClick={handleGenerate}
          disabled={loading}
          className="w-full py-2.5 px-4 bg-[var(--color-accent)] hover:bg-[var(--color-accent-light)] disabled:opacity-50 text-white font-semibold rounded-lg transition-colors duration-200 mb-3 cursor-pointer"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⟳</span> Generating...
            </span>
          ) : (
            "✨ Generate Outreach Message"
          )}
        </button>

        {outreach && (
          <div className="glass-card p-4 flex-1 overflow-y-auto animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Outreach Message
              </h3>
              <button
                id="btn-copy-outreach"
                onClick={handleCopy}
                className="text-xs text-[var(--color-accent-light)] hover:text-white transition-colors cursor-pointer"
              >
                {copied ? "✓ Copied!" : "📋 Copy"}
              </button>
            </div>
            <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
              {outreach.message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-200 font-medium">{value}</span>
    </div>
  );
}
