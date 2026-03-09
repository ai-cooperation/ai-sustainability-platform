"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import {
  fetchStatus,
  fetchForecasts,
  fetchOverview,
  type StatusReport,
  type ForecastResult,
  type OverviewData,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function Overview() {
  const { lang } = useApp();
  const [status, setStatus] = useState<StatusReport | null>(null);
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);
  const [overview, setOverview] = useState<OverviewData | null>(null);

  useEffect(() => {
    fetchStatus().then(setStatus);
    fetchForecasts().then(setForecasts);
    fetchOverview().then(setOverview);
  }, []);

  const healthy = status?.healthy ?? 0;
  const total = status?.total ?? 31;
  const statusLabel = status
    ? `${status.degraded} ${t("status.degraded", lang)}, ${status.down} ${t("status.down", lang)}`
    : t("overview.loading", lang);

  // Extract real KPIs from overview data
  const carbonKpi = overview?.domains?.carbon?.kpis?.co2;
  const intensityKpi = overview?.domains?.energy?.kpis?.intensity_forecast;
  const solarKpi = overview?.domains?.energy?.kpis?.shortwave_radiation;
  const pm25Kpi = overview?.domains?.environment?.kpis?.pm2_5;
  const co2ppmKpi = overview?.domains?.climate?.kpis?.co2_ppm;

  // Build domain list from real data
  const domainEntries = overview
    ? Object.entries(overview.domains).map(([key, d]) => ({
        key,
        sources: d.sources.length,
        records: d.record_count,
      }))
    : [
        { key: "energy", sources: 7, records: 0 },
        { key: "climate", sources: 6, records: 0 },
        { key: "environment", sources: 7, records: 0 },
        { key: "agriculture", sources: 4, records: 0 },
        { key: "carbon", sources: 5, records: 0 },
      ];

  const updatedAt = overview?.updated_at
    ? new Date(overview.updated_at).toLocaleString()
    : null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("app.title", lang)}
      </h1>
      <p className="mt-1 text-gray-500">
        {t("app.subtitle", lang, { count: total })}
        {updatedAt && (
          <span className="ml-2 text-xs">
            ({t("status.lastChecked", lang)}: {updatedAt})
          </span>
        )}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title={t("kpi.co2", lang)}
          value={carbonKpi ? carbonKpi.latest.toFixed(1) : "—"}
          unit="Gt/yr"
          trend={carbonKpi && carbonKpi.latest > carbonKpi.mean ? "up" : "neutral"}
          trendValue={carbonKpi ? `avg ${carbonKpi.mean.toFixed(1)}` : ""}
          color="red"
          sparkColor="#ef4444"
        />
        <KPICard
          title={t("kpi.renewable", lang)}
          value={solarKpi ? solarKpi.mean.toFixed(0) : "—"}
          unit="W/m²"
          trend="up"
          trendValue={solarKpi ? `max ${solarKpi.max.toFixed(0)}` : ""}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("kpi.aqi", lang)}
          value={pm25Kpi ? pm25Kpi.latest.toFixed(1) : "—"}
          unit="µg/m³ PM2.5"
          trend={pm25Kpi && pm25Kpi.latest < pm25Kpi.mean ? "down" : "up"}
          trendValue={pm25Kpi ? `avg ${pm25Kpi.mean.toFixed(1)}` : ""}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("kpi.carbonIntensity", lang)}
          value={intensityKpi ? intensityKpi.latest.toFixed(0) : "—"}
          unit="gCO2/kWh"
          trend={intensityKpi && intensityKpi.latest < intensityKpi.mean ? "down" : "up"}
          trendValue={intensityKpi ? `avg ${intensityKpi.mean.toFixed(0)}` : ""}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("kpi.apiHealth", lang)}
          value={status ? `${healthy}/${total}` : "—"}
          unit={t("overview.online", lang)}
          trend="neutral"
          trendValue={statusLabel}
          sparkColor="#6b7280"
        />
        <KPICard
          title="CO₂ (ppm)"
          value={co2ppmKpi ? co2ppmKpi.latest.toFixed(1) : "—"}
          unit="ppm"
          trend="up"
          trendValue={co2ppmKpi ? `avg ${co2ppmKpi.mean.toFixed(1)}` : ""}
          color="red"
          sparkColor="#ef4444"
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("overview.platformStatus", lang)}
          </h2>
          <div className="mt-4 space-y-3">
            {domainEntries.map((d) => (
              <div
                key={d.key}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3 dark:bg-gray-700"
              >
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {t(`domain.${d.key}`, lang)}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    {d.sources} {t("overview.sources", lang)}
                  </span>
                </div>
                <div className="text-right">
                  {d.records > 0 ? (
                    <span className="text-sm font-medium text-green-600">
                      {d.records.toLocaleString()} records
                    </span>
                  ) : (
                    <span className="text-sm text-gray-400">
                      {t("overview.loading", lang)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("overview.latestForecast", lang)}
          </h2>
          {forecasts && forecasts.length > 0 ? (
            forecasts.slice(0, 3).map((f, i) => {
              const colors = [
                { bg: "bg-emerald-50 dark:bg-emerald-900/20", text: "text-emerald-800 dark:text-emerald-300", num: "text-emerald-700 dark:text-emerald-400" },
                { bg: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-800 dark:text-blue-300", num: "text-blue-700 dark:text-blue-400" },
                { bg: "bg-amber-50 dark:bg-amber-900/20", text: "text-amber-800 dark:text-amber-300", num: "text-amber-700 dark:text-amber-400" },
              ];
              const c = colors[i % colors.length];
              return (
                <div key={i} className={`mt-4 rounded-lg p-4 ${c.bg}`}>
                  <p className={`text-sm font-medium ${c.text}`}>{f.question}</p>
                  <p className={`mt-2 text-3xl font-bold ${c.num}`}>
                    {Math.round(f.probability * 100)}% {t("overview.probability", lang)}
                  </p>
                  <p className="mt-1 text-sm text-gray-500">
                    {t("overview.confidence", lang)}: {f.confidence} | {f.positions.length} {t("overview.agents", lang)}
                  </p>
                </div>
              );
            })
          ) : (
            <p className="mt-4 text-sm text-gray-400">
              {t("overview.forecastSchedule", lang)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
