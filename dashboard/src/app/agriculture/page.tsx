"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function AgriculturePage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);

  useEffect(() => {
    fetchDomainData("agriculture").then(setData);
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("agri.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("agri.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title={lang === "zh" ? "農產品價格指數" : "Price Index"}
          value={kpis.price?.mean?.toFixed(1) ?? "—"}
          unit=""
          trend={kpis.price && kpis.price.latest < kpis.price.mean ? "down" : "up"}
          trendValue={kpis.price ? `${kpis.price.min.toFixed(0)}–${kpis.price.max.toFixed(0)}` : ""}
        />
        <KPICard
          title={lang === "zh" ? "生物多樣性觀測" : "Biodiversity Observations"}
          value={kpis.latitude?.count ?? "—"}
          unit={lang === "zh" ? "筆記錄" : "records"}
          trend="neutral"
          trendValue={`GBIF ${lang === "zh" ? "資料" : "data"}`}
        />
        <KPICard
          title={lang === "zh" ? "總記錄數" : "Total Records"}
          value={data?.record_count?.toLocaleString() ?? "—"}
          unit=""
          trend="neutral"
          trendValue={`${sources.length} ${t("overview.sources", lang)}`}
        />
      </div>

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
