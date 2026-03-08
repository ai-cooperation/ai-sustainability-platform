"use client";

import KPICard from "@/components/KPICard";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function CarbonPage() {
  const { lang } = useApp();

  const emitters = [
    { key: "carbon.china", emissions: 11.4, pct: 30.5 },
    { key: "carbon.us", emissions: 5.1, pct: 13.6 },
    { key: "carbon.india", emissions: 2.9, pct: 7.7 },
    { key: "carbon.eu27", emissions: 2.8, pct: 7.5 },
    { key: "carbon.russia", emissions: 1.8, pct: 4.8 },
    { key: "carbon.japan", emissions: 1.1, pct: 2.9 },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("carbon.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("carbon.subtitle", lang)}</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title={t("carbon.globalCo2", lang)} value="37.4" unit="Gt/yr" trend="up" trendValue="+0.8%" color="red" />
        <KPICard title={t("carbon.perCapita", lang)} value={4.7} unit="t CO2/person" trend="neutral" trendValue={t("common.stable", lang)} />
        <KPICard title={t("carbon.budgetLeft", lang)} value="~250" unit={t("carbon.budgetUnit", lang)} trend="down" trendValue={t("carbon.yearsLeft", lang)} color="red" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("carbon.topEmitters", lang)}</h2>
        <div className="mt-4 space-y-3">
          {emitters.map((c) => (
            <div key={c.key} className="flex items-center gap-4">
              <span className="w-28 text-sm text-gray-600 dark:text-gray-400">{t(c.key, lang)}</span>
              <div className="flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
                <div className="h-5 rounded-full bg-red-500 dark:bg-red-600" style={{ width: `${(c.pct / 32) * 100}%` }} />
              </div>
              <span className="w-20 text-right text-sm text-gray-700 dark:text-gray-300">{c.emissions} Gt</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
