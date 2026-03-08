import KPICard from "@/components/KPICard";

export default function ClimatePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Climate Dashboard</h1>
      <p className="mt-1 text-gray-500">6 data sources: Weather, GHG Concentrations, Climate Projections</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title="Atmospheric CO2" value="427.3" unit="ppm" trend="up" trendValue="+2.1 ppm/yr" color="red" />
        <KPICard title="Methane (CH4)" value="1923" unit="ppb" trend="up" trendValue="+12 ppb/yr" color="red" />
        <KPICard title="Temp Anomaly" value="+1.45" unit="°C vs pre-industrial" trend="up" trendValue="+0.03°C" color="red" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">CO2 Concentration Trend (Mauna Loa)</h2>
        <div className="mt-4 flex h-48 items-end gap-1">
          {[380,382,385,388,391,394,397,400,404,407,410,413,416,419,422,425,427].map((v, i) => (
            <div key={i} className="flex-1 rounded-t bg-emerald-500 dark:bg-emerald-600" style={{ height: `${((v - 375) / 55) * 100}%` }} title={`${2008 + i}: ${v} ppm`} />
          ))}
        </div>
        <div className="mt-1 flex justify-between text-xs text-gray-400">
          <span>2008</span><span>2024</span>
        </div>
      </div>
    </div>
  );
}
