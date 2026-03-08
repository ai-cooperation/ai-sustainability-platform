export type Lang = "en" | "zh";

const translations: Record<string, Record<Lang, string>> = {
  // App
  "app.title": { en: "AI Sustainability Intelligence Platform", zh: "AI 永續發展智慧決策平台" },
  "app.subtitle": { en: "Real-time monitoring across {count} global data sources", zh: "即時監測 {count} 個全球永續資料來源" },

  // Nav
  "nav.overview": { en: "Overview", zh: "總覽" },
  "nav.energy": { en: "Energy", zh: "能源" },
  "nav.climate": { en: "Climate", zh: "氣候" },
  "nav.environment": { en: "Environment", zh: "環境" },
  "nav.agriculture": { en: "Agriculture", zh: "農業" },
  "nav.carbon": { en: "Carbon", zh: "碳排放" },
  "nav.forecasts": { en: "AI Forecasts", zh: "AI 預測" },
  "nav.status": { en: "API Status", zh: "API 狀態" },

  // Domains
  "domain.energy": { en: "Energy", zh: "能源" },
  "domain.climate": { en: "Climate", zh: "氣候" },
  "domain.environment": { en: "Environment", zh: "環境" },
  "domain.agriculture": { en: "Agriculture", zh: "農業" },
  "domain.carbon": { en: "Carbon", zh: "碳排放" },
  "domain.transport": { en: "Transport", zh: "交通運輸" },

  // Common
  "common.loading": { en: "Loading...", zh: "載入中..." },
  "common.dataSources": { en: "Data Sources", zh: "資料來源" },
  "common.active": { en: "Active", zh: "運作中" },
  "common.sources": { en: "sources", zh: "個來源" },
  "common.live": { en: "Live", zh: "即時" },
  "common.online": { en: "Online", zh: "上線" },
  "common.country": { en: "Country", zh: "國家" },
  "common.stable": { en: "Stable", zh: "穩定" },

  // Status page
  "status.title": { en: "API Status", zh: "API 狀態監控" },
  "status.subtitle": { en: "Live health monitoring for {count} data sources", zh: "{count} 個資料來源即時健康監測" },
  "status.lastChecked": { en: "Last checked", zh: "最近檢查" },
  "status.healthy": { en: "Healthy", zh: "正常" },
  "status.degraded": { en: "Degraded", zh: "緩慢" },
  "status.down": { en: "Down", zh: "離線" },
  "status.api": { en: "API", zh: "API" },
  "status.domain": { en: "Domain", zh: "領域" },
  "status.latency": { en: "Latency", zh: "延遲" },
  "status.statusCol": { en: "Status", zh: "狀態" },
  "status.matrix": { en: "Health Check History (6h intervals)", zh: "健康檢查歷史（每 6 小時）" },

  // Overview page
  "overview.platformStatus": { en: "Platform Status", zh: "平台運作狀態" },
  "overview.latestForecast": { en: "Latest AI Forecast", zh: "最新 AI 預測" },
  "overview.awaitingForecast": { en: "Awaiting first forecast run", zh: "等待首次預測執行" },
  "overview.forecastSchedule": { en: "Daily forecast runs via GitHub Actions", zh: "每日自動執行 AI 預測（GitHub Actions）" },
  "overview.probability": { en: "probability", zh: "機率" },
  "overview.confidence": { en: "Confidence", zh: "信心度" },
  "overview.agents": { en: "agents", zh: "個代理" },
  "overview.online": { en: "Online", zh: "上線" },
  "overview.sources": { en: "sources", zh: "個來源" },
  "overview.live": { en: "Live", zh: "即時" },

  // KPI titles
  "kpi.co2": { en: "Global CO2 Emissions", zh: "全球 CO2 排放量" },
  "kpi.renewable": { en: "Renewable Share", zh: "再生能源佔比" },
  "kpi.aqi": { en: "Global Avg AQI", zh: "全球平均空氣品質" },
  "kpi.carbonIntensity": { en: "UK Carbon Intensity", zh: "英國碳排強度" },
  "kpi.apiHealth": { en: "API Health", zh: "API 健康度" },
  "kpi.forecastAccuracy": { en: "Forecast Accuracy", zh: "預測準確率" },

  // Energy page
  "energy.title": { en: "Energy Dashboard", zh: "能源儀表板" },
  "energy.subtitle": { en: "7 data sources: Solar, Wind, Grid Carbon Intensity, Power Systems", zh: "7 個資料來源：太陽能、風力、電網碳排強度、電力系統" },
  "energy.ukCarbon": { en: "UK Carbon Intensity", zh: "英國碳排強度" },
  "energy.solarRadiation": { en: "Solar Radiation", zh: "太陽輻射量" },
  "energy.windGeneration": { en: "Wind Generation", zh: "風力發電量" },
  "energy.renewablePct": { en: "Renewable %", zh: "再生能源佔比" },
  "energy.peakHour": { en: "Peak hour", zh: "尖峰時段" },
  "energy.lower": { en: "12% lower", zh: "降低 12%" },

  // Climate page
  "climate.title": { en: "Climate Dashboard", zh: "氣候儀表板" },
  "climate.subtitle": { en: "6 data sources: Weather, GHG Concentrations, Climate Projections", zh: "6 個資料來源：氣象、溫室氣體濃度、氣候預測" },
  "climate.co2": { en: "Atmospheric CO2", zh: "大氣 CO2 濃度" },
  "climate.methane": { en: "Methane (CH4)", zh: "甲烷 (CH4)" },
  "climate.tempAnomaly": { en: "Temp Anomaly", zh: "溫度異常" },
  "climate.vsPreindustrial": { en: "°C vs pre-industrial", zh: "°C（較工業化前）" },
  "climate.co2Trend": { en: "CO2 Concentration Trend (Mauna Loa)", zh: "CO2 濃度趨勢（茂納羅亞觀測站）" },

  // Environment page
  "env.title": { en: "Environment Dashboard", zh: "環境儀表板" },
  "env.subtitle": { en: "7 data sources: Air Quality, Water, Emissions, Forests", zh: "7 個資料來源：空氣品質、水質、排放、森林" },
  "env.aqi": { en: "Global Avg AQI", zh: "全球平均 AQI" },
  "env.good": { en: "Good", zh: "良好" },
  "env.pm25": { en: "PM2.5 Level", zh: "PM2.5 濃度" },
  "env.no2": { en: "NO2 Satellite", zh: "NO2 衛星監測" },
  "env.forestLoss": { en: "Forest Loss", zh: "森林流失" },
  "env.better": { en: "3% better", zh: "改善 3%" },
  "env.aqByRegion": { en: "Air Quality by Region", zh: "各地區空氣品質" },
  "env.northAmerica": { en: "North America", zh: "北美洲" },
  "env.europe": { en: "Europe", zh: "歐洲" },
  "env.eastAsia": { en: "East Asia", zh: "東亞" },
  "env.southAsia": { en: "South Asia", zh: "南亞" },
  "env.africa": { en: "Africa", zh: "非洲" },

  // Agriculture page
  "agri.title": { en: "Agriculture Dashboard", zh: "農業儀表板" },
  "agri.subtitle": { en: "4 data sources: FAOSTAT, EU Agri-Food, USDA, GBIF", zh: "4 個資料來源：FAOSTAT、歐盟農業、美國農業部、GBIF" },
  "agri.wheatYield": { en: "Global Wheat Yield", zh: "全球小麥產量" },
  "agri.riceProduction": { en: "Rice Production", zh: "稻米生產量" },
  "agri.foodPriceIndex": { en: "Food Price Index", zh: "糧食價格指數" },
  "agri.tonnes": { en: "tonnes", zh: "公噸" },
  "agri.topProducers": { en: "Top Crop Producers (2024)", zh: "主要農作物生產國 (2024)" },
  "agri.wheat": { en: "Wheat (Mt)", zh: "小麥 (百萬噸)" },
  "agri.rice": { en: "Rice (Mt)", zh: "稻米 (百萬噸)" },
  "agri.corn": { en: "Corn (Mt)", zh: "玉米 (百萬噸)" },
  "agri.china": { en: "China", zh: "中國" },
  "agri.india": { en: "India", zh: "印度" },
  "agri.usa": { en: "USA", zh: "美國" },
  "agri.brazil": { en: "Brazil", zh: "巴西" },
  "agri.eu": { en: "EU", zh: "歐盟" },

  // Carbon page
  "carbon.title": { en: "Carbon Emissions Dashboard", zh: "碳排放儀表板" },
  "carbon.subtitle": { en: "5 data sources: OWID, Climate Watch, Climate TRACE, Climatiq", zh: "5 個資料來源：OWID、Climate Watch、Climate TRACE、Climatiq" },
  "carbon.globalCo2": { en: "Global CO2 Emissions", zh: "全球 CO2 排放量" },
  "carbon.perCapita": { en: "Per Capita (World)", zh: "人均排放（全球）" },
  "carbon.budgetLeft": { en: "Carbon Budget Left", zh: "剩餘碳預算" },
  "carbon.budgetUnit": { en: "Gt CO2 (1.5°C)", zh: "Gt CO2（1.5°C 目標）" },
  "carbon.yearsLeft": { en: "~7 years at current rate", zh: "按目前速率約剩 7 年" },
  "carbon.topEmitters": { en: "Top Emitters", zh: "主要排放國" },
  "carbon.china": { en: "China", zh: "中國" },
  "carbon.us": { en: "United States", zh: "美國" },
  "carbon.india": { en: "India", zh: "印度" },
  "carbon.eu27": { en: "EU-27", zh: "歐盟 27 國" },
  "carbon.russia": { en: "Russia", zh: "俄羅斯" },
  "carbon.japan": { en: "Japan", zh: "日本" },

  // Forecasts page
  "forecast.title": { en: "AI Forecasts", zh: "AI 智慧預測" },
  "forecast.subtitle": { en: "Multi-agent debate and prediction system (Groq LLM)", zh: "多代理辯論預測系統（Groq LLM 驅動）" },
  "forecast.latest": { en: "Latest Forecast", zh: "最新預測" },
  "forecast.probability": { en: "probability", zh: "機率" },
  "forecast.confidence": { en: "Confidence", zh: "信心度" },
  "forecast.medium": { en: "Medium", zh: "中等" },
  "forecast.agentSources": { en: "Sources: 4 agents, 3 debate rounds", zh: "來源：4 個代理、3 輪辯論" },
  "forecast.agentDebate": { en: "Agent Debate", zh: "代理辯論過程" },
  "forecast.optimist": { en: "Optimist", zh: "樂觀派" },
  "forecast.pessimist": { en: "Pessimist", zh: "悲觀派" },
  "forecast.statistician": { en: "Statistician", zh: "統計派" },
  "forecast.optimistReason": {
    en: "Wind forecast shows strong generation next week, pushing carbon intensity down.",
    zh: "風力預報顯示下週發電量充足，將推動碳排強度下降。",
  },
  "forecast.pessimistReason": {
    en: "Gas prices rising, low wind period expected mid-week could spike intensity.",
    zh: "天然氣價格上漲，預計週中風力減弱，可能導致碳排強度飆升。",
  },
  "forecast.statisticianReason": {
    en: "Historical data shows 40% chance of exceeding 200g in March. Current trend slightly above average.",
    zh: "歷史數據顯示三月份有 40% 機率超過 200g。目前趨勢略高於平均值。",
  },
  "forecast.question1": {
    en: "Will UK grid carbon intensity exceed 200g CO2/kWh in the next 7 days?",
    zh: "英國電網碳排強度在未來 7 天內是否會超過 200g CO2/kWh？",
  },

  // Loading
  "overview.loading": { en: "Loading...", zh: "載入中..." },

  // API Detail - column headers
  "apiDetail.title": { en: "API Details", zh: "API 詳細資訊" },
  "apiDetail.source": { en: "Data Source", zh: "資料來源" },
  "apiDetail.format": { en: "Data Format", zh: "資料格式" },
  "apiDetail.content": { en: "Content", zh: "內容說明" },
  "apiDetail.close": { en: "Close", zh: "關閉" },

  // API names (full)
  "api.open_meteo_solar.name": { en: "Open-Meteo Solar Radiation", zh: "Open-Meteo 太陽輻射" },
  "api.open_meteo_solar.desc": {
    en: "Hourly and daily solar radiation forecasts including GHI, DNI, and diffuse radiation for any location worldwide.",
    zh: "提供全球任意地點的逐時及每日太陽輻射預報，包含全球水平輻射量（GHI）、直射法線輻射量（DNI）及散射輻射量。",
  },
  "api.open_meteo_solar.source": { en: "api.open-meteo.com", zh: "api.open-meteo.com" },
  "api.open_meteo_solar.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.nasa_power.name": { en: "NASA POWER", zh: "NASA POWER 能源資料" },
  "api.nasa_power.desc": {
    en: "NASA satellite-derived meteorological and solar energy data. Provides 30+ years of surface solar irradiance, temperature, and wind data.",
    zh: "NASA 衛星氣象與太陽能資料。提供超過 30 年的地表太陽輻照度、溫度及風力數據。",
  },
  "api.nasa_power.source": { en: "power.larc.nasa.gov", zh: "power.larc.nasa.gov" },
  "api.nasa_power.format": { en: "JSON/CSV REST API, free, no key required", zh: "JSON/CSV REST API，免費，無需金鑰" },

  "api.carbon_intensity_uk.name": { en: "UK Carbon Intensity", zh: "英國碳排放強度" },
  "api.carbon_intensity_uk.desc": {
    en: "Real-time and forecast carbon intensity of UK electricity grid (gCO2/kWh). Updated every 30 minutes with 96-hour forecasts.",
    zh: "英國電網即時與預測碳排強度（gCO2/kWh）。每 30 分鐘更新，提供 96 小時預報。",
  },
  "api.carbon_intensity_uk.source": { en: "api.carbonintensity.org.uk (National Grid ESO)", zh: "api.carbonintensity.org.uk（英國國家電網 ESO）" },
  "api.carbon_intensity_uk.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.open_power_system.name": { en: "Open Power System Data", zh: "開放電力系統資料" },
  "api.open_power_system.desc": {
    en: "European power system time series: electricity generation by source, consumption, and cross-border flows.",
    zh: "歐洲電力系統時間序列：按來源分類的發電量、用電量及跨境電力流動。",
  },
  "api.open_power_system.source": { en: "data.open-power-system-data.org", zh: "data.open-power-system-data.org" },
  "api.open_power_system.format": { en: "CSV/SQLite bulk download, free", zh: "CSV/SQLite 批量下載，免費" },

  "api.eia.name": { en: "U.S. EIA Energy Data", zh: "美國能源資訊署（EIA）" },
  "api.eia.desc": {
    en: "U.S. energy production, consumption, prices, and emissions data. Covers petroleum, natural gas, coal, electricity, and renewables.",
    zh: "美國能源生產、消費、價格及排放數據。涵蓋石油、天然氣、煤炭、電力及再生能源。",
  },
  "api.eia.source": { en: "api.eia.gov (U.S. Energy Information Administration)", zh: "api.eia.gov（美國能源資訊署）" },
  "api.eia.format": { en: "JSON REST API, requires free API key", zh: "JSON REST API，需申請免費金鑰" },

  "api.electricity_maps.name": { en: "Electricity Maps", zh: "Electricity Maps 電力碳排" },
  "api.electricity_maps.desc": {
    en: "Real-time carbon intensity and power breakdown for 160+ electricity zones worldwide. Shows renewable vs fossil fuel mix.",
    zh: "全球 160+ 電力區域的即時碳排強度與電力結構。顯示再生能源與化石燃料比例。",
  },
  "api.electricity_maps.source": { en: "api.electricitymaps.com", zh: "api.electricitymaps.com" },
  "api.electricity_maps.format": { en: "JSON REST API, free tier available", zh: "JSON REST API，有免費方案" },

  "api.nrel.name": { en: "NREL Renewable Energy", zh: "NREL 再生能源" },
  "api.nrel.desc": {
    en: "U.S. National Renewable Energy Laboratory datasets including solar resource, wind data, and alternative fuel stations.",
    zh: "美國國家再生能源實驗室資料集，包含太陽能資源、風力數據及替代燃料站。",
  },
  "api.nrel.source": { en: "developer.nrel.gov", zh: "developer.nrel.gov" },
  "api.nrel.format": { en: "JSON REST API, requires free API key", zh: "JSON REST API，需申請免費金鑰" },

  "api.open_meteo_weather.name": { en: "Open-Meteo Weather", zh: "Open-Meteo 天氣" },
  "api.open_meteo_weather.desc": {
    en: "Global weather forecasts: temperature, precipitation, wind, humidity. 16-day forecasts and 80+ years of historical data.",
    zh: "全球天氣預報：溫度、降水、風力、濕度。提供 16 天預報及超過 80 年歷史數據。",
  },
  "api.open_meteo_weather.source": { en: "api.open-meteo.com", zh: "api.open-meteo.com" },
  "api.open_meteo_weather.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.open_meteo_climate.name": { en: "Open-Meteo Climate Projections", zh: "Open-Meteo 氣候預測" },
  "api.open_meteo_climate.desc": {
    en: "CMIP6 climate model projections: temperature, precipitation changes under different emission scenarios (SSP1-5) through 2100.",
    zh: "CMIP6 氣候模型預測：不同排放情境（SSP1-5）下的溫度、降水變化預估至 2100 年。",
  },
  "api.open_meteo_climate.source": { en: "climate-api.open-meteo.com", zh: "climate-api.open-meteo.com" },
  "api.open_meteo_climate.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.noaa_ghg.name": { en: "NOAA Greenhouse Gases", zh: "NOAA 溫室氣體監測" },
  "api.noaa_ghg.desc": {
    en: "Global atmospheric greenhouse gas concentrations from NOAA's Global Monitoring Laboratory. CO2, CH4, N2O measurements from Mauna Loa and global stations.",
    zh: "NOAA 全球監測實驗室的大氣溫室氣體濃度。來自茂納羅亞及全球測站的 CO2、CH4、N2O 測量值。",
  },
  "api.noaa_ghg.source": { en: "gml.noaa.gov (NOAA Global Monitoring Lab)", zh: "gml.noaa.gov（NOAA 全球監測實驗室）" },
  "api.noaa_ghg.format": { en: "Text/CSV files, free, no key required", zh: "文字/CSV 檔案，免費，無需金鑰" },

  "api.world_bank_climate.name": { en: "World Bank Climate Indicators", zh: "世界銀行氣候指標" },
  "api.world_bank_climate.desc": {
    en: "Country-level climate and development indicators: CO2 emissions per capita, renewable energy share, forest area, access to electricity.",
    zh: "各國氣候與發展指標：人均 CO2 排放量、再生能源佔比、森林面積、電力普及率。",
  },
  "api.world_bank_climate.source": { en: "api.worldbank.org (World Bank Open Data)", zh: "api.worldbank.org（世界銀行開放資料）" },
  "api.world_bank_climate.format": { en: "JSON/XML REST API, free, no key required", zh: "JSON/XML REST API，免費，無需金鑰" },

  "api.noaa_cdo.name": { en: "NOAA Climate Data Online", zh: "NOAA 氣候資料線上" },
  "api.noaa_cdo.desc": {
    en: "Historical weather and climate records from global stations. Daily/monthly observations: temperature extremes, precipitation, snow depth.",
    zh: "來自全球測站的歷史天氣與氣候紀錄。每日/每月觀測：極端溫度、降水量、雪深。",
  },
  "api.noaa_cdo.source": { en: "www.ncei.noaa.gov (NCEI)", zh: "www.ncei.noaa.gov（NCEI 國家環境資訊中心）" },
  "api.noaa_cdo.format": { en: "JSON REST API, requires free token", zh: "JSON REST API，需申請免費 Token" },

  "api.copernicus_cds.name": { en: "Copernicus Climate Data Store", zh: "哥白尼氣候資料庫" },
  "api.copernicus_cds.desc": {
    en: "ERA5 reanalysis and satellite climate data from the EU's Copernicus program. Comprehensive global atmospheric and land surface variables.",
    zh: "歐盟哥白尼計畫的 ERA5 再分析與衛星氣候資料。全面的全球大氣與地表變量。",
  },
  "api.copernicus_cds.source": { en: "cds.climate.copernicus.eu (EU Copernicus)", zh: "cds.climate.copernicus.eu（歐盟哥白尼計畫）" },
  "api.copernicus_cds.format": { en: "NetCDF/GRIB via CDS API, free account required", zh: "NetCDF/GRIB 格式，需免費帳號" },

  "api.open_meteo_air_quality.name": { en: "Open-Meteo Air Quality", zh: "Open-Meteo 空氣品質" },
  "api.open_meteo_air_quality.desc": {
    en: "Global air quality forecasts: PM2.5, PM10, O3, NO2, SO2, CO concentrations and AQI values with 5-day forecasts.",
    zh: "全球空氣品質預報：PM2.5、PM10、O3、NO2、SO2、CO 濃度及 AQI 值，提供 5 天預報。",
  },
  "api.open_meteo_air_quality.source": { en: "air-quality-api.open-meteo.com", zh: "air-quality-api.open-meteo.com" },
  "api.open_meteo_air_quality.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.epa_envirofacts.name": { en: "EPA Envirofacts", zh: "美國環保署環境資料" },
  "api.epa_envirofacts.desc": {
    en: "U.S. EPA environmental data: toxic releases, facility emissions, hazardous waste, water discharge permits.",
    zh: "美國環保署環境資料：有毒物質排放、設施排放量、有害廢棄物、水排放許可。",
  },
  "api.epa_envirofacts.source": { en: "data.epa.gov (U.S. EPA)", zh: "data.epa.gov（美國環保署）" },
  "api.epa_envirofacts.format": { en: "JSON/XML/CSV REST API, free, no key required", zh: "JSON/XML/CSV REST API，免費，無需金鑰" },

  "api.epa_water_quality.name": { en: "EPA Water Quality", zh: "美國水質監測" },
  "api.epa_water_quality.desc": {
    en: "U.S. water quality monitoring data from 400+ organizations. Stream, lake, and groundwater chemistry measurements.",
    zh: "來自 400+ 組織的美國水質監測資料。河流、湖泊及地下水化學測量值。",
  },
  "api.epa_water_quality.source": { en: "www.waterqualitydata.us (WQP)", zh: "www.waterqualitydata.us（WQP 水質入口網）" },
  "api.epa_water_quality.format": { en: "JSON/CSV REST API, free, no key required", zh: "JSON/CSV REST API，免費，無需金鑰" },

  "api.emissions_api.name": { en: "Emissions API (Satellite)", zh: "衛星排放量 API" },
  "api.emissions_api.desc": {
    en: "Satellite-based CO2 emission estimates derived from Sentinel-5P. Country and region-level carbon emission monitoring.",
    zh: "基於哨兵 5P 衛星的 CO2 排放估算。提供國家及區域級碳排放監測。",
  },
  "api.emissions_api.source": { en: "api.v2.emissions-api.org", zh: "api.v2.emissions-api.org" },
  "api.emissions_api.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.openaq.name": { en: "OpenAQ Air Quality", zh: "OpenAQ 全球空氣品質" },
  "api.openaq.desc": {
    en: "Open-source platform aggregating real-time air quality data from 300+ sources across 100+ countries.",
    zh: "開源平台，匯集來自 100+ 國家、300+ 資料來源的即時空氣品質數據。",
  },
  "api.openaq.source": { en: "api.openaq.org", zh: "api.openaq.org" },
  "api.openaq.format": { en: "JSON REST API, free API key required", zh: "JSON REST API，需免費 API 金鑰" },

  "api.aqicn.name": { en: "AQICN World Air Quality", zh: "AQICN 世界空氣品質指數" },
  "api.aqicn.desc": {
    en: "Real-time AQI data from 12,000+ monitoring stations in 1,000+ cities. Provides PM2.5, PM10, O3, NO2, SO2, CO readings.",
    zh: "來自 1,000+ 城市、12,000+ 監測站的即時 AQI 資料。提供 PM2.5、PM10、O3、NO2、SO2、CO 讀數。",
  },
  "api.aqicn.source": { en: "api.waqi.info (WAQI project)", zh: "api.waqi.info（WAQI 世界空氣品質計畫）" },
  "api.aqicn.format": { en: "JSON REST API, free token required", zh: "JSON REST API，需免費 Token" },

  "api.global_forest_watch.name": { en: "Global Forest Watch", zh: "全球森林監測" },
  "api.global_forest_watch.desc": {
    en: "Near real-time forest change monitoring using Landsat and Sentinel satellite imagery. Tree cover loss, gain, and fire alerts.",
    zh: "利用 Landsat 及 Sentinel 衛星影像的近即時森林變化監測。樹木覆蓋流失、增加及火災警報。",
  },
  "api.global_forest_watch.source": { en: "data-api.globalforestwatch.org (WRI)", zh: "data-api.globalforestwatch.org（世界資源研究所）" },
  "api.global_forest_watch.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.faostat.name": { en: "FAO FAOSTAT", zh: "聯合國糧農組織 FAOSTAT" },
  "api.faostat.desc": {
    en: "UN Food and Agriculture Organization statistics: crop production, food prices, trade, land use, pesticides, fertilizers across 245 countries.",
    zh: "聯合國糧農組織統計資料：245 個國家的農作物生產、糧食價格、貿易、土地使用、農藥、肥料。",
  },
  "api.faostat.source": { en: "fenixservices.fao.org (FAO)", zh: "fenixservices.fao.org（聯合國糧農組織）" },
  "api.faostat.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.eu_agri_food.name": { en: "EU Agriculture / Eurostat", zh: "歐盟農業 / Eurostat" },
  "api.eu_agri_food.desc": {
    en: "European agricultural statistics from Eurostat: crop production, farm structures, organic farming, food prices with USDA FAS fallback.",
    zh: "Eurostat 歐洲農業統計：農作物生產、農場結構、有機農業、糧食價格，備援 USDA FAS 資料。",
  },
  "api.eu_agri_food.source": { en: "ec.europa.eu/eurostat + apps.fas.usda.gov", zh: "ec.europa.eu/eurostat + apps.fas.usda.gov" },
  "api.eu_agri_food.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.usda_nass.name": { en: "USDA NASS QuickStats", zh: "美國農業部 NASS" },
  "api.usda_nass.desc": {
    en: "U.S. agricultural statistics: crop acreage, production, yield, livestock, prices from National Agricultural Statistics Service.",
    zh: "美國農業統計：農作物面積、產量、收成、畜牧、價格，來自國家農業統計服務。",
  },
  "api.usda_nass.source": { en: "quickstats.nass.usda.gov (USDA)", zh: "quickstats.nass.usda.gov（美國農業部）" },
  "api.usda_nass.format": { en: "JSON/CSV REST API, requires free API key", zh: "JSON/CSV REST API，需申請免費金鑰" },

  "api.gbif.name": { en: "GBIF Biodiversity", zh: "GBIF 全球生物多樣性" },
  "api.gbif.desc": {
    en: "Global Biodiversity Information Facility: 2.4 billion+ species occurrence records from natural history collections and citizen science.",
    zh: "全球生物多樣性資訊機構：24 億+筆物種出現紀錄，來自自然史典藏及公民科學。",
  },
  "api.gbif.source": { en: "api.gbif.org", zh: "api.gbif.org" },
  "api.gbif.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.owid_carbon.name": { en: "Our World in Data CO2", zh: "Our World in Data 碳排資料" },
  "api.owid_carbon.desc": {
    en: "Comprehensive CO2 and greenhouse gas emissions dataset by country. Annual emissions, per capita, cumulative, by sector since 1750.",
    zh: "各國完整 CO2 及溫室氣體排放資料集。自 1750 年起的年度排放量、人均、累計及各部門排放。",
  },
  "api.owid_carbon.source": { en: "github.com/owid/co2-data (Our World in Data)", zh: "github.com/owid/co2-data（Our World in Data）" },
  "api.owid_carbon.format": { en: "CSV/JSON via GitHub, free, no key required", zh: "CSV/JSON 透過 GitHub，免費，無需金鑰" },

  "api.climate_watch.name": { en: "Climate Watch", zh: "Climate Watch 氣候觀測" },
  "api.climate_watch.desc": {
    en: "WRI Climate Watch: NDC targets, historical emissions by country/sector, climate indicators, and Paris Agreement tracking.",
    zh: "WRI 氣候觀測：NDC 目標、各國/部門歷史排放、氣候指標及巴黎協定追蹤。",
  },
  "api.climate_watch.source": { en: "www.climatewatchdata.org (WRI)", zh: "www.climatewatchdata.org（世界資源研究所）" },
  "api.climate_watch.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.open_climate_data.name": { en: "Open Climate Data", zh: "開放氣候資料" },
  "api.open_climate_data.desc": {
    en: "Curated open datasets: global temperature records (GISTEMP, HadCRUT), sea level, Arctic ice extent from multiple research institutions.",
    zh: "精選開放資料集：全球溫度紀錄（GISTEMP、HadCRUT）、海平面、北極冰層範圍，來自多個研究機構。",
  },
  "api.open_climate_data.source": { en: "github.com/openclimatedata", zh: "github.com/openclimatedata" },
  "api.open_climate_data.format": { en: "CSV via GitHub, free, no key required", zh: "CSV 透過 GitHub，免費，無需金鑰" },

  "api.climate_trace.name": { en: "Climate TRACE", zh: "Climate TRACE 排放追蹤" },
  "api.climate_trace.desc": {
    en: "Independent facility-level GHG emissions tracking using satellite and AI. Covers power plants, factories, oil/gas, shipping, aviation.",
    zh: "利用衛星與 AI 獨立追蹤設施級溫室氣體排放。涵蓋發電廠、工廠、油氣、航運、航空。",
  },
  "api.climate_trace.source": { en: "api.climatetrace.org", zh: "api.climatetrace.org" },
  "api.climate_trace.format": { en: "JSON REST API, free, no key required", zh: "JSON REST API，免費，無需金鑰" },

  "api.climatiq.name": { en: "Climatiq Emission Factors", zh: "Climatiq 排放因子" },
  "api.climatiq.desc": {
    en: "Emission factor database for carbon footprint calculations. Convert activities (flights, electricity, shipping) to CO2 equivalents.",
    zh: "碳足跡計算排放因子資料庫。將活動（飛行、用電、運輸）轉換為 CO2 當量。",
  },
  "api.climatiq.source": { en: "api.climatiq.io", zh: "api.climatiq.io" },
  "api.climatiq.format": { en: "JSON REST API, free tier with API key", zh: "JSON REST API，有免費方案，需 API 金鑰" },

  "api.open_charge_map.name": { en: "Open Charge Map", zh: "Open Charge Map 充電站" },
  "api.open_charge_map.desc": {
    en: "Global electric vehicle charging station directory. 300,000+ locations with real-time availability, connector types, and pricing.",
    zh: "全球電動車充電站目錄。300,000+ 站點，提供即時可用性、接頭類型及定價資訊。",
  },
  "api.open_charge_map.source": { en: "api.openchargemap.io", zh: "api.openchargemap.io" },
  "api.open_charge_map.format": { en: "JSON REST API, free, API key optional", zh: "JSON REST API，免費，API 金鑰可選" },

  "api.nrel_alt_fuel.name": { en: "NREL Alt Fuel Stations", zh: "NREL 替代燃料站" },
  "api.nrel_alt_fuel.desc": {
    en: "U.S. alternative fuel station locations: EV charging, biodiesel, CNG, E85, hydrogen, LNG, propane stations nationwide.",
    zh: "美國替代燃料站點：電動車充電、生質柴油、CNG、E85、氫能、LNG、丙烷站點全國分佈。",
  },
  "api.nrel_alt_fuel.source": { en: "developer.nrel.gov (AFDC)", zh: "developer.nrel.gov（替代燃料資料中心）" },
  "api.nrel_alt_fuel.format": { en: "JSON REST API, requires free API key", zh: "JSON REST API，需申請免費金鑰" },
};

export function t(key: string, lang: Lang, params?: Record<string, string | number>): string {
  const entry = translations[key];
  let text = entry?.[lang] ?? entry?.en ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v));
    }
  }
  return text;
}
