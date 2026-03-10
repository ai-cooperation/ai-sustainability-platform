const RAW_BASE =
  "https://raw.githubusercontent.com/ai-cooperation/ai-sustainability-platform/main/data";

export interface ApiStatus {
  id: string;
  domain: string;
  status: "healthy" | "degraded" | "down";
  latency_ms: number;
  message: string;
  checked_at: string;
}

export interface StatusReport {
  checked_at: string;
  total: number;
  healthy: number;
  degraded: number;
  down: number;
  apis: ApiStatus[];
}

export interface HistoryEntry {
  checked_at: string;
  total: number;
  healthy: number;
  degraded: number;
  down: number;
  apis: ApiStatus[];
}

export interface ForecastResult {
  question: string;
  probability: number;
  confidence: string;
  reasoning: string;
  positions: { agent: string; probability: number; reasoning: string }[];
  created_at: string;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${RAW_BASE}/${path}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchStatus(): Promise<StatusReport | null> {
  return fetchJson<StatusReport>("status/status.json");
}

export async function fetchHistory(
  date: string
): Promise<HistoryEntry[] | null> {
  return fetchJson<HistoryEntry[]>(`status/history/${date}.json`);
}

/** Fetch history entries from the last N days, merged and sorted by time. */
export async function fetchRecentHistory(
  days: number = 3
): Promise<HistoryEntry[]> {
  const dates: string[] = [];
  const now = new Date();
  for (let i = 0; i < days; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().split("T")[0]);
  }
  const results = await Promise.all(dates.map((d) => fetchHistory(d)));
  const merged: HistoryEntry[] = [];
  for (const r of results) {
    if (r) merged.push(...r);
  }
  return merged.sort(
    (a, b) => new Date(a.checked_at).getTime() - new Date(b.checked_at).getTime()
  );
}

export async function fetchForecasts(): Promise<ForecastResult[] | null> {
  return fetchJson<ForecastResult[]>("forecasts/latest.json");
}

// --- Domain dashboard data ---

export interface KpiSummary {
  latest: number;
  mean: number;
  min: number;
  max: number;
  count: number;
}

export interface TimeSeriesData {
  timestamps: string[];
  data: Record<string, number[]>;
  forecast_timestamps?: string[];
  forecast?: Record<string, number[]>;
}

export interface DomainData {
  domain: string;
  updated_at: string;
  record_count: number;
  file: string;
  sources: string[];
  columns: string[];
  kpis: Record<string, KpiSummary>;
  time_series: Record<string, TimeSeriesData>;
}

export interface OverviewData {
  updated_at: string;
  domains: Record<string, {
    record_count: number;
    sources: string[];
    kpis: Record<string, KpiSummary>;
  }>;
}

export async function fetchDomainData(domain: string): Promise<DomainData | null> {
  return fetchJson<DomainData>(`dashboard/${domain}.json`);
}

export async function fetchOverview(): Promise<OverviewData | null> {
  return fetchJson<OverviewData>("dashboard/overview.json");
}

// --- TaiPower real-time data ---

export interface TaiPowerDailyPeak {
  date: string;
  solar_mw_max: number;
  wind_mw_max: number;
  hydro_mw_max: number;
  renewable_mw_max: number;
  total_mw_max: number;
  renewable_pct_max: number;
  load_mw_max: number;
  count: number;
}

export interface TaiPowerData {
  updated_at: string;
  latest: Record<string, number | string>;
  record_count: number;
  time_series: {
    timestamps: string[];
    renewable_pct: (number | null)[];
    solar_mw: (number | null)[];
    wind_mw: (number | null)[];
    hydro_mw: (number | null)[];
    total_mw: (number | null)[];
    renewable_mw: (number | null)[];
    load_mw: (number | null)[];
    util_rate_pct: (number | null)[];
    fore_reserve_pct: (number | null)[];
  };
  daily_peaks: TaiPowerDailyPeak[];
}

const TAIPOWER_BASE =
  "https://raw.githubusercontent.com/ai-cooperation/taipower-data/main/data";

export async function fetchTaiPower(): Promise<TaiPowerData | null> {
  try {
    const res = await fetch(`${TAIPOWER_BASE}/dashboard.json`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as TaiPowerData;
  } catch {
    return null;
  }
}
