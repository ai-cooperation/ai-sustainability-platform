"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import {
  fetchStatus,
  fetchForecasts,
  type StatusReport,
  type ForecastResult,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function Overview() {
  const { lang } = useApp();
  const [status, setStatus] = useState<StatusReport | null>(null);
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);

  useEffect(() => {
    fetchStatus().then(setStatus);
    fetchForecasts().then(setForecasts);
  }, []);

  const healthy = status?.healthy ?? 29;
  const total = status?.total ?? 31;
  const statusLabel = status
    ? `${status.degraded} ${t("status.degraded", lang)}, ${status.down} ${t("status.down", lang)}`
    : t("overview.loading", lang);

  const domains = [
    { key: "energy", sources: 7 },
    { key: "climate", sources: 6 },
    { key: "environment", sources: 7 },
    { key: "agriculture", sources: 4 },
    { key: "carbon", sources: 5 },
    { key: "transport", sources: 2 },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("app.title", lang)}
      </h1>
      <p className="mt-1 text-gray-500">
        {t("app.subtitle", lang, { count: total })}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title={t("kpi.co2", lang)} value="37.4" unit="Gt/yr" trend="up" trendValue="+0.8%" color="red" />
        <KPICard title={t("kpi.renewable", lang)} value="30.1" unit="%" trend="up" trendValue="+2.3%" />
        <KPICard title={t("kpi.aqi", lang)} value={42} unit="Good" trend="down" trendValue="-3%" />
        <KPICard title={t("kpi.carbonIntensity", lang)} value={186} unit="gCO2/kWh" trend="down" trendValue="-12%" />
        <KPICard title={t("kpi.apiHealth", lang)} value={`${healthy}/${total}`} unit={t("overview.online", lang)} trend="neutral" trendValue={statusLabel} />
        <KPICard title={t("kpi.forecastAccuracy", lang)} value="78" unit="%" trend="up" trendValue="+5%" />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("overview.platformStatus", lang)}
          </h2>
          <div className="mt-4 space-y-3">
            {domains.map((d) => (
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
                <span className="text-sm font-medium text-green-600">
                  {status ? t("overview.live", lang) : t("overview.loading", lang)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("overview.latestForecast", lang)}
          </h2>
          {forecasts && forecasts.length > 0 ? (
            forecasts.slice(0, 2).map((f, i) => (
              <div
                key={i}
                className={`mt-4 rounded-lg p-4 ${
                  i === 0
                    ? "bg-emerald-50 dark:bg-emerald-900/20"
                    : "bg-blue-50 dark:bg-blue-900/20"
                }`}
              >
                <p
                  className={`text-sm font-medium ${
                    i === 0
                      ? "text-emerald-800 dark:text-emerald-300"
                      : "text-blue-800 dark:text-blue-300"
                  }`}
                >
                  {f.question}
                </p>
                <p
                  className={`mt-2 text-3xl font-bold ${
                    i === 0
                      ? "text-emerald-700 dark:text-emerald-400"
                      : "text-blue-700 dark:text-blue-400"
                  }`}
                >
                  {Math.round(f.probability * 100)}% {t("overview.probability", lang)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  {t("overview.confidence", lang)}: {f.confidence} | {f.positions.length} {t("overview.agents", lang)}
                </p>
              </div>
            ))
          ) : (
            <div className="mt-4 space-y-4">
              <div className="rounded-lg bg-emerald-50 p-4 dark:bg-emerald-900/20">
                <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                  {t("forecast.question1", lang)}
                </p>
                <p className="mt-2 text-3xl font-bold text-emerald-700 dark:text-emerald-400">
                  45% {t("forecast.probability", lang)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  {t("forecast.confidence", lang)}: {t("forecast.medium", lang)} | {t("forecast.agentSources", lang)}
                </p>
              </div>
              <p className="text-xs text-gray-400">
                {t("overview.forecastSchedule", lang)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
