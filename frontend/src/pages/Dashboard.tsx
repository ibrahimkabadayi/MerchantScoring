import { useState, useEffect, useCallback } from "react";
import type { Merchant, StatsResponse } from "../types";
import { fetchMerchants, fetchStats, type MerchantFilters } from "../api/client";
import StatsBar from "../components/StatsBar";
import FilterBar from "../components/FilterBar";
import LeadList from "../components/LeadList";
import MerchantMap from "../components/MerchantMap";
import OutreachPanel from "../components/OutreachPanel";

export default function Dashboard() {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);

  // Filters
  const [tier, setTier] = useState("");
  const [category, setCategory] = useState("");
  const [district, setDistrict] = useState("");

  // Derived filter options
  const categories = Object.keys(stats?.category_distribution ?? {}).sort();
  const districts = Object.keys(stats?.district_distribution ?? {}).sort();

  // Load stats once
  useEffect(() => {
    setStatsLoading(true);
    fetchStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setStatsLoading(false));
  }, []);

  // Load merchants when filters change
  const loadMerchants = useCallback(async () => {
    setLoading(true);
    try {
      const filters: MerchantFilters = {
        limit: 250,
        sort_by: "score",
      };
      if (tier) filters.tier = tier;
      if (category) filters.category = category;
      if (district) filters.district = district;

      const result = await fetchMerchants(filters);
      setMerchants(result.merchants);
      setTotal(result.total);
    } catch (err) {
      console.error("Failed to load merchants:", err);
    } finally {
      setLoading(false);
    }
  }, [tier, category, district]);

  useEffect(() => {
    loadMerchants();
  }, [loadMerchants]);

  const handleSelect = (m: Merchant) => {
    setSelectedMerchant(m);
  };

  const handleClosePanel = () => {
    setSelectedMerchant(null);
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top Bar */}
      <header className="flex-shrink-0 border-b border-[var(--color-border)] px-5 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-accent)] to-purple-500 flex items-center justify-center text-white font-bold text-sm">
              M
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Moka Fit Score
              </h1>
              <p className="text-[11px] text-slate-500 -mt-0.5">
                AI-Powered Lead Scoring Dashboard
              </p>
            </div>
          </div>
          <FilterBar
            categories={categories}
            districts={districts}
            selectedCategory={category}
            selectedDistrict={district}
            selectedTier={tier}
            onCategoryChange={setCategory}
            onDistrictChange={setDistrict}
            onTierChange={setTier}
          />
        </div>
        <StatsBar stats={stats} loading={statsLoading} />
      </header>

      {/* Main Content — 3-column layout */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: Lead List */}
        <aside className="w-[340px] flex-shrink-0 border-r border-[var(--color-border)] p-3 overflow-hidden flex flex-col">
          <LeadList
            merchants={merchants}
            selectedId={selectedMerchant?.place_id ?? null}
            onSelect={handleSelect}
            loading={loading}
            total={total}
          />
        </aside>

        {/* Center: Map */}
        <div className="flex-1 p-3 min-h-0">
          <div className="w-full h-full">
            <MerchantMap
              merchants={merchants}
              selectedId={selectedMerchant?.place_id ?? null}
              onSelect={handleSelect}
            />
          </div>
        </div>

        {/* Right: Detail / Outreach Panel */}
        <aside className="w-[360px] flex-shrink-0 border-l border-[var(--color-border)] p-4 overflow-y-auto">
          <OutreachPanel
            merchant={selectedMerchant}
            onClose={handleClosePanel}
          />
        </aside>
      </main>
    </div>
  );
}
