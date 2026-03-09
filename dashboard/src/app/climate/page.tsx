"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function ClimatePage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchDomainData("climate")
      .then((d) => { setData(d); setError(d ? null : "Failed to load data"); })
      .catch(() => setError("Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  if (loading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("climate.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("climate.subtitle", lang)}</p>
      <div className="mt-6"><LoadingSkeleton rows={4} /></div>
    </div>
  );

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("climate.title", lang)}</h1>
      <p className="mt-4 text-red-500">{error}</p>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("climate.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("climate.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title={t("climate.co2", lang)}
          value={kpis.co2_ppm?.latest?.toFixed(1) ?? "—"}
          unit="ppm"
          trend="up"
          trendValue={kpis.co2_ppm ? `avg ${kpis.co2_ppm.mean.toFixed(1)}` : ""}
          color="red"
        />
        <KPICard
          title={t("climate.tempAnomaly", lang)}
          value={kpis.temperature?.mean?.toFixed(1) ?? "—"}
          unit="°C"
          trend={kpis.temperature && kpis.temperature.latest > kpis.temperature.mean ? "up" : "down"}
          trendValue={kpis.temperature ? `${kpis.temperature.min.toFixed(1)}–${kpis.temperature.max.toFixed(1)}°C` : ""}
          sparkData={ts.open_meteo_weather?.data?.temperature}
          sparkColor="#ef4444"
        />
        <KPICard
          title={t("climate.humidity", lang)}
          value={kpis.humidity?.mean?.toFixed(0) ?? "—"}
          unit="%"
          trend="neutral"
          trendValue={kpis.humidity ? `${kpis.humidity.min.toFixed(0)}–${kpis.humidity.max.toFixed(0)}%` : ""}
          sparkData={ts.open_meteo_weather?.data?.humidity}
          sparkColor="#3b82f6"
        />
      </div>

      {ts.open_meteo_weather?.data?.temperature && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("climate.tempTrend", lang)}
          </h2>
          <div className="mt-4">
            <Sparkline data={ts.open_meteo_weather.data.temperature} color="#ef4444" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{ts.open_meteo_weather.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{ts.open_meteo_weather.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
          </div>
        </div>
      )}

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("common.dataSources", lang)} ({data?.record_count?.toLocaleString() ?? 0} records)
        </h2>
        <div className="mt-4 space-y-2">
          {sources.map((s) => (
            <div key={s} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
              <span className="text-sm text-gray-700 dark:text-gray-300">{t(`api.${s}.name`, lang)}</span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs text-gray-500">{ts[s]?.timestamps?.length ?? 0} pts</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
