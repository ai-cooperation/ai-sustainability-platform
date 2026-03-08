"use client";

import KPICard from "@/components/KPICard";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

export default function EnergyPage() {
  const { lang } = useApp();

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("energy.subtitle", lang)}</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title={t("energy.ukCarbon", lang)} value={186} unit="gCO2/kWh" trend="down" trendValue={t("energy.lower", lang)} />
        <KPICard title={t("energy.solarRadiation", lang)} value={845} unit="W/m²" trend="up" trendValue={t("energy.peakHour", lang)} />
        <KPICard title={t("energy.windGeneration", lang)} value="28.4" unit="GW" trend="up" trendValue="+3.2 GW" />
        <KPICard title={t("energy.renewablePct", lang)} value="38.2" unit="%" trend="up" trendValue="+2.1%" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("common.dataSources", lang)}</h2>
        <div className="mt-4 space-y-2">
          {["Open-Meteo Solar", "NASA POWER", "UK Carbon Intensity", "Open Power System Data", "EIA", "Electricity Maps", "NREL"].map((s) => (
            <div key={s} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
              <span className="text-sm text-gray-700 dark:text-gray-300">{s}</span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs text-gray-500">{t("common.active", lang)}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
