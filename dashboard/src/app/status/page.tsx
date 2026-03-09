"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/StatusBadge";
import ApiDetailModal from "@/components/ApiDetailModal";
import {
  fetchStatus,
  fetchRecentHistory,
  type StatusReport,
  type ApiStatus,
  type HistoryEntry,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

function formatDomain(domain: string, lang: "en" | "zh"): string {
  return t(`domain.${domain}`, lang) || domain;
}

const statusColor: Record<string, string> = {
  healthy: "bg-green-500",
  degraded: "bg-yellow-500",
  down: "bg-red-500",
};

function HistoryDots({
  apiId,
  history,
}: {
  apiId: string;
  history: HistoryEntry[];
}) {
  return (
    <div className="flex items-center gap-0.5">
      {history.map((h, i) => {
        const api = h.apis.find((a) => a.id === apiId);
        const status = api?.status ?? "unknown";
        const time = new Date(h.checked_at).toLocaleString([], {
          month: "numeric",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
        return (
          <span
            key={i}
            title={`${time}: ${status}`}
            className={`inline-block h-3 w-3 rounded-full ${
              statusColor[status] ?? "bg-gray-300 dark:bg-gray-600"
            }`}
          />
        );
      })}
    </div>
  );
}

export default function StatusPage() {
  const { lang } = useApp();
  const [report, setReport] = useState<StatusReport | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApi, setSelectedApi] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchStatus(), fetchRecentHistory(3)]).then(([s, h]) => {
      setReport(s);
      setHistory(h);
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

      {/* Detail table with integrated history */}
      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">{t("status.api", lang)}</th>
              <th className="px-4 py-3">{t("status.domain", lang)}</th>
              <th className="px-4 py-3">{t("status.statusCol", lang)}</th>
              <th className="px-4 py-3">{t("status.latency", lang)}</th>
              {history.length > 0 && (
                <th className="px-4 py-3">{t("status.history", lang)}</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {apis.map((api: ApiStatus) => (
              <tr key={api.id} className="text-gray-700 dark:text-gray-300">
                <td className="px-4 py-2.5">
                  <button
                    onClick={() => setSelectedApi(api.id)}
                    className="text-left font-medium text-emerald-600 underline decoration-dotted hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                  >
                    {t(`api.${api.id}.name`, lang)}
                  </button>
                </td>
                <td className="px-4 py-2.5">{formatDomain(api.domain, lang)}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={api.status} lang={lang} />
                </td>
                <td className="px-4 py-2.5">
                  {api.latency_ms > 0 ? `${api.latency_ms}ms` : "—"}
                </td>
                {history.length > 0 && (
                  <td className="px-4 py-2.5">
                    <HistoryDots apiId={api.id} history={history} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedApi && (
        <ApiDetailModal
          apiId={selectedApi}
          lang={lang}
          onClose={() => setSelectedApi(null)}
        />
      )}
    </div>
  );
}
