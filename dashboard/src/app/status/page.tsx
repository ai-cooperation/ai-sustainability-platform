"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/StatusBadge";
import { fetchStatus, type StatusReport, type ApiStatus } from "@/lib/data";

function guessDomain(name: string): string {
  const l = name.toLowerCase();
  if (l.includes("solar") || l.includes("power") || l.includes("eia") || l.includes("nrel") || l.includes("electricity") || l.includes("carbon intensity")) return "Energy";
  if (l.includes("weather") || l.includes("climate") || l.includes("ghg") || l.includes("noaa") || l.includes("copernicus") || l.includes("world bank")) return "Climate";
  if (l.includes("air") || l.includes("water") || l.includes("forest") || l.includes("emission") || l.includes("epa") || l.includes("openaq") || l.includes("aqicn")) return "Environment";
  if (l.includes("fao") || l.includes("agri") || l.includes("usda") || l.includes("gbif")) return "Agriculture";
  if (l.includes("co2") || l.includes("carbon") || l.includes("climatiq") || l.includes("owid") || l.includes("trace")) return "Carbon";
  if (l.includes("charge") || l.includes("fuel") || l.includes("transport")) return "Transport";
  return "Other";
}

export default function StatusPage() {
  const [report, setReport] = useState<StatusReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus().then((data) => {
      setReport(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Status</h1>
        <p className="mt-4 text-gray-500">Loading live status data...</p>
      </div>
    );
  }

  const apis = report
    ? report.results.map((r: ApiStatus) => ({
        name: r.name,
        domain: guessDomain(r.name),
        status: r.status,
        latency: r.latency_ms,
      }))
    : [];

  const healthy = apis.filter((a) => a.status === "healthy").length;
  const degraded = apis.filter((a) => a.status === "degraded").length;
  const down = apis.filter((a) => a.status === "down").length;
  const total = apis.length;
  const checkedAt = report?.checked_at
    ? new Date(report.checked_at).toLocaleString()
    : "N/A";

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Status</h1>
      <p className="mt-1 text-gray-500">
        Live health monitoring for {total} data sources — Last checked: {checkedAt}
      </p>

      <div className="mt-6 flex gap-4">
        <div className="rounded-lg bg-green-50 px-4 py-2 dark:bg-green-900/20">
          <span className="text-2xl font-bold text-green-600">{healthy}</span>
          <span className="ml-1 text-sm text-green-600">Healthy</span>
        </div>
        <div className="rounded-lg bg-yellow-50 px-4 py-2 dark:bg-yellow-900/20">
          <span className="text-2xl font-bold text-yellow-600">{degraded}</span>
          <span className="ml-1 text-sm text-yellow-600">Degraded</span>
        </div>
        <div className="rounded-lg bg-red-50 px-4 py-2 dark:bg-red-900/20">
          <span className="text-2xl font-bold text-red-600">{down}</span>
          <span className="ml-1 text-sm text-red-600">Down</span>
        </div>
      </div>

      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">API</th>
              <th className="px-4 py-3">Domain</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {apis.map((api) => (
              <tr key={api.name} className="text-gray-700 dark:text-gray-300">
                <td className="px-4 py-2.5 font-medium">{api.name}</td>
                <td className="px-4 py-2.5">{api.domain}</td>
                <td className="px-4 py-2.5"><StatusBadge status={api.status} /></td>
                <td className="px-4 py-2.5">{api.latency > 0 ? `${api.latency}ms` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
