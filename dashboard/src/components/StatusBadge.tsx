import { t, type Lang } from "@/lib/i18n";

interface StatusBadgeProps {
  status: "healthy" | "degraded" | "down" | string;
  lang?: Lang;
}

export default function StatusBadge({ status, lang = "en" }: StatusBadgeProps) {
  const colors = {
    healthy: "bg-green-500",
    degraded: "bg-yellow-500",
    down: "bg-red-500",
  };
  const bg = colors[status as keyof typeof colors] || "bg-gray-400";
  const label = t(`status.${status}`, lang);

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${bg}`} />
      <span className="text-sm">{label}</span>
    </span>
  );
}
