"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  fetchStatus,
  fetchForecasts,
  fetchOverview,
  fetchDomainData,
  fetchTaiPower,
  type StatusReport,
  type ForecastResult,
  type OverviewData,
  type DomainData,
  type TaiPowerData,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function Overview() {
  const { lang } = useApp();
  const [status, setStatus] = useState<StatusReport | null>(null);
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [domains, setDomains] = useState<Record<string, DomainData>>({});
  const [taipower, setTaipower] = useState<TaiPowerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const names = ["energy", "climate", "environment", "agriculture", "carbon"];

    Promise.all([
      fetchStatus().then(setStatus),
      fetchForecasts().then(setForecasts),
      fetchOverview().then(setOverview),
      fetchTaiPower().then(setTaipower),
      Promise.all(names.map((n) => fetchDomainData(n))).then((results) => {
        const map: Record<string, DomainData> = {};
        results.forEach((r, i) => {
          if (r) map[names[i]] = r;
        });
        setDomains(map);
      }),
    ])
      .then(() => setError(null))
      .catch(() => setError("Failed to load overview data"))
      .finally(() => setLoading(false));
  }, []);

  const healthy = status?.healthy ?? 0;
  const total = status?.total ?? 31;
  const statusLabel = status
    ? `${status.degraded} ${t("status.degraded", lang)}, ${status.down} ${t("status.down", lang)}`
    : t("overview.loading", lang);

  // Extract KPIs + sparklines from domain data
  const energyKpis = overview?.domains?.energy?.kpis ?? {};
  const climateKpis = overview?.domains?.climate?.kpis ?? {};
  const envKpis = overview?.domains?.environment?.kpis ?? {};
  const carbonKpis = overview?.domains?.carbon?.kpis ?? {};

  // Time series for sparklines
  const energyTs = domains.energy?.time_series ?? {};
  const climateTs = domains.climate?.time_series ?? {};
  const envTs = domains.environment?.time_series ?? {};
  const carbonTs = domains.carbon?.time_series ?? {};

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

  if (loading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("app.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("app.subtitle", lang, { count: total })}</p>
      <div className="mt-6"><LoadingSkeleton rows={4} /></div>
    </div>
  );

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("app.title", lang)}</h1>
      <p className="mt-4 text-red-500">{error}</p>
    </div>
  );

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
        {/* Row 1: Temperature, Renewable Energy, Solar Radiation */}
        <KPICard
          title={t("kpi.temperature", lang)}
          value={energyKpis.temperature_2m?.latest?.toFixed(1) ?? energyKpis.temperature?.latest?.toFixed(1) ?? "—"}
          unit="°C"
          trend={energyKpis.temperature_2m && energyKpis.temperature_2m.latest > energyKpis.temperature_2m.mean ? "up" : "down"}
          trendValue={energyKpis.temperature_2m ? `avg ${energyKpis.temperature_2m.mean.toFixed(1)}°C` : ""}
          sparkData={energyTs.open_meteo_solar?.data?.temperature_2m}
          sparkForecast={energyTs.open_meteo_solar?.forecast?.temperature_2m}
          sparkColor="#3b82f6"
          sparkLabel={t("spark.temp", lang)}
          sparkRange={t("spark.range.7d+7d", lang)}
          color="blue"
        />
        <KPICard
          title={t("kpi.renewable", lang)}
          value={taipower?.latest?.renewable_pct != null ? Number(taipower.latest.renewable_pct).toFixed(1) : "—"}
          unit="%"
          trend={taipower?.latest?.renewable_pct != null && Number(taipower.latest.renewable_pct) > 15 ? "up" : "down"}
          trendValue={taipower?.latest ? `${Number(taipower.latest.solar_mw ?? 0).toFixed(0)} MW ☀️ + ${Number(taipower.latest.wind_mw ?? 0).toFixed(0)} MW 💨` : ""}
          sparkData={taipower?.time_series?.renewable_pct?.filter((v): v is number => v != null)}
          sparkColor="#10b981"
          sparkLabel={t("spark.renewablePct", lang)}
          sparkRange={t("spark.range.realtime", lang)}
        />
        <KPICard
          title={t("kpi.solarTaipei", lang)}
          value={energyKpis.direct_radiation?.latest?.toFixed(0) ?? "—"}
          unit="W/m²"
          trend={energyKpis.direct_radiation && energyKpis.direct_radiation.latest > energyKpis.direct_radiation.mean ? "up" : "down"}
          trendValue={energyKpis.direct_radiation ? `avg ${energyKpis.direct_radiation.mean.toFixed(0)} W/m²` : ""}
          sparkData={energyTs.open_meteo_solar?.data?.direct_radiation}
          sparkForecast={energyTs.open_meteo_solar?.forecast?.direct_radiation}
          sparkColor="#f97316"
          sparkLabel={t("spark.directRad", lang)}
          sparkRange={t("spark.range.7d+7d", lang)}
          color="amber"
        />
        {/* Row 2: CO₂ ppm, Global Emissions, Air Quality */}
        <KPICard
          title={t("common.co2ppm", lang)}
          value={climateKpis.co2_ppm?.latest?.toFixed(1) ?? "—"}
          unit="ppm"
          trend="up"
          trendValue={climateKpis.co2_ppm ? `avg ${climateKpis.co2_ppm.mean.toFixed(1)} ppm` : ""}
          sparkData={climateTs.noaa_ghg?.data?.co2_ppm}
          sparkColor="#ef4444"
          sparkLabel={t("spark.co2ppm", lang)}
          sparkRange={t("spark.range.14y", lang)}
          color="red"
        />
        <KPICard
          title={t("kpi.co2", lang)}
          value={carbonKpis.co2?.latest?.toFixed(1) ?? "—"}
          unit="Mt CO₂"
          trend={carbonKpis.co2 && carbonKpis.co2.latest > carbonKpis.co2.mean ? "up" : "down"}
          trendValue={carbonKpis.co2 ? `avg ${carbonKpis.co2.mean.toFixed(0)} Mt` : ""}
          sparkData={carbonTs.owid_carbon?.data?.co2}
          sparkColor="#ef4444"
          sparkLabel={t("spark.emissions", lang)}
          sparkRange={t("spark.range.historical", lang)}
          color="red"
        />
        <KPICard
          title={t("kpi.aqi", lang)}
          value={envKpis.pm2_5?.latest?.toFixed(1) ?? "—"}
          unit="µg/m³ PM2.5"
          trend={envKpis.pm2_5 && envKpis.pm2_5.latest < envKpis.pm2_5.mean ? "down" : "up"}
          trendValue={envKpis.pm2_5 ? `avg ${envKpis.pm2_5.mean.toFixed(1)}` : ""}
          sparkData={envTs.open_meteo_air_quality?.data?.pm2_5}
          sparkColor="#10b981"
          sparkLabel="PM2.5"
          sparkRange={t("spark.range.7d", lang)}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("overview.platformStatus", lang)}
            </h2>
            {status && (
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2.5 w-2.5 rounded-full ${healthy === total ? "bg-green-500" : healthy >= 25 ? "bg-yellow-500" : "bg-red-500"}`} />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {healthy}/{total} {t("overview.online", lang)}
                </span>
                {(status.degraded > 0 || status.down > 0) && (
                  <span className="text-xs text-gray-500">
                    ({statusLabel})
                  </span>
                )}
              </div>
            )}
          </div>
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
                      {d.records.toLocaleString()} {t("common.records", lang)}
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
