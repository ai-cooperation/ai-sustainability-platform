"use client";

import KPICard from "@/components/KPICard";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function EnvironmentPage() {
  const { lang } = useApp();

  const regions = [
    { key: "env.northAmerica", aqi: 35, color: "bg-green-500" },
    { key: "env.europe", aqi: 42, color: "bg-green-500" },
    { key: "env.eastAsia", aqi: 78, color: "bg-yellow-500" },
    { key: "env.southAsia", aqi: 142, color: "bg-red-500" },
    { key: "env.africa", aqi: 56, color: "bg-yellow-500" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("env.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("env.subtitle", lang)}</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title={t("env.aqi", lang)} value={42} unit={t("env.good", lang)} trend="down" trendValue={t("env.better", lang)} />
        <KPICard title={t("env.pm25", lang)} value={12.3} unit="µg/m³" trend="down" trendValue="-1.2" />
        <KPICard title={t("env.no2", lang)} value={8.7} unit="µmol/m²" trend="down" trendValue="-5%" />
        <KPICard title={t("env.forestLoss", lang)} value="3.7M" unit="ha/yr" trend="down" trendValue="-12%" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("env.aqByRegion", lang)}</h2>
        <div className="mt-4 space-y-3">
          {regions.map((r) => (
            <div key={r.key} className="flex items-center gap-4">
              <span className="w-32 text-sm text-gray-600 dark:text-gray-400">{t(r.key, lang)}</span>
              <div className="flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
                <div className={`h-4 rounded-full ${r.color}`} style={{ width: `${Math.min(r.aqi / 2, 100)}%` }} />
              </div>
              <span className="w-12 text-right text-sm font-medium text-gray-700 dark:text-gray-300">{r.aqi}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
