"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function EnergyPage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchDomainData("energy")
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
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("energy.subtitle", lang)}</p>
      <div className="mt-6"><LoadingSkeleton rows={4} /></div>
    </div>
  );

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-4 text-red-500">{error}</p>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("energy.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title={t("energy.solarRadiation", lang)}
          value={kpis.shortwave_radiation?.mean?.toFixed(0) ?? "—"}
          unit="W/m²"
          trend="up"
          trendValue={kpis.shortwave_radiation ? `max ${kpis.shortwave_radiation.max.toFixed(0)} W/m²` : ""}
          sparkData={ts.open_meteo_solar?.data?.shortwave_radiation}
          sparkColor="#f59e0b"
        />
        <KPICard
          title={t("energy.directRad", lang)}
          value={kpis.direct_radiation?.mean?.toFixed(0) ?? "—"}
          unit="W/m²"
          trend="up"
          trendValue={kpis.direct_radiation ? `max ${kpis.direct_radiation.max.toFixed(0)} W/m²` : ""}
          sparkData={ts.open_meteo_solar?.data?.direct_radiation}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("energy.nasaSolar", lang)}
          value={kpis.solar_radiation?.mean?.toFixed(2) ?? "—"}
          unit="kWh/m²/day"
          trend="neutral"
          trendValue="from NASA POWER"
          sparkData={ts.nasa_power?.data?.solar_radiation}
          sparkColor="#6366f1"
        />
        <KPICard
          title={t("kpi.carbonIntensity", lang)}
          value={kpis.intensity_forecast?.latest?.toFixed(0) ?? "—"}
          unit="gCO₂/kWh"
          trend={kpis.intensity_forecast && kpis.intensity_forecast.latest < kpis.intensity_forecast.mean ? "down" : "neutral"}
          trendValue=""
          sparkColor="#ef4444"
        />
      </div>

      {ts.open_meteo_solar?.data?.shortwave_radiation && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("energy.solarRadiation", lang)} — 7-day trend
          </h2>
          <div className="mt-4">
            <Sparkline data={ts.open_meteo_solar.data.shortwave_radiation} color="#f59e0b" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{ts.open_meteo_solar.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{ts.open_meteo_solar.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
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
