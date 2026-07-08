export interface ScoreBreakdown {
  digital_readiness: number;
  growth_momentum: number;
  reachability: number;
  sector_fit: number;
}

export interface Merchant {
  place_id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  address: string | null;
  district: string | null;
  rating: number | null;
  review_count: number | null;
  price_level: number | null;
  has_website: boolean;
  has_phone: boolean;
  moka_fit_score: number | null;
  score_breakdown: ScoreBreakdown | null;
  priority_tier: string | null;
}

export interface MerchantListResponse {
  total: number;
  merchants: Merchant[];
}

export interface StatsResponse {
  total_merchants: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  avg_score: number;
  category_distribution: Record<string, number>;
  district_distribution: Record<string, number>;
}

export interface OutreachResponse {
  place_id: string;
  merchant_name: string;
  message: string;
}

export type Tier = "HIGH" | "MEDIUM" | "LOW";

export const TIER_COLORS: Record<Tier, string> = {
  HIGH: "#10b981",
  MEDIUM: "#f59e0b",
  LOW: "#ef4444",
};

export const TIER_LABELS: Record<Tier, string> = {
  HIGH: "High Priority",
  MEDIUM: "Medium Priority",
  LOW: "Low Priority",
};

export const CATEGORY_LABELS: Record<string, string> = {
  restaurant: "Restaurant",
  cafe: "Cafe",
  clothing_store: "Clothing",
  electronics_store: "Electronics",
  beauty_salon: "Beauty Salon",
};
