"use client";

import { useEffect, useState } from "react";
import KPICard from "@/components/KPICard";
import Sparkline from "@/components/Sparkline";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  fetchDomainData,
  fetchTaiPower,
  type DomainData,
  type TaiPowerData,
} from "@/lib/data";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";

/** Simple horizontal bar for generation mix */
function GenMixBar({ items }: { items: { label: string; mw: number; color: string }[] }) {
  const total = items.reduce((s, i) => s + i.mw, 0);
  if (total === 0) return null;
  return (
    <div className="flex h-6 w-full overflow-hidden rounded-full">
      {items.map((item) => {
        const pct = (item.mw / total) * 100;
        if (pct < 0.5) return null;
        return (
          <div
            key={item.label}
            className="flex items-center justify-center text-[10px] font-medium text-white"
            style={{ width: `${pct}%`, backgroundColor: item.color }}
            title={`${item.label}: ${item.mw.toLocaleString()} MW (${pct.toFixed(1)}%)`}
          >
            {pct > 5 ? `${pct.toFixed(0)}%` : ""}
          </div>
        );
      })}
    </div>
  );
}

/** Reserve indicator card with G/Y/O/R traffic light */
const RESERVE_COLORS: Record<string, { bg: string; text: string; label: Record<string, string> }> = {
  G: { bg: "bg-green-500", text: "text-green-700 dark:text-green-400", label: { en: "Adequate", zh: "供電充裕" } },
  Y: { bg: "bg-yellow-400", text: "text-yellow-700 dark:text-yellow-400", label: { en: "Tight", zh: "供電吃緊" } },
  O: { bg: "bg-orange-500", text: "text-orange-700 dark:text-orange-400", label: { en: "Critical", zh: "供電警戒" } },
  R: { bg: "bg-red-500", text: "text-red-700 dark:text-red-400", label: { en: "Emergency", zh: "限電警戒" } },
};

function ReserveCard({
  lang,
  indicator,
  reservePct,
  reserveMw,
  sparkData,
}: {
  lang: "en" | "zh";
  indicator: string;
  reservePct: number;
  reserveMw: number;
  sparkData: number[];
}) {
  const color = RESERVE_COLORS[indicator] ?? RESERVE_COLORS.G;
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
        {t("taipower.reserve", lang)}
      </p>
      <div className="mt-2 flex items-center gap-3">
        <span className={`inline-block h-5 w-5 rounded-full ${color.bg}`} />
        <span className={`text-2xl font-bold ${color.text}`}>
          {reservePct.toFixed(1)}%
        </span>
      </div>
      <p className="mt-1 text-xs text-gray-500">
        {reserveMw >= 10000 ? `${(reserveMw / 1000).toFixed(1)} GW` : `${reserveMw.toLocaleString()} MW`} — {color.label[lang] ?? color.label.en}
      </p>
      {sparkData.length > 1 && (
        <div className="mt-2">
          <Sparkline data={sparkData} color="#ef4444" width={200} height={32} />
        </div>
      )}
    </div>
  );
}

export default function EnergyPage() {
  const { lang } = useApp();
  const [data, setData] = useState<DomainData | null>(null);
  const [taipower, setTaipower] = useState<TaiPowerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchDomainData("energy").then(setData),
      fetchTaiPower().then(setTaipower),
    ])
      .then(() => setError(null))
      .catch(() => setError("Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  const kpis = data?.kpis ?? {};
  const sources = data?.sources ?? [];
  const ts = data?.time_series ?? {};
  const updatedAt = data?.updated_at ? new Date(data.updated_at).toLocaleString() : null;

  // TaiPower data
  const tpLatest = taipower?.latest;
  const tpTs = taipower?.time_series;
  const tpDaily = taipower?.daily_peaks ?? [];
  const tpUpdated = taipower?.updated_at ? new Date(taipower.updated_at).toLocaleString() : null;

  if (loading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-1 text-gray-500">{t("energy.subtitle", lang)}</p>
      <div className="mt-6"><LoadingSkeleton rows={4} /></div>
    </div>
  );

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-4 text-red-500">{error}</p>
    </div>
  );

  // Generation mix items for bar chart (TaiPower official colors)
  const mixItems = tpLatest ? [
    { label: t("taipower.solar", lang), mw: Number(tpLatest.solar_mw ?? 0), color: "#00CC00" },
    { label: t("taipower.wind", lang), mw: Number(tpLatest.wind_mw ?? 0), color: "#009933" },
    { label: t("taipower.hydro", lang), mw: Number(tpLatest.hydro_mw ?? 0), color: "#0000B2" },
    { label: t("taipower.lng", lang), mw: Number(tpLatest.lng_mw ?? 0) + Number(tpLatest.ipp_lng_mw ?? 0), color: "#008A20" },
    { label: t("taipower.coal", lang), mw: Number(tpLatest.coal_mw ?? 0) + Number(tpLatest.ipp_coal_mw ?? 0), color: "#E65C00" },
    { label: t("taipower.nuclear", lang), mw: Number(tpLatest.nuclear_mw ?? 0), color: "#CC0099" },
    { label: t("taipower.other", lang), mw: Number(tpLatest.oil_mw ?? 0) + Number(tpLatest.cogen_mw ?? 0) + Number(tpLatest.storage_mw ?? 0) + Number(tpLatest.other_renewable_mw ?? 0), color: "#6699FF" },
  ] : [];

  // Filter valid numbers for sparklines
  const filterNums = (arr?: (number | null)[]) => arr?.filter((v): v is number => v != null) ?? [];

  /** Format MW: show as GW if >= 10,000 MW */
  const fmtMW = (mw: number) => mw >= 10000 ? `${(mw / 1000).toFixed(1)}` : mw.toLocaleString();
  const fmtMWUnit = (mw: number) => mw >= 10000 ? "GW" : "MW";

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("energy.title", lang)}</h1>
      <p className="mt-1 text-gray-500">
        {t("energy.subtitle", lang)}
        {updatedAt && <span className="ml-2 text-xs">({updatedAt})</span>}
      </p>

      {/* TaiPower Real-time Section */}
      {tpLatest && (
        <div className="mt-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("taipower.title", lang)}
            </h2>
            {tpUpdated && (
              <span className="text-xs text-gray-400">{tpUpdated}</span>
            )}
          </div>

          {/* KPI cards row */}
          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <KPICard
              title={t("taipower.renewablePct", lang)}
              value={Number(tpLatest.renewable_pct ?? 0).toFixed(1)}
              unit="%"
              trend={Number(tpLatest.renewable_pct ?? 0) > 15 ? "up" : "down"}
              sparkData={filterNums(tpTs?.renewable_pct)}
              sparkColor="#10b981"
            />
            <KPICard
              title={t("taipower.solar", lang)}
              value={Number(tpLatest.solar_mw ?? 0).toLocaleString()}
              unit="MW"
              trend="up"
              sparkData={filterNums(tpTs?.solar_mw)}
              sparkColor="#00CC00"
            />
            <KPICard
              title={t("taipower.wind", lang)}
              value={Number(tpLatest.wind_mw ?? 0).toLocaleString()}
              unit="MW"
              trend="up"
              sparkData={filterNums(tpTs?.wind_mw)}
              sparkColor="#009933"
            />
            <KPICard
              title={t("taipower.hydro", lang)}
              value={Number(tpLatest.hydro_mw ?? 0).toLocaleString()}
              unit="MW"
              trend="neutral"
              sparkData={filterNums(tpTs?.hydro_mw)}
              sparkColor="#0000B2"
            />
            <KPICard
              title={t("taipower.totalGen", lang)}
              value={fmtMW(Number(tpLatest.total_mw ?? 0))}
              unit={fmtMWUnit(Number(tpLatest.total_mw ?? 0))}
              trend="neutral"
              sparkData={filterNums(tpTs?.total_mw)}
              sparkColor="#6b7280"
            />
            <KPICard
              title={t("taipower.load", lang)}
              value={fmtMW(Number(tpLatest.load_mw ?? 0))}
              unit={fmtMWUnit(Number(tpLatest.load_mw ?? 0))}
              trendValue={`${t("taipower.reserve", lang)}: ${Number(tpLatest.fore_reserve_pct ?? 0).toFixed(1)}%`}
              trend={Number(tpLatest.util_rate_pct ?? 0) > 90 ? "up" : "neutral"}
              sparkData={filterNums(tpTs?.load_mw)}
              sparkColor="#8b5cf6"
            />
            <ReserveCard
              lang={lang}
              indicator={String(tpLatest.reserve_indicator ?? "")}
              reservePct={Number(tpLatest.fore_reserve_pct ?? 0)}
              reserveMw={Number(tpLatest.fore_reserve_mw ?? 0)}
              sparkData={filterNums(tpTs?.fore_reserve_pct)}
            />
          </div>

          {/* Generation mix bar */}
          <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              {t("taipower.genMix", lang)}
            </h3>
            <div className="mt-3">
              <GenMixBar items={mixItems} />
            </div>
            <div className="mt-3 flex flex-wrap gap-3">
              {mixItems.filter((i) => i.mw > 0).map((item) => (
                <div key={item.label} className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.label}: {item.mw.toLocaleString()} MW
                </div>
              ))}
            </div>
          </div>

          {/* Daily peaks chart */}
          {tpDaily.length > 1 && (
            <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {t("taipower.dailyPeaks", lang)}
              </h3>
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-xs text-gray-500 mb-2">{t("taipower.solarPeak", lang)} (MW)</p>
                  <Sparkline
                    data={tpDaily.map((d) => d.solar_mw_max)}
                    color="#00CC00"
                    width={400}
                    height={80}
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                    <span>{tpDaily[0]?.date}</span>
                    <span>{tpDaily.at(-1)?.date}</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-2">{t("taipower.windPeak", lang)} (MW)</p>
                  <Sparkline
                    data={tpDaily.map((d) => d.wind_mw_max)}
                    color="#009933"
                    width={400}
                    height={80}
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                    <span>{tpDaily[0]?.date}</span>
                    <span>{tpDaily.at(-1)?.date}</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-2">{t("taipower.renewablePctPeak", lang)} (%)</p>
                  <Sparkline
                    data={tpDaily.map((d) => d.renewable_pct_max)}
                    color="#10b981"
                    width={400}
                    height={80}
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                    <span>{tpDaily[0]?.date}</span>
                    <span>{tpDaily.at(-1)?.date}</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-2">{t("taipower.totalPeak", lang)} (MW)</p>
                  <Sparkline
                    data={tpDaily.map((d) => d.total_mw_max)}
                    color="#6b7280"
                    width={400}
                    height={80}
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                    <span>{tpDaily[0]?.date}</span>
                    <span>{tpDaily.at(-1)?.date}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Original energy KPIs */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("energy.globalData", lang)}
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title={t("energy.solarRadiation", lang)}
            value={kpis.shortwave_radiation?.mean?.toFixed(0) ?? "—"}
            unit="W/m²"
            trend="up"
            trendValue={kpis.shortwave_radiation ? `max ${kpis.shortwave_radiation.max.toFixed(0)} W/m²` : ""}
            sparkData={ts.open_meteo_solar?.data?.shortwave_radiation}
            sparkForecast={ts.open_meteo_solar?.forecast?.shortwave_radiation}
            sparkColor="#f59e0b"
          />
          <KPICard
            title={t("energy.directRad", lang)}
            value={kpis.direct_radiation?.mean?.toFixed(0) ?? "—"}
            unit="W/m²"
            trend="up"
            trendValue={kpis.direct_radiation ? `max ${kpis.direct_radiation.max.toFixed(0)} W/m²` : ""}
            sparkData={ts.open_meteo_solar?.data?.direct_radiation}
            sparkForecast={ts.open_meteo_solar?.forecast?.direct_radiation}
            sparkColor="#10b981"
          />
          <KPICard
            title={t("energy.nasaSolar", lang)}
            value={kpis.solar_radiation?.mean?.toFixed(2) ?? "—"}
            unit="kWh/m²/day"
            trend="neutral"
            trendValue="NASA POWER"
            sparkData={ts.nasa_power?.data?.solar_radiation}
            sparkColor="#6366f1"
          />
          <KPICard
            title={t("kpi.carbonIntensity", lang)}
            value={kpis.intensity_forecast?.latest?.toFixed(0) ?? "—"}
            unit="gCO₂/kWh"
            trend={kpis.intensity_forecast && kpis.intensity_forecast.latest < kpis.intensity_forecast.mean ? "down" : "neutral"}
            trendValue=""
            sparkColor="#ef4444"
          />
        </div>
      </div>

      {ts.open_meteo_solar?.data?.shortwave_radiation && (
        <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("energy.solarRadiation", lang)} — {t("spark.range.7d+7d", lang)}
          </h2>
          <div className="mt-4">
            <Sparkline
              data={ts.open_meteo_solar.data.shortwave_radiation}
              forecastData={ts.open_meteo_solar.forecast?.shortwave_radiation}
              color="#f59e0b"
              width={600}
              height={120}
            />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{ts.open_meteo_solar.timestamps[0]?.split("T")[0] ?? ""}</span>
            <span>{ts.open_meteo_solar.timestamps.at(-1)?.split("T")[0] ?? ""}</span>
          </div>
        </div>
      )}

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("common.dataSources", lang)} ({data?.record_count?.toLocaleString() ?? 0} {t("common.records", lang)})
        </h2>
        <div className="mt-4 space-y-2">
          {sources.map((s) => (
            <div key={s} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
              <span className="text-sm text-gray-700 dark:text-gray-300">{t(`api.${s}.name`, lang)}</span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs text-gray-500">{ts[s]?.timestamps?.length ?? 0} pts</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
