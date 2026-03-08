"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import {
  fetchStatus,
  fetchForecasts,
  type StatusReport,
  type ForecastResult,
} from "@/lib/data";

export default function Overview() {
  const [status, setStatus] = useState<StatusReport | null>(null);
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);

  useEffect(() => {
    fetchStatus().then(setStatus);
    fetchForecasts().then(setForecasts);
  }, []);

  const healthy = status?.healthy ?? 29;
  const total = status?.total ?? 31;
  const statusLabel = status
    ? `${status.degraded} degraded, ${status.down} down`
    : "Loading...";

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        AI Sustainability Intelligence Platform
      </h1>
      <p className="mt-1 text-gray-500">
        Real-time monitoring across {total} global data sources
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title="Global CO2 Emissions"
          value="37.4"
          unit="Gt/yr"
          trend="up"
          trendValue="+0.8%"
          color="red"
        />
        <KPICard
          title="Renewable Share"
          value="30.1"
          unit="%"
          trend="up"
          trendValue="+2.3%"
        />
        <KPICard
          title="Global Avg AQI"
          value={42}
          unit="Good"
          trend="down"
          trendValue="-3%"
        />
        <KPICard
          title="UK Carbon Intensity"
          value={186}
          unit="gCO2/kWh"
          trend="down"
          trendValue="-12%"
        />
        <KPICard
          title="API Health"
          value={`${healthy}/${total}`}
          unit="Online"
          trend="neutral"
          trendValue={statusLabel}
        />
        <KPICard
          title="Forecast Accuracy"
          value="78"
          unit="%"
          trend="up"
          trendValue="+5%"
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Platform Status
          </h2>
          <div className="mt-4 space-y-3">
            {[
              { domain: "Energy", sources: 7 },
              { domain: "Climate", sources: 6 },
              { domain: "Environment", sources: 7 },
              { domain: "Agriculture", sources: 4 },
              { domain: "Carbon", sources: 5 },
              { domain: "Transport", sources: 2 },
            ].map((d) => (
              <div
                key={d.domain}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3 dark:bg-gray-700"
              >
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {d.domain}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    {d.sources} sources
                  </span>
                </div>
                <span className="text-sm font-medium text-green-600">
                  {status ? "Live" : "Loading..."}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Latest AI Forecast
          </h2>
          {forecasts && forecasts.length > 0 ? (
            forecasts.slice(0, 2).map((f, i) => (
              <div
                key={i}
                className={`mt-4 rounded-lg p-4 ${
                  i === 0
                    ? "bg-emerald-50 dark:bg-emerald-900/20"
                    : "bg-blue-50 dark:bg-blue-900/20"
                }`}
              >
                <p
                  className={`text-sm font-medium ${
                    i === 0
                      ? "text-emerald-800 dark:text-emerald-300"
                      : "text-blue-800 dark:text-blue-300"
                  }`}
                >
                  {f.question}
                </p>
                <p
                  className={`mt-2 text-3xl font-bold ${
                    i === 0
                      ? "text-emerald-700 dark:text-emerald-400"
                      : "text-blue-700 dark:text-blue-400"
                  }`}
                >
                  {Math.round(f.probability * 100)}% probability
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Confidence: {f.confidence} | {f.positions.length} agents
                </p>
              </div>
            ))
          ) : (
            <div className="mt-4 rounded-lg bg-emerald-50 p-4 dark:bg-emerald-900/20">
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                Will UK grid carbon intensity exceed 200g CO2/kWh in the next 7 days?
              </p>
              <p className="mt-2 text-3xl font-bold text-emerald-700 dark:text-emerald-400">
                Awaiting first forecast run
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Weekly forecast runs every Monday via GitHub Actions
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
