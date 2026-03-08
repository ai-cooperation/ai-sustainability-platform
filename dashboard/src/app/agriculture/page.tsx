import KPICard from "@/components/KPICard";

export default function AgriculturePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agriculture Dashboard</h1>
      <p className="mt-1 text-gray-500">4 data sources: FAOSTAT, EU Agri-Food, USDA, GBIF</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title="Global Wheat Yield" value={3.52} unit="t/ha" trend="up" trendValue="+1.2%" />
        <KPICard title="Rice Production" value="523M" unit="tonnes" trend="up" trendValue="+0.8%" />
        <KPICard title="Food Price Index" value={118.5} unit="(2015=100)" trend="down" trendValue="-3.2%" />
      </div>

      <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Top Crop Producers (2024)</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
              <tr><th className="px-4 py-2">Country</th><th className="px-4 py-2">Wheat (Mt)</th><th className="px-4 py-2">Rice (Mt)</th><th className="px-4 py-2">Corn (Mt)</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
              {[
                ["China", "138", "212", "289"],
                ["India", "110", "195", "36"],
                ["USA", "49", "7", "384"],
                ["Brazil", "11", "12", "132"],
                ["EU", "132", "3", "62"],
              ].map(([c, w, r, m]) => (
                <tr key={c} className="text-gray-700 dark:text-gray-300"><td className="px-4 py-2 font-medium">{c}</td><td className="px-4 py-2">{w}</td><td className="px-4 py-2">{r}</td><td className="px-4 py-2">{m}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
