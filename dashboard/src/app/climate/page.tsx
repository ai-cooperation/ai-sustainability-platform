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
          title={t("common.co2ppm", lang)}
          value={kpis.co2_ppm?.latest?.toFixed(1) ?? "—"}
          unit="ppm"
          trend="up"
          trendValue={kpis.co2_ppm ? `avg ${kpis.co2_ppm.mean.toFixed(1)}` : ""}
          sparkData={ts.noaa_ghg?.data?.co2_ppm}
          sparkColor="#ef4444"
          color="red"
        />
        <KPICard
          title={t("climate.tempMax", lang)}
          value={kpis.temperature_max?.latest?.toFixed(1) ?? "—"}
          unit="°C"
          trend={kpis.temperature_max && kpis.temperature_max.latest > kpis.temperature_max.mean ? "up" : "down"}
          trendValue={kpis.temperature_max ? `avg ${kpis.temperature_max.mean.toFixed(1)}°C` : ""}
          sparkData={ts.open_meteo_climate?.data?.temperature_max}
          sparkColor="#ef4444"
        />
        <KPICard
          title={t("climate.precipitation", lang)}
          value={kpis.precipitation?.latest?.toFixed(1) ?? "—"}
          unit="mm"
          trend={kpis.precipitation && kpis.precipitation.latest > kpis.precipitation.mean ? "up" : "down"}
          trendValue={kpis.precipitation ? `avg ${kpis.precipitation.mean.toFixed(1)} mm` : ""}
          sparkData={ts.open_meteo_climate?.data?.precipitation}
          sparkColor="#3b82f6"
        />
      </div>

      {ts.open_meteo_climate?.data?.temperature_max && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("climate.tempTrend", lang)}
          </h2>
          <div className="mt-4">
            <Sparkline data={ts.open_meteo_climate.data.temperature_max} color="#ef4444" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{ts.open_meteo_climate.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{ts.open_meteo_climate.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
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
