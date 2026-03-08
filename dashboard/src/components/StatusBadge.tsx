interface StatusBadgeProps {
  status: "healthy" | "degraded" | "down" | string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors = {
    healthy: "bg-green-500",
    degraded: "bg-yellow-500",
    down: "bg-red-500",
  };
  const bg = colors[status as keyof typeof colors] || "bg-gray-400";

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${bg}`} />
      <span className="text-sm capitalize">{status}</span>
    </span>
  );
}
