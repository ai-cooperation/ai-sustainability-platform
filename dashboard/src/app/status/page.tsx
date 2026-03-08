import StatusBadge from "@/components/StatusBadge";

const apis = [
  { id: "open_meteo_solar", name: "Open-Meteo Solar", domain: "Energy", status: "healthy", latency: 142 },
  { id: "nasa_power", name: "NASA POWER", domain: "Energy", status: "healthy", latency: 320 },
  { id: "carbon_intensity_uk", name: "UK Carbon Intensity", domain: "Energy", status: "healthy", latency: 89 },
  { id: "open_power_system", name: "Open Power System", domain: "Energy", status: "healthy", latency: 450 },
  { id: "eia", name: "EIA", domain: "Energy", status: "healthy", latency: 210 },
  { id: "electricity_maps", name: "Electricity Maps", domain: "Energy", status: "healthy", latency: 156 },
  { id: "nrel", name: "NREL", domain: "Energy", status: "healthy", latency: 198 },
  { id: "open_meteo_weather", name: "Open-Meteo Weather", domain: "Climate", status: "healthy", latency: 134 },
  { id: "open_meteo_climate", name: "Open-Meteo Climate", domain: "Climate", status: "healthy", latency: 178 },
  { id: "noaa_ghg", name: "NOAA GHG", domain: "Climate", status: "healthy", latency: 567 },
  { id: "world_bank_climate", name: "World Bank Climate", domain: "Climate", status: "degraded", latency: 1200 },
  { id: "noaa_cdo", name: "NOAA CDO", domain: "Climate", status: "healthy", latency: 345 },
  { id: "copernicus_cds", name: "Copernicus CDS", domain: "Climate", status: "healthy", latency: 890 },
  { id: "open_meteo_aq", name: "Open-Meteo Air Quality", domain: "Environment", status: "healthy", latency: 145 },
  { id: "epa_envirofacts", name: "EPA Envirofacts", domain: "Environment", status: "healthy", latency: 430 },
  { id: "epa_water", name: "EPA Water Quality", domain: "Environment", status: "healthy", latency: 380 },
  { id: "emissions_api", name: "Emissions API", domain: "Environment", status: "healthy", latency: 267 },
  { id: "openaq", name: "OpenAQ", domain: "Environment", status: "healthy", latency: 198 },
  { id: "aqicn", name: "AQICN", domain: "Environment", status: "healthy", latency: 156 },
  { id: "gfw", name: "Global Forest Watch", domain: "Environment", status: "down", latency: 0 },
  { id: "faostat", name: "FAOSTAT", domain: "Agriculture", status: "healthy", latency: 780 },
  { id: "eu_agri", name: "EU Agri-Food", domain: "Agriculture", status: "healthy", latency: 345 },
  { id: "usda_nass", name: "USDA NASS", domain: "Agriculture", status: "healthy", latency: 290 },
  { id: "gbif", name: "GBIF", domain: "Agriculture", status: "healthy", latency: 410 },
  { id: "owid", name: "OWID CO2", domain: "Carbon", status: "healthy", latency: 120 },
  { id: "climate_watch", name: "Climate Watch", domain: "Carbon", status: "healthy", latency: 340 },
  { id: "open_climate", name: "Open Climate Data", domain: "Carbon", status: "healthy", latency: 180 },
  { id: "climate_trace", name: "Climate TRACE", domain: "Carbon", status: "healthy", latency: 560 },
  { id: "climatiq", name: "Climatiq", domain: "Carbon", status: "healthy", latency: 210 },
  { id: "ocm", name: "Open Charge Map", domain: "Transport", status: "healthy", latency: 320 },
  { id: "nrel_alt", name: "NREL Alt Fuel", domain: "Transport", status: "healthy", latency: 245 },
];

export default function StatusPage() {
  const healthy = apis.filter(a => a.status === "healthy").length;
  const degraded = apis.filter(a => a.status === "degraded").length;
  const down = apis.filter(a => a.status === "down").length;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Status</h1>
      <p className="mt-1 text-gray-500">Health monitoring for all 31 data sources</p>

      <div className="mt-6 flex gap-4">
        <div className="rounded-lg bg-green-50 px-4 py-2 dark:bg-green-900/20">
          <span className="text-2xl font-bold text-green-600">{healthy}</span>
          <span className="ml-1 text-sm text-green-600">Healthy</span>
        </div>
        <div className="rounded-lg bg-yellow-50 px-4 py-2 dark:bg-yellow-900/20">
          <span className="text-2xl font-bold text-yellow-600">{degraded}</span>
          <span className="ml-1 text-sm text-yellow-600">Degraded</span>
        </div>
        <div className="rounded-lg bg-red-50 px-4 py-2 dark:bg-red-900/20">
          <span className="text-2xl font-bold text-red-600">{down}</span>
          <span className="ml-1 text-sm text-red-600">Down</span>
        </div>
      </div>

      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">API</th>
              <th className="px-4 py-3">Domain</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {apis.map((api) => (
              <tr key={api.id} className="text-gray-700 dark:text-gray-300">
                <td className="px-4 py-2.5 font-medium">{api.name}</td>
                <td className="px-4 py-2.5">{api.domain}</td>
                <td className="px-4 py-2.5"><StatusBadge status={api.status} /></td>
                <td className="px-4 py-2.5">{api.latency > 0 ? `${api.latency}ms` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
