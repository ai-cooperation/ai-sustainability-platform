# Agent 任務規格書

> 每個 agent 的完整指令。斷線可用此文件恢復任務。
> Generated: 2026-03-08

---

# Phase 1: 專案骨架（直接執行，非 agent）

## 產出清單

```
ai-sustainability-platform/
├── src/
│   ├── __init__.py
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── models.py          # DatasetEntry Pydantic model
│   │   ├── loader.py          # load_registry(), validate()
│   │   └── cli.py             # python -m src.registry.cli list|search|info
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py            # BaseConnector ABC
│   │   ├── energy/__init__.py
│   │   ├── climate/__init__.py
│   │   ├── environment/__init__.py
│   │   ├── agriculture/__init__.py
│   │   ├── transport/__init__.py
│   │   └── carbon/__init__.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   └── base.py            # BasePipeline ABC
│   ├── agents/
│   │   ├── __init__.py
│   │   └── base.py            # BaseAgent ABC
│   ├── monitor/
│   │   ├── __init__.py
│   │   └── health_checker.py  # HealthChecker
│   └── utils/
│       ├── __init__.py
│       ├── config.py          # Settings (pydantic-settings)
│       ├── logging.py         # setup_logger()
│       └── telegram.py        # send_telegram()
├── data/
│   └── registry/
│       └── datasets.yaml      # 31 個資料集定義
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/__init__.py
│   └── integration/__init__.py
├── pyproject.toml
├── CLAUDE.md
├── .env
├── .env.example
└── .gitignore
```

## BaseConnector 介面規格

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass(frozen=True)
class ConnectorResult:
    data: pd.DataFrame
    source: str
    fetched_at: datetime
    record_count: int
    metadata: dict

class BaseConnector(ABC):
    """所有 connector 必須繼承此類別"""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector 識別名稱"""

    @property
    @abstractmethod
    def domain(self) -> str:
        """所屬領域: energy|climate|environment|agriculture|transport|carbon"""

    @abstractmethod
    def fetch(self, **params) -> dict | list:
        """從 API 抓取原始資料"""

    @abstractmethod
    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """將原始資料轉換為標準 DataFrame"""

    def validate(self, df: pd.DataFrame) -> bool:
        """驗證 DataFrame schema"""
        return len(df) > 0 and not df.empty

    def health_check(self) -> dict:
        """檢查 API 可用性，回傳 {status, latency_ms, message}"""

    def run(self, **params) -> ConnectorResult:
        """完整流程: fetch → normalize → validate → 回傳結果"""
        raw = self.fetch(**params)
        df = self.normalize(raw)
        if not self.validate(df):
            raise ValidationError(f"{self.name}: validation failed")
        return ConnectorResult(
            data=df,
            source=self.name,
            fetched_at=datetime.utcnow(),
            record_count=len(df),
            metadata={}
        )
```

## datasets.yaml 格式

```yaml
datasets:
  - id: open_meteo_solar
    name: Open-Meteo Solar Radiation
    domain: energy
    provider: Open-Meteo
    access:
      type: api
      endpoint: https://api.open-meteo.com/v1/forecast
      auth: none
      rate_limit: "10000/day"
    update_frequency: hourly
    data_format: json
    connector_class: OpenMeteoSolarConnector
    connector_module: src.connectors.energy.open_meteo_solar
    fields:
      - shortwave_radiation
      - direct_radiation
      - diffuse_radiation
      - timestamp
      - latitude
      - longitude
    status: active
```

## pyproject.toml 依賴

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31",
    "httpx>=0.27",
    "pandas>=2.2",
    "polars>=1.0",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio", "pytest-cov", "ruff>=0.5", "respx"]
groq = ["groq>=0.9"]
dashboard = []
```

---

# Phase 2: Connector Agent 任務規格

> 6 個 agent 各負責一個領域，使用 worktree 隔離開發。

## 共通規則（所有 agent 必須遵守）

1. **繼承 `BaseConnector`**，實作 `name`, `domain`, `fetch()`, `normalize()`
2. **每個 connector 一個檔案**，放在 `src/connectors/{domain}/` 下
3. **每個 connector 附帶 unit test**，放在 `tests/unit/connectors/{domain}/`
4. **test 用 mock**（不實際呼叫 API），另寫 integration test 標記 `@pytest.mark.integration`
5. **normalize() 回傳標準 DataFrame**，必含 `timestamp` 欄位（datetime64）
6. **不要 hardcode API key**，從 `Config` 讀取
7. **錯誤處理**：API 失敗拋 `ConnectorError`，附帶有用訊息
8. **在 `datasets.yaml` 新增對應條目**

## Agent A: 能源領域 (7 connectors)

**檔案清單：**
```
src/connectors/energy/
├── __init__.py
├── open_meteo_solar.py        # #1 Open-Meteo Solar Radiation
├── nasa_power.py              # #2 NASA POWER
├── carbon_intensity_uk.py     # #3 UK Grid Carbon Intensity
├── open_power_system.py       # #4 EU Open Power System Data
├── eia.py                     # #5 US EIA (需 key)
├── electricity_maps.py        # #6 Electricity Maps (需 key)
└── nrel.py                    # #7 NREL Solar+Wind (需 key)

tests/unit/connectors/energy/
├── __init__.py
├── test_open_meteo_solar.py
├── test_nasa_power.py
├── test_carbon_intensity_uk.py
├── test_open_power_system.py
├── test_eia.py
├── test_electricity_maps.py
└── test_nrel.py
```

**各 connector 規格：**

### #1 OpenMeteoSolarConnector
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Params: `latitude, longitude, hourly=shortwave_radiation,direct_radiation,diffuse_radiation`
- Auth: 無
- Output columns: `timestamp, latitude, longitude, shortwave_radiation, direct_radiation, diffuse_radiation`
- Rate limit: 10,000/day

### #2 NASAPowerConnector
- Endpoint: `https://power.larc.nasa.gov/api/temporal/daily/point`
- Params: `parameters=ALLSKY_SFC_SW_DWN,T2M&community=RE&longitude=X&latitude=Y&start=YYYYMMDD&end=YYYYMMDD&format=JSON`
- Auth: 無
- Output columns: `timestamp, latitude, longitude, solar_radiation, temperature`

### #3 CarbonIntensityUKConnector
- Endpoint: `https://api.carbonintensity.org.uk/intensity`
- Also: `/intensity/date/{date}`, `/regional`
- Auth: 無
- Output columns: `timestamp, intensity_forecast, intensity_actual, index, region`

### #4 OpenPowerSystemConnector
- Endpoint: 靜態 CSV 下載 `https://data.open-power-system-data.org/time_series/`
- Auth: 無
- Output columns: `timestamp, country, load, wind_onshore, wind_offshore, solar, ...`
- 注意：資料量大，需支援分片下載

### #5 EIAConnector
- Endpoint: `https://api.eia.gov/v2/`
- Auth: API key (`EIA_API_KEY`)
- Output columns: 依 dataset 而定
- 支援多個 series：electricity, petroleum, natural-gas

### #6 ElectricityMapsConnector
- Endpoint: `https://api.electricitymaps.com/v3/carbon-intensity/latest`
- Auth: API key (`ELECTRICITY_MAPS_API_KEY`)
- Output columns: `timestamp, zone, carbon_intensity, fossil_fuel_percentage`

### #7 NRELConnector
- Endpoint: `https://developer.nrel.gov/api/solar/solar_resource/v1.json`
- Also: wind toolkit, PVWatts
- Auth: API key (`NREL_API_KEY`)
- Output columns: `timestamp, latitude, longitude, ghi, dni, wind_speed`

---

## Agent B: 氣候領域 (6 connectors)

**檔案清單：**
```
src/connectors/climate/
├── __init__.py
├── open_meteo_weather.py      # #8
├── open_meteo_climate.py      # #9
├── noaa_ghg.py                # #10
├── world_bank_climate.py      # #11
├── noaa_cdo.py                # #12 (需 key)
└── copernicus_cds.py          # #13 (需 key)

tests/unit/connectors/climate/
├── __init__.py
├── test_open_meteo_weather.py
├── test_open_meteo_climate.py
├── test_noaa_ghg.py
├── test_world_bank_climate.py
├── test_noaa_cdo.py
└── test_copernicus_cds.py
```

### #8 OpenMeteoWeatherConnector
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Params: `latitude,longitude,hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m`
- Auth: 無
- Output: `timestamp, lat, lon, temperature, humidity, precipitation, wind_speed`

### #9 OpenMeteoClimateConnector
- Endpoint: `https://climate-api.open-meteo.com/v1/climate`
- Params: `latitude,longitude,start_date,end_date,models=EC_Earth3P_HR,daily=temperature_2m_max`
- Auth: 無
- Output: `timestamp, lat, lon, temperature_max, temperature_min, precipitation`

### #10 NOAAGHGConnector
- Endpoint: `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv` (Mauna Loa)
- Also: `co2_mm_gl.csv` (global), CH4
- Auth: 無
- Output: `timestamp, co2_ppm, trend, location`
- 注意：CSV 前有 comment header（#開頭），需跳過

### #11 WorldBankClimateConnector
- Endpoint: `https://climatecknowledgeportal.worldbank.org/api/...` 或
  `http://climatedataapi.worldbank.org/climateweb/rest/v1/country/...`
- Auth: 無
- Output: `country, year, temperature, precipitation, scenario`

### #12 NOAACDOConnector
- Endpoint: `https://www.ncei.noaa.gov/cdo-web/api/v2/data`
- Auth: Token (`NOAA_CDO_TOKEN`)
- Headers: `{"token": "..."}`
- Output: `timestamp, station, datatype, value`
- Rate: 5 req/sec, 10,000/day

### #13 CopernicusCDSConnector
- Endpoint: CDS API (`cdsapi` Python package)
- Auth: `.cdsapirc` file or `COPERNICUS_CDS_KEY`
- Output: 依 dataset，通常需轉 NetCDF → DataFrame
- 注意：queue-based，需 poll 等結果

---

## Agent C: 環境領域 (7 connectors)

**檔案清單：**
```
src/connectors/environment/
├── __init__.py
├── open_meteo_air_quality.py  # #14
├── epa_envirofacts.py         # #15
├── epa_water_quality.py       # #16
├── emissions_api.py           # #17
├── openaq.py                  # #18 (需 key)
├── aqicn.py                   # #19 (需 key)
└── global_forest_watch.py     # #20 (需 key)

tests/unit/connectors/environment/
├── __init__.py
├── test_open_meteo_air_quality.py
├── test_epa_envirofacts.py
├── test_epa_water_quality.py
├── test_emissions_api.py
├── test_openaq.py
├── test_aqicn.py
└── test_global_forest_watch.py
```

### #14 OpenMeteoAirQualityConnector
- Endpoint: `https://air-quality-api.open-meteo.com/v1/air-quality`
- Params: `latitude,longitude,hourly=pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone,european_aqi`
- Auth: 無
- Output: `timestamp, lat, lon, pm2_5, pm10, co, no2, o3, aqi`

### #15 EPAEnvirofactsConnector
- Endpoint: `https://data.epa.gov/efservice/{table}/JSON`
- Tables: `GHG_EMITTER_SECTOR`, `TRI_FACILITY`, etc.
- Auth: 無
- Output: 依 table，通常 `facility, sector, emissions, year`

### #16 EPAWaterQualityConnector
- Endpoint: `https://www.waterqualitydata.us/data/Result/search`
- Params: `statecode=US:XX&characteristicName=Dissolved+oxygen&mimeType=csv`
- Auth: 無
- Output: `timestamp, station, parameter, value, unit`

### #17 EmissionsAPIConnector
- Endpoint: `https://api.v2.emissions-api.org/api/v2/{product}/geo.json`
- Products: `carbonmonoxide`, `nitrogendioxide`, `ozone`, `sulfurdioxide`
- Auth: 無
- Output: `timestamp, latitude, longitude, product, value`

### #18 OpenAQConnector
- Endpoint: `https://api.openaq.org/v3/locations` / `measurements`
- Auth: API key (`OPENAQ_API_KEY`)
- Output: `timestamp, location, parameter, value, unit, country`

### #19 AQICNConnector
- Endpoint: `https://api.waqi.info/feed/{city}/`
- Auth: Token (`AQICN_API_TOKEN`)
- Output: `timestamp, city, aqi, pm25, pm10, o3, no2, so2, co`

### #20 GlobalForestWatchConnector
- Endpoint: `https://data-api.globalforestwatch.org/dataset/{dataset}/latest`
- Auth: API key
- Output: `year, country, tree_cover_loss_ha, co2_emissions`

---

## Agent D: 農業領域 (4 connectors)

**檔案清單：**
```
src/connectors/agriculture/
├── __init__.py
├── faostat.py                 # #21
├── eu_agri_food.py            # #22
├── usda_nass.py               # #23 (需 key)
└── gbif.py                    # #24 (需 key)

tests/unit/connectors/agriculture/
├── __init__.py
├── test_faostat.py
├── test_eu_agri_food.py
├── test_usda_nass.py
└── test_gbif.py
```

### #21 FAOSTATConnector
- Endpoint: `https://fenixservices.fao.org/faostat/api/v1/en/data/{domain}`
- Domains: `QCL` (crop production), `RL` (land use), `GT` (trade)
- Auth: 無
- Output: `year, country, item, element, value, unit`

### #22 EUAgriFoodConnector
- Endpoint: `https://agridata.ec.europa.eu/api/v1/...`
- Data: dairy prices, cereal prices, trade
- Auth: 無
- Output: `date, product, country, price, unit`

### #23 USDANASSConnector
- Endpoint: `https://quickstats.nass.usda.gov/api/api_GET/`
- Params: `key=KEY&commodity_desc=CORN&year=2024&format=JSON`
- Auth: API key (`USDA_NASS_API_KEY`)
- Output: `year, state, commodity, statistic, value, unit`
- Limit: 50,000 records per query

### #24 GBIFConnector
- Endpoint: `https://api.gbif.org/v1/occurrence/search`
- Params: `country=TW&limit=300&offset=0`
- Auth: 需帳號（`GBIF_USERNAME`, `GBIF_PASSWORD`）for downloads；search 免
- Output: `timestamp, species, country, latitude, longitude, dataset`

---

## Agent E: 碳排/ESG 領域 (5 connectors)

**檔案清單：**
```
src/connectors/carbon/
├── __init__.py
├── owid_carbon.py             # #25
├── climate_watch.py           # #26
├── open_climate_data.py       # #27
├── climate_trace.py           # #28
└── climatiq.py                # #29 (需 key)

tests/unit/connectors/carbon/
├── __init__.py
├── test_owid_carbon.py
├── test_climate_watch.py
├── test_open_climate_data.py
├── test_climate_trace.py
└── test_climatiq.py
```

### #25 OWIDCarbonConnector
- Endpoint: `https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv`
- Auth: 無
- Output: `year, country, co2, co2_per_capita, population, gdp, energy_per_capita`

### #26 ClimateWatchConnector
- Endpoint: `https://www.climatewatchdata.org/api/v1/data/historical_emissions`
- Params: `source=CAIT&gas=All GHG&sector=Total including LUCF`
- Auth: 無
- Output: `year, country, sector, gas, value`

### #27 OpenClimateDataConnector
- Endpoint: GitHub raw CSV files from `https://github.com/openclimatedata/`
- Repos: `national-climate-plans`, `global-carbon-budget`
- Auth: 無
- Output: `year, country, emissions, category`

### #28 ClimateTRACEConnector
- Endpoint: `https://api.climatetrace.org/v6/country/emissions`
- Params: `since=2015&to=2023`
- Auth: 無 (beta)
- Output: `year, country, sector, subsector, co2, ch4, n2o, co2e`

### #29 ClimatiqConnector
- Endpoint: `https://api.climatiq.io/estimate`
- Auth: API key (`CLIMATIQ_API_KEY`)
- Headers: `{"Authorization": "Bearer KEY"}`
- Output: `activity, emission_factor, co2e, unit, source`

---

## Agent F: 交通/城市領域 (2 connectors)

**檔案清單：**
```
src/connectors/transport/
├── __init__.py
├── open_charge_map.py         # #30
└── nrel_alt_fuel.py           # #31 (需 key)

tests/unit/connectors/transport/
├── __init__.py
├── test_open_charge_map.py
└── test_nrel_alt_fuel.py
```

### #30 OpenChargeMapConnector
- Endpoint: `https://api.openchargemap.io/v3/poi/`
- Params: `output=json&countrycode=TW&maxresults=100&key=KEY`
- Auth: 可選 key
- Output: `id, title, latitude, longitude, country, power_kw, connector_type, operator`

### #31 NRELAltFuelConnector
- Endpoint: `https://developer.nrel.gov/api/alt-fuel-stations/v1.json`
- Params: `api_key=KEY&fuel_type=ELEC&state=CA&limit=200`
- Auth: API key (`NREL_API_KEY`，同 #7 共用)
- Output: `id, station_name, latitude, longitude, fuel_type, city, state, access_code`

---

# Phase 3: Pipeline Agent 任務規格

## Agent G: 6 條 Pipeline

**前提**：Phase 2 的 connectors 全部完成

**檔案清單：**
```
src/pipelines/
├── __init__.py
├── base.py                    # BasePipeline（Phase 1 已建）
├── energy.py                  # EnergyPipeline
├── climate.py                 # ClimatePipeline
├── environment.py             # EnvironmentPipeline
├── agriculture.py             # AgriculturePipeline
├── carbon.py                  # CarbonPipeline
└── cross_domain.py            # CrossDomainPipeline

tests/unit/pipelines/
├── __init__.py
├── test_energy.py
├── test_climate.py
├── test_environment.py
├── test_agriculture.py
├── test_carbon.py
└── test_cross_domain.py

.github/workflows/
├── daily-update.yml
└── hourly-realtime.yml
```

**BasePipeline 介面：**
```python
class BasePipeline(ABC):
    @abstractmethod
    def extract(self) -> list[ConnectorResult]: ...
    @abstractmethod
    def transform(self, results: list[ConnectorResult]) -> pd.DataFrame: ...
    @abstractmethod
    def load(self, df: pd.DataFrame, path: Path) -> None: ...

    def run(self) -> Path:
        results = self.extract()    # 呼叫多個 connector
        df = self.transform(results) # 合併、清洗
        path = self.output_path()
        self.load(df, path)          # 寫入 parquet
        self.notify()                # TG 通知
        return path
```

**每條 Pipeline 職責：**
- `EnergyPipeline`: 合併 #1-#7 → `data/processed/energy/`
- `ClimatePipeline`: 合併 #8-#13 → `data/processed/climate/`
- `EnvironmentPipeline`: 合併 #14-#20 → `data/processed/environment/`
- `AgriculturePipeline`: 合併 #21-#24 → `data/processed/agriculture/`
- `CarbonPipeline`: 合併 #25-#29 → `data/processed/carbon/`
- `CrossDomainPipeline`: 跨領域關聯（能源×氣候×碳排）→ `data/processed/cross_domain/`

**GitHub Actions workflows:**
- `daily-update.yml`: 每日 UTC 06:00 跑全部 pipeline
- `hourly-realtime.yml`: 每小時跑即時數據（#3 碳強度、#14 空品）

---

# Phase 4: Dashboard Agent 任務規格

## Agent H: TailAdmin Dashboard 8 頁面

**前提**：Phase 2 的 connectors 至少部分完成（有數據可顯示）

**步驟：**
1. Clone TailAdmin Free Next.js Dashboard
2. 清理不需要的範例頁面
3. 建立 8 個頁面
4. 接入靜態 JSON 數據
5. GitHub Pages 部署 workflow

**目錄結構：**
```
dashboard/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Overview
│   │   ├── energy/page.tsx
│   │   ├── climate/page.tsx
│   │   ├── environment/page.tsx
│   │   ├── agriculture/page.tsx
│   │   ├── carbon/page.tsx
│   │   ├── forecasts/page.tsx
│   │   └── status/page.tsx
│   ├── components/
│   │   ├── sustainability/       # 自訂元件
│   │   │   ├── KPICard.tsx
│   │   │   ├── TimeSeriesChart.tsx
│   │   │   ├── SustainabilityMap.tsx
│   │   │   ├── EmissionsRanking.tsx
│   │   │   └── APIStatusTable.tsx
│   │   └── ...                   # TailAdmin 原有元件
│   └── data/                     # 靜態 JSON（pipeline 產出）
│       ├── overview.json
│       ├── energy.json
│       ├── climate.json
│       ├── environment.json
│       ├── agriculture.json
│       ├── carbon.json
│       └── status.json
├── public/
├── package.json
└── next.config.js               # static export 設定
```

**頁面內容規格：**

| 頁面 | 主要元件 | 數據來源 |
|------|---------|---------|
| Overview | 6 KPI 卡片 + 全球地圖 + 趨勢圖 | 各領域摘要 |
| Energy | 碳強度地圖 + 太陽能/風能圖表 | Connector #1-#7 |
| Climate | CO2 趨勢線 + 溫度異常圖 + 氣候預測 | Connector #8-#13 |
| Environment | 空品地圖 + 水質指標 + 森林覆蓋 | Connector #14-#20 |
| Agriculture | 產量趨勢 + 食品價格 + 區域比較 | Connector #21-#24 |
| Carbon | 國家排放排名 + 趨勢 + 部門分析 | Connector #25-#29 |
| Forecasts | AI 預測卡片 + 辯論時間線 | Phase 6 產出 |
| Status | API 狀態表格 + uptime 圖 | Monitor 產出 |

**部署：**
```yaml
# .github/workflows/deploy-dashboard.yml
on:
  push:
    branches: [main]
    paths: ['dashboard/**', 'data/processed/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: cd dashboard && npm ci && npm run build
      - uses: peaceiris/actions-gh-pages@v4
        with:
          publish_dir: dashboard/out
```

---

# Phase 5: Monitor Agent 任務規格

## Agent I: API 健康監控

**檔案清單：**
```
src/monitor/
├── __init__.py
├── health_checker.py          # Phase 1 骨架，此處完善
├── reporter.py                # 產出 status.json + TG 報告
└── scheduler.py               # 排程邏輯

data/
└── status/
    ├── status.json            # 即時狀態
    └── history/               # 歷史 uptime

.github/workflows/
└── api-health-check.yml       # 每 6 小時

tests/unit/monitor/
├── __init__.py
├── test_health_checker.py
└── test_reporter.py
```

**HealthChecker 規格：**
- 逐一檢查 31 個 API endpoint
- 記錄：HTTP status, latency (ms), schema 有效性, 最後成功時間
- 產出 `status.json`：
  ```json
  {
    "checked_at": "2026-03-08T12:00:00Z",
    "total": 31,
    "healthy": 28,
    "degraded": 2,
    "down": 1,
    "apis": [
      {
        "id": "open_meteo_solar",
        "name": "Open-Meteo Solar",
        "status": "healthy",
        "latency_ms": 142,
        "last_success": "2026-03-08T12:00:00Z",
        "uptime_30d": 99.8
      }
    ]
  }
  ```
- 狀態變化（healthy→down）→ TG 即時通知
- 每日 08:00 → TG 健康摘要

---

# Phase 6: 多代理系統 任務規格

## Agent J: 多代理決策系統

**前提**：Phase 2+3 完成（有數據可分析），Groq API key 已設定

**檔案清單：**
```
src/agents/
├── __init__.py
├── base.py                    # BaseAgent（Phase 1 已建）
├── llm_client.py              # GroqClient
├── signal_agent.py            # SignalAgent
├── news_agent.py              # NewsAgent
├── analyst_agent.py           # AnalystAgent
├── debate_agent.py            # DebateAgent (3 variants)
├── judge_agent.py             # JudgeAgent
├── orchestrator.py            # ForecastOrchestrator
└── prompts/
    ├── signal.txt
    ├── news.txt
    ├── analyst.txt
    ├── debate_optimist.txt
    ├── debate_pessimist.txt
    ├── debate_statistician.txt
    └── judge.txt

tests/unit/agents/
├── __init__.py
├── test_llm_client.py
├── test_signal_agent.py
├── test_orchestrator.py
└── test_debate_flow.py
```

**GroqClient 規格：**
```python
class GroqClient:
    """Groq API 整合，支援 Llama 3.3 70B"""
    model: str = "llama-3.3-70b-versatile"
    max_tokens: int = 4096
    rate_limit: int = 30  # req/min free tier
    # 含 retry, rate limiting, token counting
    # fallback: MCP llm_chat tool
```

**ForecastOrchestrator 工作流：**
```
1. 資料快照 → 傳給 SignalAgent
2. SignalAgent 產出 signals[] → 傳給 AnalystAgent
3. AnalystAgent 產出 hypotheses[] → 生成 forecast question
4. 3 個 DebateAgent 各自分析 → 各產出 {probability, reasoning}
5. 辯論（最多 3 輪，每輪看到對方論點後更新）
6. JudgeAgent 評估所有論點 → 最終 prediction
7. 輸出 JSON → 存檔 + 推送 dashboard
```

**輸出格式：**
```json
{
  "id": "forecast-2026-03-08-001",
  "question": "Will UK grid carbon intensity exceed 200g CO2/kWh in the next 7 days?",
  "created_at": "2026-03-08T12:00:00Z",
  "signals": [...],
  "debate_rounds": [
    {
      "round": 1,
      "agents": {
        "optimist": {"probability": 0.25, "reasoning": "..."},
        "pessimist": {"probability": 0.72, "reasoning": "..."},
        "statistician": {"probability": 0.48, "reasoning": "..."}
      }
    }
  ],
  "final_prediction": {
    "probability": 0.45,
    "confidence": "medium",
    "reasoning": "...",
    "data_sources": ["carbon_intensity_uk", "open_meteo_weather"]
  }
}
```

---

# 進度追蹤

| Agent | 領域 | Connectors | 狀態 |
|-------|------|-----------|------|
| — | Phase 1 骨架 | — | ⬜ 待開始 |
| A | 能源 | 7 | ⬜ 待開始 |
| B | 氣候 | 6 | ⬜ 待開始 |
| C | 環境 | 7 | ⬜ 待開始 |
| D | 農業 | 4 | ⬜ 待開始 |
| E | 碳排/ESG | 5 | ⬜ 待開始 |
| F | 交通/城市 | 2 | ⬜ 待開始 |
| G | Pipeline | 6 條 | ⬜ 待開始 |
| H | Dashboard | 8 頁面 | ⬜ 待開始 |
| I | Monitor | 31 API | ⬜ 待開始 |
| J | 多代理 | 7 代理 | ⬜ 待開始 |
