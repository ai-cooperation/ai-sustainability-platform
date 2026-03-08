"use client";

import { useEffect, useState } from "react";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";
import { fetchForecasts, type ForecastResult } from "@/lib/data";

export default function ForecastsPage() {
  const { lang } = useApp();
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);

  useEffect(() => {
    fetchForecasts().then(setForecasts);
  }, []);

  const agents = [
    { nameKey: "forecast.optimist", prob: "25%", reasonKey: "forecast.optimistReason", color: "green" },
    { nameKey: "forecast.pessimist", prob: "72%", reasonKey: "forecast.pessimistReason", color: "red" },
    { nameKey: "forecast.statistician", prob: "48%", reasonKey: "forecast.statisticianReason", color: "blue" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("forecast.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("forecast.subtitle", lang)}</p>

      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("forecast.latest", lang)}</h2>

        {forecasts && forecasts.length > 0 ? (
          <div className="mt-4 space-y-4">
            {forecasts.map((f, i) => (
              <div key={i} className="rounded-lg bg-emerald-50 p-4 dark:bg-emerald-900/20">
                <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">{f.question}</p>
                <p className="mt-2 text-3xl font-bold text-emerald-700 dark:text-emerald-400">
                  {Math.round(f.probability * 100)}% {t("forecast.probability", lang)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  {t("forecast.confidence", lang)}: {f.confidence} | {f.positions.length} {t("overview.agents", lang)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-lg bg-emerald-50 p-4 dark:bg-emerald-900/20">
            <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
              {t("forecast.question1", lang)}
            </p>
            <p className="mt-2 text-3xl font-bold text-emerald-700 dark:text-emerald-400">
              45% {t("forecast.probability", lang)}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {t("forecast.confidence", lang)}: {t("forecast.medium", lang)} | {t("forecast.agentSources", lang)}
            </p>
          </div>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("forecast.agentDebate", lang)}</h2>
        <div className="mt-4 space-y-4">
          {agents.map((a) => (
            <div key={a.nameKey} className={`rounded-lg border-l-4 border-${a.color}-500 bg-gray-50 p-4 dark:bg-gray-700`}>
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900 dark:text-white">{t(a.nameKey, lang)}</span>
                <span className={`text-lg font-bold text-${a.color}-600 dark:text-${a.color}-400`}>{a.prob}</span>
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{t(a.reasonKey, lang)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
