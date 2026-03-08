"use client";

import KPICard from "@/components/KPICard";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function AgriculturePage() {
  const { lang } = useApp();

  const countries = [
    { key: "agri.china", w: "138", r: "212", m: "289" },
    { key: "agri.india", w: "110", r: "195", m: "36" },
    { key: "agri.usa", w: "49", r: "7", m: "384" },
    { key: "agri.brazil", w: "11", r: "12", m: "132" },
    { key: "agri.eu", w: "132", r: "3", m: "62" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("agri.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("agri.subtitle", lang)}</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title={t("agri.wheatYield", lang)} value={3.52} unit="t/ha" trend="up" trendValue="+1.2%" />
        <KPICard title={t("agri.riceProduction", lang)} value="523M" unit={t("agri.tonnes", lang)} trend="up" trendValue="+0.8%" />
        <KPICard title={t("agri.foodPriceIndex", lang)} value={118.5} unit="(2015=100)" trend="down" trendValue="-3.2%" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("agri.topProducers", lang)}</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
              <tr>
                <th className="px-4 py-2">{t("common.country", lang)}</th>
                <th className="px-4 py-2">{t("agri.wheat", lang)}</th>
                <th className="px-4 py-2">{t("agri.rice", lang)}</th>
                <th className="px-4 py-2">{t("agri.corn", lang)}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
              {countries.map((c) => (
                <tr key={c.key} className="text-gray-700 dark:text-gray-300">
                  <td className="px-4 py-2 font-medium">{t(c.key, lang)}</td>
                  <td className="px-4 py-2">{c.w}</td>
                  <td className="px-4 py-2">{c.r}</td>
                  <td className="px-4 py-2">{c.m}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
