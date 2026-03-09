"use client";

import { useEffect, useState } from "react";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";
import { fetchForecasts, type ForecastResult } from "@/lib/data";

const FORECAST_COLORS = [
  { bg: "bg-emerald-50 dark:bg-emerald-900/20", text: "text-emerald-800 dark:text-emerald-300", num: "text-emerald-700 dark:text-emerald-400" },
  { bg: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-800 dark:text-blue-300", num: "text-blue-700 dark:text-blue-400" },
  { bg: "bg-amber-50 dark:bg-amber-900/20", text: "text-amber-800 dark:text-amber-300", num: "text-amber-700 dark:text-amber-400" },
];

const AGENT_BORDER: Record<string, string> = {
  Optimist: "border-green-500",
  Pessimist: "border-red-500",
  Statistician: "border-blue-500",
};

const AGENT_NUM: Record<string, string> = {
  Optimist: "text-green-600 dark:text-green-400",
  Pessimist: "text-red-600 dark:text-red-400",
  Statistician: "text-blue-600 dark:text-blue-400",
};

export default function ForecastsPage() {
  const { lang } = useApp();
  const [forecasts, setForecasts] = useState<ForecastResult[] | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    fetchForecasts().then(setForecasts);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("forecast.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("forecast.subtitle", lang)}</p>

      {forecasts && forecasts.length > 0 ? (
        <div className="mt-6 space-y-6">
          {forecasts.map((f, i) => {
            const c = FORECAST_COLORS[i % FORECAST_COLORS.length];
            const isExpanded = expanded === i;
            return (
              <div key={i} className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
                <div className={`rounded-lg p-4 ${c.bg}`}>
                  <p className={`text-sm font-medium ${c.text}`}>{f.question}</p>
                  <p className={`mt-2 text-3xl font-bold ${c.num}`}>
                    {Math.round(f.probability * 100)}% {t("forecast.probability", lang)}
                  </p>
                  <p className="mt-1 text-sm text-gray-500">
                    {t("forecast.confidence", lang)}: {f.confidence} | {f.positions.length} {t("overview.agents", lang)}
                    {f.created_at && (
                      <span className="ml-2">| {new Date(f.created_at).toLocaleString()}</span>
                    )}
                  </p>
                </div>

                <button
                  onClick={() => setExpanded(isExpanded ? null : i)}
                  className="mt-3 text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                >
                  {isExpanded ? "▲ " + t("forecast.agentDebate", lang) : "▼ " + t("forecast.agentDebate", lang)}
                </button>

                {isExpanded && f.positions.length > 0 && (
                  <div className="mt-4 space-y-3">
                    {f.positions.map((p, j) => (
                      <div key={j} className={`rounded-lg border-l-4 ${AGENT_BORDER[p.agent] ?? "border-gray-500"} bg-gray-50 p-4 dark:bg-gray-700`}>
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 dark:text-white">{p.agent}</span>
                          <span className={`text-lg font-bold ${AGENT_NUM[p.agent] ?? "text-gray-600"}`}>
                            {Math.round(p.probability * 100)}%
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                          {p.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-gray-400">{t("overview.forecastSchedule", lang)}</p>
        </div>
      )}
    </div>
  );
}
