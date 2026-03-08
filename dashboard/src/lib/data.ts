const RAW_BASE =
  "https://raw.githubusercontent.com/ai-cooperation/ai-sustainability-platform/main/data";

export interface ApiStatus {
  name: string;
  status: "healthy" | "degraded" | "down";
  latency_ms: number;
  checked_at: string;
}

export interface StatusReport {
  checked_at: string;
  total: number;
  healthy: number;
  degraded: number;
  down: number;
  results: ApiStatus[];
}

export interface RealtimeWeather {
  timestamp: string;
  temperature_2m: number;
  relative_humidity_2m: number;
  wind_speed_10m: number;
}

export interface RealtimeCarbonIntensity {
  from: string;
  to: string;
  intensity_forecast: number;
  intensity_index: string;
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

export async function fetchWeather(): Promise<RealtimeWeather[] | null> {
  return fetchJson<RealtimeWeather[]>("realtime/weather.json");
}

export async function fetchCarbonIntensity(): Promise<
  RealtimeCarbonIntensity[] | null
> {
  return fetchJson<RealtimeCarbonIntensity[]>(
    "realtime/carbon_intensity_uk.json"
  );
}

export async function fetchForecasts(): Promise<ForecastResult[] | null> {
  return fetchJson<ForecastResult[]>("forecasts/latest.json");
}
