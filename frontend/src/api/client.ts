import axios from "axios";
import type {
  Merchant,
  MerchantListResponse,
  StatsResponse,
  OutreachResponse,
} from "../types";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

export interface MerchantFilters {
  tier?: string;
  category?: string;
  district?: string;
  min_score?: number;
  sort_by?: string;
  limit?: number;
  offset?: number;
}

export async function fetchMerchants(
  filters: MerchantFilters = {}
): Promise<MerchantListResponse> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")
  );
  const { data } = await api.get<MerchantListResponse>("/merchants", {
    params,
  });
  return data;
}

export async function fetchTopMerchants(
  limit: number = 20
): Promise<Merchant[]> {
  const { data } = await api.get<Merchant[]>("/merchants/top", {
    params: { limit },
  });
  return data;
}

export async function fetchMerchant(placeId: string): Promise<Merchant> {
  const { data } = await api.get<Merchant>(`/merchants/${placeId}`);
  return data;
}

export async function fetchStats(): Promise<StatsResponse> {
  const { data } = await api.get<StatsResponse>("/merchants/stats");
  return data;
}

export async function generateOutreach(
  placeId: string
): Promise<OutreachResponse> {
  const { data } = await api.post<OutreachResponse>("/outreach/generate", {
    place_id: placeId,
  });
  return data;
}
