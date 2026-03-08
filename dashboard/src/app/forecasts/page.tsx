export default function ForecastsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Forecasts</h1>
      <p className="mt-1 text-gray-500">Multi-agent debate and prediction system (Groq LLM)</p>

      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Latest Forecast</h2>
        <div className="mt-4 rounded-lg bg-emerald-50 p-4 dark:bg-emerald-900/20">
          <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
            Will UK grid carbon intensity exceed 200g CO2/kWh in the next 7 days?
          </p>
          <p className="mt-2 text-3xl font-bold text-emerald-700 dark:text-emerald-400">45% probability</p>
          <p className="mt-1 text-sm text-gray-500">Confidence: Medium | Sources: 4 agents, 3 debate rounds</p>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agent Debate</h2>
        <div className="mt-4 space-y-4">
          {[
            { agent: "Optimist", prob: "25%", reasoning: "Wind forecast shows strong generation next week, pushing carbon intensity down.", color: "green" },
            { agent: "Pessimist", prob: "72%", reasoning: "Gas prices rising, low wind period expected mid-week could spike intensity.", color: "red" },
            { agent: "Statistician", prob: "48%", reasoning: "Historical data shows 40% chance of exceeding 200g in March. Current trend slightly above average.", color: "blue" },
          ].map((a) => (
            <div key={a.agent} className={`rounded-lg border-l-4 border-${a.color}-500 bg-gray-50 p-4 dark:bg-gray-700`}>
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900 dark:text-white">{a.agent}</span>
                <span className={`text-lg font-bold text-${a.color}-600 dark:text-${a.color}-400`}>{a.prob}</span>
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{a.reasoning}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
