"use client";

import Sparkline from "@/components/Sparkline";

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  color?: string;
  sparkData?: number[];
  sparkForecast?: number[];
  sparkColor?: string;
  sparkLabel?: string;
  sparkRange?: string;
}

export default function KPICard({
  title,
  value,
  unit,
  trend,
  trendValue,
  color = "emerald",
  sparkData,
  sparkForecast,
  sparkColor,
  sparkLabel,
  sparkRange,
}: KPICardProps) {
  const trendColor =
    trend === "up"
      ? "text-green-600 dark:text-green-400"
      : trend === "down"
        ? "text-red-500 dark:text-red-400"
        : "text-gray-500 dark:text-gray-400";

  const defaultSparkColor =
    trend === "down" ? "#ef4444" : trend === "up" ? "#10b981" : "#6b7280";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className={`text-3xl font-bold text-${color}-600 dark:text-${color}-400`}>{value}</p>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      {trendValue && (
        <p className={`mt-1 text-sm ${trendColor}`}>{trendValue}</p>
      )}
      {sparkData && sparkData.length > 1 && (
        <div className="mt-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex-1 min-w-0">
              <Sparkline
                data={sparkData}
                forecastData={sparkForecast}
                color={sparkColor ?? defaultSparkColor}
                width={280}
                height={72}
              />
            </div>
            <div className="shrink-0 text-right">
              {sparkLabel && (
                <span className="block text-[11px] text-gray-400">{sparkLabel}</span>
              )}
              {sparkRange && (
                <span className="block text-[11px] text-gray-400 dark:text-gray-500">{sparkRange}</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
