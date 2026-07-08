import { CATEGORY_LABELS } from "../types";

interface FilterBarProps {
  categories: string[];
  districts: string[];
  selectedCategory: string;
  selectedDistrict: string;
  selectedTier: string;
  onCategoryChange: (v: string) => void;
  onDistrictChange: (v: string) => void;
  onTierChange: (v: string) => void;
}

export default function FilterBar({
  categories,
  districts,
  selectedCategory,
  selectedDistrict,
  selectedTier,
  onCategoryChange,
  onDistrictChange,
  onTierChange,
}: FilterBarProps) {
  const selectClass =
    "bg-[var(--color-surface-light)] border border-[var(--color-border)] text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[var(--color-accent)] transition-colors cursor-pointer appearance-none";

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
        Filters
      </span>

      {/* Tier */}
      <select
        id="filter-tier"
        value={selectedTier}
        onChange={(e) => onTierChange(e.target.value)}
        className={selectClass}
      >
        <option value="">All Tiers</option>
        <option value="HIGH">🟢 High</option>
        <option value="MEDIUM">🟡 Medium</option>
        <option value="LOW">🔴 Low</option>
      </select>

      {/* Category */}
      <select
        id="filter-category"
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
        className={selectClass}
      >
        <option value="">All Categories</option>
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {CATEGORY_LABELS[cat] ?? cat}
          </option>
        ))}
      </select>

      {/* District */}
      <select
        id="filter-district"
        value={selectedDistrict}
        onChange={(e) => onDistrictChange(e.target.value)}
        className={selectClass}
      >
        <option value="">All Districts</option>
        {districts.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>

      {/* Clear */}
      {(selectedTier || selectedCategory || selectedDistrict) && (
        <button
          onClick={() => {
            onTierChange("");
            onCategoryChange("");
            onDistrictChange("");
          }}
          className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded border border-[var(--color-border)] hover:border-slate-400 transition-colors"
        >
          Clear All
        </button>
      )}
    </div>
  );
}
