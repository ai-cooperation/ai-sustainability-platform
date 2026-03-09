"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function EnvironmentPage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);

  useEffect(() => {
    fetchDomainData("environment").then(setData);
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("env.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("env.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title={t("env.pm25", lang)}
          value={kpis.pm2_5?.latest?.toFixed(1) ?? "—"}
          unit="µg/m³"
          trend={kpis.pm2_5 && kpis.pm2_5.latest < kpis.pm2_5.mean ? "down" : "up"}
          trendValue={kpis.pm2_5 ? `avg ${kpis.pm2_5.mean.toFixed(1)}` : ""}
          sparkData={ts.open_meteo_air_quality?.data?.pm2_5}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("env.aqi", lang)}
          value={kpis.aqi?.latest?.toFixed(0) ?? "—"}
          unit={kpis.aqi && kpis.aqi.latest <= 50 ? t("env.good", lang) : ""}
          trend={kpis.aqi && kpis.aqi.latest < kpis.aqi.mean ? "down" : "up"}
          trendValue={kpis.aqi ? `avg ${kpis.aqi.mean.toFixed(0)}` : ""}
        />
        <KPICard
          title={t("env.no2", lang)}
          value={kpis.no2?.latest?.toFixed(1) ?? "—"}
          unit="µg/m³"
          trend={kpis.no2 && kpis.no2.latest < kpis.no2.mean ? "down" : "up"}
          trendValue={kpis.no2 ? `avg ${kpis.no2.mean.toFixed(1)}` : ""}
          sparkData={ts.open_meteo_air_quality?.data?.no2}
          sparkColor="#6366f1"
        />
        <KPICard
          title="PM10"
          value={kpis.pm10?.latest?.toFixed(1) ?? "—"}
          unit="µg/m³"
          trend={kpis.pm10 && kpis.pm10.latest < kpis.pm10.mean ? "down" : "up"}
          trendValue={kpis.pm10 ? `avg ${kpis.pm10.mean.toFixed(1)}` : ""}
          sparkData={ts.open_meteo_air_quality?.data?.pm10}
          sparkColor="#f59e0b"
        />
      </div>

      {ts.open_meteo_air_quality?.data?.pm2_5 && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            PM2.5 — {lang === "zh" ? "趨勢" : "Trend"}
          </h2>
          <div className="mt-4">
            <Sparkline data={ts.open_meteo_air_quality.data.pm2_5} color="#10b981" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{ts.open_meteo_air_quality.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{ts.open_meteo_air_quality.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
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
