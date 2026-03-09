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
