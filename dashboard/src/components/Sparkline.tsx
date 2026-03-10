import { useId } from "react";

interface SparklineProps {
  data: number[];
  forecastData?: number[];
  color?: string;
  height?: number;
  width?: number;
}

export default function Sparkline({
  data,
  forecastData,
  color = "#10b981",
  height = 40,
  width = 120,
}: SparklineProps) {
  const gradId = useId();

  if (data.length < 2) return null;

  // Combine data for unified scale calculation
  const allValues = forecastData ? [...data, ...forecastData] : data;
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || 1;
  const padding = 2;
  const innerH = height - padding * 2;
  const totalLen = allValues.length;
  const innerW = width - padding * 2;

  const toPoint = (v: number, i: number) => {
    const x = padding + (i / (totalLen - 1)) * innerW;
    const y = padding + innerH - ((v - min) / range) * innerH;
    return { x, y };
  };

  // Historical points
  const histPoints = data.map((v, i) => toPoint(v, i));
  const histStr = histPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Last historical point (current value indicator)
  const lastHist = histPoints[histPoints.length - 1];

  // Area fill under historical line
  const areaPoints = [
    `${padding},${height - padding}`,
    ...histPoints.map((p) => `${p.x},${p.y}`),
    `${lastHist.x},${height - padding}`,
  ].join(" ");

  // Forecast points (starts from last historical point for continuity)
  let forecastStr = "";
  let lastForecast: { x: number; y: number } | null = null;
  if (forecastData && forecastData.length > 0) {
    const fcPoints = forecastData.map((v, i) => toPoint(v, data.length + i));
    // Connect from last historical point
    const allFcPoints = [lastHist, ...fcPoints];
    forecastStr = allFcPoints.map((p) => `${p.x},${p.y}`).join(" ");
    lastForecast = fcPoints[fcPoints.length - 1];
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full overflow-visible"
      style={{ height }}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.25} />
          <stop offset="100%" stopColor={color} stopOpacity={0.02} />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradId})`} />
      <polyline
        points={histStr}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {forecastStr && (
        <>
          {/* Divider line at boundary */}
          <line
            x1={lastHist.x}
            y1={padding}
            x2={lastHist.x}
            y2={height - padding}
            stroke={color}
            strokeWidth={0.5}
            strokeOpacity={0.3}
          />
          {/* Forecast dashed line */}
          <polyline
            points={forecastStr}
            fill="none"
            stroke={color}
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="3 2"
            strokeOpacity={0.6}
          />
        </>
      )}
      <circle cx={lastHist.x} cy={lastHist.y} r={3} fill={color} />
      {lastForecast && (
        <circle
          cx={lastForecast.x}
          cy={lastForecast.y}
          r={2.5}
          fill="none"
          stroke={color}
          strokeWidth={1}
          strokeOpacity={0.6}
        />
      )}
    </svg>
  );
}
