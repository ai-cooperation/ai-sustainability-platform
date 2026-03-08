"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/StatusBadge";
import {
  fetchStatus,
  fetchHistory,
  type StatusReport,
  type ApiStatus,
  type HistoryEntry,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

function formatDomain(domain: string, lang: "en" | "zh"): string {
  return t(`domain.${domain}`, lang) || domain;
}

export default function StatusPage() {
  const { lang } = useApp();
  const [report, setReport] = useState<StatusReport | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date().toISOString().split("T")[0];
    Promise.all([fetchStatus(), fetchHistory(today)]).then(([s, h]) => {
      setReport(s);
      setHistory(h ?? []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("status.title", lang)}
        </h1>
        <p className="mt-4 text-gray-500">{t("overview.loading", lang)}</p>
      </div>
    );
  }

  const apis = report?.apis ?? [];
  const healthy = report?.healthy ?? 0;
  const degraded = report?.degraded ?? 0;
  const down = report?.down ?? 0;
  const total = report?.total ?? 0;
  const checkedAt = report?.checked_at
    ? new Date(report.checked_at).toLocaleString()
    : "N/A";

  // Build matrix: rows = API names, cols = check timestamps
  const checkTimes = history.map((h) => {
    const d = new Date(h.checked_at);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  });

  const allApiIds = apis.map((a) => a.id);
  const matrixData: Record<string, string[]> = {};
  for (const apiId of allApiIds) {
    matrixData[apiId] = history.map((h) => {
      const found = h.apis.find((a) => a.id === apiId);
      return found?.status ?? "unknown";
    });
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("status.title", lang)}
      </h1>
      <p className="mt-1 text-gray-500">
        {t("status.subtitle", lang, { count: total })} — {t("status.lastChecked", lang)}: {checkedAt}
      </p>

      {/* Summary badges */}
      <div className="mt-6 flex gap-4">
        <div className="rounded-lg bg-green-50 px-4 py-2 dark:bg-green-900/20">
          <span className="text-2xl font-bold text-green-600">{healthy}</span>
          <span className="ml-1 text-sm text-green-600">{t("status.healthy", lang)}</span>
        </div>
        <div className="rounded-lg bg-yellow-50 px-4 py-2 dark:bg-yellow-900/20">
          <span className="text-2xl font-bold text-yellow-600">{degraded}</span>
          <span className="ml-1 text-sm text-yellow-600">{t("status.degraded", lang)}</span>
        </div>
        <div className="rounded-lg bg-red-50 px-4 py-2 dark:bg-red-900/20">
          <span className="text-2xl font-bold text-red-600">{down}</span>
          <span className="ml-1 text-sm text-red-600">{t("status.down", lang)}</span>
        </div>
      </div>

      {/* Status Matrix */}
      {history.length > 0 && (
        <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            {t("status.matrix", lang)}
          </h2>
          <div className="overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="sticky left-0 bg-white px-2 py-1 text-left text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {t("status.api", lang)}
                  </th>
                  {checkTimes.map((time, i) => (
                    <th key={i} className="px-2 py-1 text-center text-gray-500 dark:text-gray-400">
                      {time}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allApiIds.map((apiId) => (
                  <tr key={apiId}>
                    <td className="sticky left-0 bg-white px-2 py-1 font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                      {apiId}
                    </td>
                    {(matrixData[apiId] ?? []).map((status, i) => (
                      <td key={i} className="px-2 py-1 text-center">
                        <span
                          className={`inline-block h-4 w-4 rounded-full ${
                            status === "healthy"
                              ? "bg-green-500"
                              : status === "degraded"
                                ? "bg-yellow-500"
                                : status === "down"
                                  ? "bg-red-500"
                                  : "bg-gray-300 dark:bg-gray-600"
                          }`}
                          title={`${apiId}: ${status}`}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail table */}
      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">{t("status.api", lang)}</th>
              <th className="px-4 py-3">{t("status.domain", lang)}</th>
              <th className="px-4 py-3">{t("status.healthy", lang)}</th>
              <th className="px-4 py-3">{t("status.latency", lang)}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {apis.map((api: ApiStatus) => (
              <tr key={api.id} className="text-gray-700 dark:text-gray-300">
                <td className="px-4 py-2.5 font-medium">{api.id}</td>
                <td className="px-4 py-2.5">{formatDomain(api.domain, lang)}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={api.status} />
                </td>
                <td className="px-4 py-2.5">
                  {api.latency_ms > 0 ? `${api.latency_ms}ms` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
