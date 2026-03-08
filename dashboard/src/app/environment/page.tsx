import KPICard from "@/components/KPICard";

export default function EnvironmentPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Environment Dashboard</h1>
      <p className="mt-1 text-gray-500">7 data sources: Air Quality, Water, Emissions, Forests</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Global Avg AQI" value={42} unit="Good" trend="down" trendValue="3% better" />
        <KPICard title="PM2.5 Level" value={12.3} unit="µg/m³" trend="down" trendValue="-1.2" />
        <KPICard title="NO2 Satellite" value={8.7} unit="µmol/m²" trend="down" trendValue="-5%" />
        <KPICard title="Forest Loss" value="3.7M" unit="ha/yr" trend="down" trendValue="-12%" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Air Quality by Region</h2>
        <div className="mt-4 space-y-3">
          {[
            { region: "North America", aqi: 35, color: "bg-green-500" },
            { region: "Europe", aqi: 42, color: "bg-green-500" },
            { region: "East Asia", aqi: 78, color: "bg-yellow-500" },
            { region: "South Asia", aqi: 142, color: "bg-red-500" },
            { region: "Africa", aqi: 56, color: "bg-yellow-500" },
          ].map((r) => (
            <div key={r.region} className="flex items-center gap-4">
              <span className="w-32 text-sm text-gray-600 dark:text-gray-400">{r.region}</span>
              <div className="flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
                <div className={`h-4 rounded-full ${r.color}`} style={{ width: `${Math.min(r.aqi / 2, 100)}%` }} />
              </div>
              <span className="w-12 text-right text-sm font-medium text-gray-700 dark:text-gray-300">{r.aqi}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
