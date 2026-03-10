"use client";

import { useEffect, useMemo, useState } from "react";
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

type SortCol = "name" | "domain" | "status" | "latency";
type SortDir = "asc" | "desc";
type StatusFilter = "all" | "healthy" | "degraded" | "down";

const DOMAINS = [
  "all",
  "energy",
  "climate",
  "environment",
  "agriculture",
  "carbon",
  "transport",
] as const;

const STATUS_ORDER: Record<string, number> = {
  down: 0,
  degraded: 1,
  healthy: 2,
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
  const [error, setError] = useState<string | null>(null);
  const [selectedApi, setSelectedApi] = useState<string | null>(null);
  const [sortCol, setSortCol] = useState<SortCol>("status");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterDomain, setFilterDomain] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<StatusFilter>("all");

  useEffect(() => {
    Promise.all([fetchStatus(), fetchRecentHistory(3)])
      .then(([s, h]) => {
        setReport(s);
        setHistory(h);
        if (!s) setError("Failed to load status data");
      })
      .catch(() => setError("Failed to load status data"))
      .finally(() => setLoading(false));
  }, []);

  const apis = report?.apis ?? [];
  const healthy = report?.healthy ?? 0;
  const degraded = report?.degraded ?? 0;
  const down = report?.down ?? 0;
  const total = report?.total ?? 0;
  const checkedAt = report?.checked_at
    ? new Date(report.checked_at).toLocaleString()
    : "N/A";

  const statusCounts = useMemo(() => {
    const counts = { all: apis.length, healthy: 0, degraded: 0, down: 0 };
    for (const api of apis) {
      if (api.status in counts) {
        counts[api.status as "healthy" | "degraded" | "down"] += 1;
      }
    }
    return counts;
  }, [apis]);

  const filteredSortedApis = useMemo(() => {
    const filtered = apis.filter((api) => {
      const domainMatch =
        filterDomain === "all" || api.domain === filterDomain;
      const statusMatch =
        filterStatus === "all" || api.status === filterStatus;
      return domainMatch && statusMatch;
    });

    return [...filtered].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      switch (sortCol) {
        case "name":
          return dir * a.id.localeCompare(b.id);
        case "domain":
          return dir * a.domain.localeCompare(b.domain);
        case "status":
          return (
            dir *
            ((STATUS_ORDER[a.status] ?? 99) - (STATUS_ORDER[b.status] ?? 99))
          );
        case "latency":
          return dir * (a.latency_ms - b.latency_ms);
        default:
          return 0;
      }
    });
  }, [apis, filterDomain, filterStatus, sortCol, sortDir]);

  const handleSort = (col: SortCol) => {
    if (sortCol === col) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  };

  const sortArrow = (col: SortCol) => {
    if (sortCol !== col) return null;
    return <span className="ml-1">{sortDir === "asc" ? "▲" : "▼"}</span>;
  };

  const statusFilterItems: {
    key: StatusFilter;
    label: string;
    count: number;
    activeColor: string;
  }[] = [
    {
      key: "all",
      label: t("status.filterAll", lang),
      count: statusCounts.all,
      activeColor:
        "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    },
    {
      key: "healthy",
      label: t("status.healthy", lang),
      count: statusCounts.healthy,
      activeColor:
        "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
    },
    {
      key: "degraded",
      label: t("status.degraded", lang),
      count: statusCounts.degraded,
      activeColor:
        "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
    },
    {
      key: "down",
      label: t("status.down", lang),
      count: statusCounts.down,
      activeColor:
        "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    },
  ];

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

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("status.title", lang)}
        </h1>
        <p className="mt-4 text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("status.title", lang)}
      </h1>
      <p className="mt-1 text-gray-500">
        {t("status.subtitle", lang, { count: total })} —{" "}
        {t("status.lastChecked", lang)}: {checkedAt}
      </p>

      {/* Summary badges */}
      <div className="mt-6 flex flex-wrap gap-4">
        <div className="rounded-lg bg-green-50 px-4 py-2 dark:bg-green-900/20">
          <span className="text-2xl font-bold text-green-600">{healthy}</span>
          <span className="ml-1 text-sm text-green-600">
            {t("status.healthy", lang)}
          </span>
        </div>
        <div className="rounded-lg bg-yellow-50 px-4 py-2 dark:bg-yellow-900/20">
          <span className="text-2xl font-bold text-yellow-600">{degraded}</span>
          <span className="ml-1 text-sm text-yellow-600">
            {t("status.degraded", lang)}
          </span>
        </div>
        <div className="rounded-lg bg-red-50 px-4 py-2 dark:bg-red-900/20">
          <span className="text-2xl font-bold text-red-600">{down}</span>
          <span className="ml-1 text-sm text-red-600">
            {t("status.down", lang)}
          </span>
        </div>
      </div>

      {/* Domain filter pills */}
      <div className="mt-6 flex flex-wrap gap-2">
        {DOMAINS.map((domain) => {
          const isActive = filterDomain === domain;
          const label =
            domain === "all"
              ? t("domain.all", lang)
              : formatDomain(domain, lang);
          return (
            <button
              key={domain}
              onClick={() => setFilterDomain(domain)}
              className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-emerald-500 text-white dark:bg-emerald-600"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Status filter */}
      <div className="mt-3 flex flex-wrap gap-2">
        {statusFilterItems.map((item) => {
          const isActive = filterStatus === item.key;
          return (
            <button
              key={item.key}
              onClick={() => setFilterStatus(item.key)}
              className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                isActive
                  ? item.activeColor
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              {item.label} ({item.count})
            </button>
          );
        })}
      </div>

      {/* Detail table with integrated history */}
      <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th
                className="cursor-pointer select-none px-4 py-3 hover:text-gray-700 dark:hover:text-gray-200"
                onClick={() => handleSort("name")}
              >
                {t("status.api", lang)}
                {sortArrow("name")}
              </th>
              <th
                className="cursor-pointer select-none px-4 py-3 hover:text-gray-700 dark:hover:text-gray-200"
                onClick={() => handleSort("domain")}
              >
                {t("status.domain", lang)}
                {sortArrow("domain")}
              </th>
              <th
                className="cursor-pointer select-none px-4 py-3 hover:text-gray-700 dark:hover:text-gray-200"
                onClick={() => handleSort("status")}
              >
                {t("status.statusCol", lang)}
                {sortArrow("status")}
              </th>
              <th
                className="cursor-pointer select-none px-4 py-3 hover:text-gray-700 dark:hover:text-gray-200"
                onClick={() => handleSort("latency")}
              >
                {t("status.latency", lang)}
                {sortArrow("latency")}
              </th>
              {history.length > 0 && (
                <th className="px-4 py-3">{t("status.history", lang)}</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {filteredSortedApis.map((api: ApiStatus) => (
              <tr key={api.id} className="text-gray-700 dark:text-gray-300">
                <td className="px-4 py-2.5">
                  <button
                    onClick={() => setSelectedApi(api.id)}
                    className="text-left font-medium text-emerald-600 underline decoration-dotted hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                  >
                    {t(`api.${api.id}.name`, lang)}
                  </button>
                </td>
                <td className="px-4 py-2.5">
                  {formatDomain(api.domain, lang)}
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={api.status} lang={lang} />
                </td>
                <td className="px-4 py-2.5">
                  {api.latency_ms > 0 ? `${api.latency_ms}ms` : "\u2014"}
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
