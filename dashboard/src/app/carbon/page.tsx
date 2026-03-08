import KPICard from "@/components/KPICard";

export default function CarbonPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Carbon Emissions Dashboard</h1>
      <p className="mt-1 text-gray-500">5 data sources: OWID, Climate Watch, Climate TRACE, Climatiq</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title="Global CO2 Emissions" value="37.4" unit="Gt/yr" trend="up" trendValue="+0.8%" color="red" />
        <KPICard title="Per Capita (World)" value={4.7} unit="t CO2/person" trend="neutral" trendValue="Stable" />
        <KPICard title="Carbon Budget Left" value="~250" unit="Gt CO2 (1.5°C)" trend="down" trendValue="~7 years at current rate" color="red" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Top Emitters</h2>
        <div className="mt-4 space-y-3">
          {[
            { country: "China", emissions: 11.4, pct: 30.5 },
            { country: "United States", emissions: 5.1, pct: 13.6 },
            { country: "India", emissions: 2.9, pct: 7.7 },
            { country: "EU-27", emissions: 2.8, pct: 7.5 },
            { country: "Russia", emissions: 1.8, pct: 4.8 },
            { country: "Japan", emissions: 1.1, pct: 2.9 },
          ].map((c) => (
            <div key={c.country} className="flex items-center gap-4">
              <span className="w-28 text-sm text-gray-600 dark:text-gray-400">{c.country}</span>
              <div className="flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
                <div className="h-5 rounded-full bg-red-500 dark:bg-red-600" style={{ width: `${(c.pct / 32) * 100}%` }} />
              </div>
              <span className="w-20 text-right text-sm text-gray-700 dark:text-gray-300">{c.emissions} Gt</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
