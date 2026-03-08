export type Lang = "en" | "zh";

const translations: Record<string, Record<Lang, string>> = {
  "app.title": {
    en: "AI Sustainability Intelligence Platform",
    zh: "AI 永續發展智慧平台",
  },
  "app.subtitle": {
    en: "Real-time monitoring across {count} global data sources",
    zh: "即時監測 {count} 個全球資料來源",
  },
  "nav.overview": { en: "Overview", zh: "總覽" },
  "nav.energy": { en: "Energy", zh: "能源" },
  "nav.climate": { en: "Climate", zh: "氣候" },
  "nav.environment": { en: "Environment", zh: "環境" },
  "nav.agriculture": { en: "Agriculture", zh: "農業" },
  "nav.carbon": { en: "Carbon", zh: "碳排放" },
  "nav.forecasts": { en: "AI Forecasts", zh: "AI 預測" },
  "nav.status": { en: "API Status", zh: "API 狀態" },
  "status.title": { en: "API Status", zh: "API 狀態" },
  "status.subtitle": {
    en: "Live health monitoring for {count} data sources",
    zh: "即時監測 {count} 個資料來源的健康狀態",
  },
  "status.lastChecked": { en: "Last checked", zh: "最近檢查" },
  "status.healthy": { en: "Healthy", zh: "正常" },
  "status.degraded": { en: "Degraded", zh: "緩慢" },
  "status.down": { en: "Down", zh: "離線" },
  "status.api": { en: "API", zh: "API" },
  "status.domain": { en: "Domain", zh: "領域" },
  "status.latency": { en: "Latency", zh: "延遲" },
  "status.matrix": {
    en: "Health Check History (6h intervals)",
    zh: "健康檢查歷史（每 6 小時）",
  },
  "overview.platformStatus": { en: "Platform Status", zh: "平台狀態" },
  "overview.latestForecast": { en: "Latest AI Forecast", zh: "最新 AI 預測" },
  "overview.sources": { en: "sources", zh: "個來源" },
  "overview.live": { en: "Live", zh: "運作中" },
  "overview.loading": { en: "Loading...", zh: "載入中..." },
  "overview.awaitingForecast": {
    en: "Awaiting first forecast run",
    zh: "等待首次預測執行",
  },
  "overview.weeklyForecast": {
    en: "Daily forecast runs via GitHub Actions",
    zh: "每日自動執行 AI 預測（GitHub Actions）",
  },
  "overview.probability": { en: "probability", zh: "機率" },
  "overview.confidence": { en: "Confidence", zh: "信心度" },
  "overview.agents": { en: "agents", zh: "個代理" },
  "overview.online": { en: "Online", zh: "上線" },
  "kpi.co2": { en: "Global CO2 Emissions", zh: "全球 CO2 排放量" },
  "kpi.renewable": { en: "Renewable Share", zh: "再生能源佔比" },
  "kpi.aqi": { en: "Global Avg AQI", zh: "全球平均 AQI" },
  "kpi.carbonIntensity": { en: "UK Carbon Intensity", zh: "英國碳排強度" },
  "kpi.apiHealth": { en: "API Health", zh: "API 健康度" },
  "kpi.forecastAccuracy": { en: "Forecast Accuracy", zh: "預測準確率" },
  "domain.energy": { en: "Energy", zh: "能源" },
  "domain.climate": { en: "Climate", zh: "氣候" },
  "domain.environment": { en: "Environment", zh: "環境" },
  "domain.agriculture": { en: "Agriculture", zh: "農業" },
  "domain.carbon": { en: "Carbon", zh: "碳排放" },
  "domain.transport": { en: "Transport", zh: "交通" },
  "theme.light": { en: "Light", zh: "淺色" },
  "theme.dark": { en: "Dark", zh: "深色" },
};

export function t(key: string, lang: Lang, params?: Record<string, string | number>): string {
  const entry = translations[key];
  let text = entry?.[lang] ?? entry?.en ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v));
    }
  }
  return text;
}
