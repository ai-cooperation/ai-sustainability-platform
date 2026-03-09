"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function CarbonPage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);

  useEffect(() => {
    fetchDomainData("carbon").then(setData);
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  // OWID carbon has the most interesting data
  const owidTs = ts.owid_carbon?.data;
  const owidTimestamps = ts.owid_carbon?.timestamps ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("carbon.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("carbon.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title={t("carbon.globalCo2", lang)}
          value={kpis.co2?.latest?.toFixed(1) ?? "—"}
          unit="Mt/yr"
          trend={kpis.co2 && kpis.co2.latest > kpis.co2.mean ? "up" : "down"}
          trendValue={kpis.co2 ? `avg ${kpis.co2.mean.toFixed(0)}` : ""}
          color="red"
          sparkData={owidTs?.co2}
          sparkColor="#ef4444"
        />
        <KPICard
          title={t("carbon.perCapita", lang)}
          value={kpis.co2_per_capita?.latest?.toFixed(2) ?? "—"}
          unit="t CO2/person"
          trend={kpis.co2_per_capita && kpis.co2_per_capita.latest < kpis.co2_per_capita.mean ? "down" : "up"}
          trendValue={kpis.co2_per_capita ? `avg ${kpis.co2_per_capita.mean.toFixed(2)}` : ""}
          sparkData={owidTs?.co2_per_capita}
          sparkColor="#f59e0b"
        />
        <KPICard
          title={lang === "zh" ? "化石燃料+工業排放" : "Fossil + Industry"}
          value={kpis["Fossil-Fuel-And-Industry"]?.latest?.toFixed(1) ?? "—"}
          unit="GtC/yr"
          trend="up"
          trendValue={kpis["Fossil-Fuel-And-Industry"] ? `avg ${kpis["Fossil-Fuel-And-Industry"].mean.toFixed(1)}` : ""}
          color="red"
          sparkData={ts.open_climate_data?.data?.["Fossil-Fuel-And-Industry"]}
          sparkColor="#dc2626"
        />
      </div>

      {owidTs?.co2 && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            CO₂ {lang === "zh" ? "排放趨勢 (OWID)" : "Emissions Trend (OWID)"}
          </h2>
          <div className="mt-4">
            <Sparkline data={owidTs.co2} color="#ef4444" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{owidTimestamps[0] ?? ""}</span>
            <span>{owidTimestamps.at(-1) ?? ""}</span>
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
