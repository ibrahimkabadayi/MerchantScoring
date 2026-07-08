import { useState, useEffect, useCallback } from "react";
import type { Merchant, StatsResponse } from "../types";
import { fetchMerchants, fetchStats, type MerchantFilters } from "../api/client";
import StatsBar from "../components/StatsBar";
import FilterBar from "../components/FilterBar";
import LeadList from "../components/LeadList";
import MerchantMap from "../components/MerchantMap";
import OutreachPanel from "../components/OutreachPanel";
import { Zap } from "lucide-react";

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
    <div className="h-screen w-full flex flex-col p-4 gap-4 overflow-hidden">
      {/* Top Bar */}
      <header className="glass-panel flex-shrink-0 px-8 py-5 flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-light)] flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Zap className="w-6 h-6 fill-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Moka Fit Score
              </h1>
              <p className="text-sm text-slate-400">
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
      <main className="flex-1 flex gap-4 overflow-hidden">
        {/* Left: Lead List */}
        <aside className="glass-panel w-[380px] flex-shrink-0 p-4 overflow-hidden flex flex-col">
          <LeadList
            merchants={merchants}
            selectedId={selectedMerchant?.place_id ?? null}
            onSelect={handleSelect}
            loading={loading}
            total={total}
          />
        </aside>

        {/* Center: Map */}
        <div className="glass-panel flex-1 p-2 min-h-0 flex flex-col">
          <div className="w-full h-full rounded-xl overflow-hidden relative z-0">
            <MerchantMap
              merchants={merchants}
              selectedId={selectedMerchant?.place_id ?? null}
              onSelect={handleSelect}
            />
          </div>
        </div>

        {/* Right: Detail / Outreach Panel */}
        <aside className="glass-panel w-[400px] flex-shrink-0 p-5 overflow-y-auto">
          <OutreachPanel
            merchant={selectedMerchant}
            onClose={handleClosePanel}
          />
        </aside>
      </main>
    </div>
  );
}
