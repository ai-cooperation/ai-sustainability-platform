"use client";

export default function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="rounded-lg bg-gray-200 dark:bg-gray-700 h-24" />
      ))}
    </div>
  );
}
