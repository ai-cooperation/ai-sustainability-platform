"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { fetchDomainData, type DomainData } from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function AgriculturePage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchDomainData("agriculture")
      .then((d) => { setData(d); setError(d ? null : "Failed to load data"); })
      .catch(() => setError("Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  // Find first available time series for the trend chart
  const agriTsKey = Object.keys(ts).find((k) => ts[k]?.timestamps?.length > 1);
  const agriTsData = agriTsKey ? ts[agriTsKey] : null;
  const firstDataKey = agriTsData ? Object.keys(agriTsData.data)[0] : null;

  if (loading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("agri.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("agri.subtitle", lang)}</p>
      <div className="mt-6"><LoadingSkeleton rows={4} /></div>
    </div>
  );

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("agri.title", lang)}</h1>
      <p className="mt-4 text-red-500">{error}</p>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("agri.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("agri.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title={t("agri.priceIndex", lang)}
          value={kpis.price?.mean?.toFixed(1) ?? "—"}
          unit=""
          trend={kpis.price && kpis.price.latest < kpis.price.mean ? "down" : "up"}
          trendValue={kpis.price ? `${kpis.price.min.toFixed(0)}–${kpis.price.max.toFixed(0)}` : ""}
          sparkData={ts.eu_agri_food?.data?.price}
          sparkColor="#10b981"
        />
        <KPICard
          title={t("agri.biodiversity", lang)}
          value={kpis.latitude?.count ?? "—"}
          unit={t("agri.records", lang)}
          trend="neutral"
          trendValue={`GBIF ${t("agri.gbifData", lang)}`}
          sparkData={ts.gbif_biodiversity?.data?.latitude}
          sparkColor="#6366f1"
        />
        <KPICard
          title={t("agri.totalRecords", lang)}
          value={data?.record_count?.toLocaleString() ?? "—"}
          unit=""
          trend="neutral"
          trendValue={`${sources.length} ${t("overview.sources", lang)}`}
        />
      </div>

      {agriTsData && firstDataKey && agriTsData.data[firstDataKey]?.length > 1 && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {agriTsKey} — {t("env.trend", lang)}
          </h2>
          <div className="mt-4">
            <Sparkline data={agriTsData.data[firstDataKey]} color="#10b981" width={600} height={120} />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{agriTsData.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{agriTsData.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
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
