"use client";

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  color?: string;
}

export default function KPICard({ title, value, unit, trend, trendValue, color = "emerald" }: KPICardProps) {
  const trendIcon = trend === "up" ? "+" : trend === "down" ? "-" : "";
  const trendColor = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-500";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className={`text-3xl font-bold text-${color}-600 dark:text-${color}-400`}>{value}</p>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      {trendValue && (
        <p className={`mt-1 text-sm ${trendColor}`}>
          {trendIcon}{trendValue}
        </p>
      )}
    </div>
  );
}
