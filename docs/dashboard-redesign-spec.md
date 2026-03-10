# Dashboard 數據呈現重構規格書

## 問題根因

`scripts/export_dashboard_json.py` 第 57-69 行把**所有數值欄位**都當成 KPI 輸出，
導致 latitude, longitude, year, facility_id, population, gdp 等無意義欄位全部出現在 dashboard。
同時 time_series 也輸出所有數值欄位（OPSD 268 個歐洲國家變數全部灌入）。

## 修復策略

### 核心：KPI 白名單 + 時間序列白名單

每個 domain 明確定義「哪些欄位是 KPI」和「哪些欄位畫 sparkline」，
其餘全部過濾掉。

---

## 各 Domain 數據設計

### Energy（能源）

**KPI 白名單：**
| KPI Key | 來源 | 說明 | 單位 |
|---------|------|------|------|
| shortwave_radiation | open_meteo_solar | 台北總輻射量 | W/m² |
| direct_radiation | open_meteo_solar | 台北直射輻射 | W/m² |
| diffuse_radiation | open_meteo_solar | 台北散射輻射 | W/m² |
| solar_radiation | nasa_power | NASA 日均太陽輻射 | kWh/m²/day |
| temperature | nasa_power | NASA 氣溫 | °C |
| intensity_forecast | carbon_intensity_uk | 英國碳強度 | gCO₂/kWh |
| DE_solar_generation_actual | open_power_system | 德國太陽能發電 | MW |
| DE_wind_generation_actual | open_power_system | 德國風電發電 | MW |
| DE_load_actual_entsoe_transparency | open_power_system | 德國電力負載 | MW |
| DE_price_day_ahead | open_power_system | 德國電價 | €/MWh |

**Sparkline 白名單：**
- open_meteo_solar: `shortwave_radiation`, `direct_radiation`
- nasa_power: `solar_radiation`, `temperature`
- open_power_system: `DE_solar_generation_actual`, `DE_wind_generation_actual`

**排除：** latitude, longitude, 以及非 DE 的所有 268 個國家欄位（保留 DE 代表性即可）

---

### Climate（氣候）

**KPI 白名單：**
| KPI Key | 來源 | 說明 | 單位 |
|---------|------|------|------|
| co2_ppm | noaa_ghg | 全球 CO₂ 濃度 | ppm |
| trend | noaa_ghg | CO₂ 趨勢值 | ppm |
| temperature_max | open_meteo_climate | 台北最高溫 | °C |
| temperature_min | open_meteo_climate | 台北最低溫 | °C |
| precipitation | open_meteo_climate | 台北降水 | mm |

**Sparkline 白名單：**
- noaa_ghg: `co2_ppm`
- open_meteo_climate: `temperature_max`, `precipitation`

**排除：** lat, lon, value（world_bank 不明確欄位）

---

### Environment（環境）

**KPI 白名單：**
| KPI Key | 來源 | 說明 | 單位 |
|---------|------|------|------|
| pm2_5 | open_meteo_air_quality | 台北 PM2.5 | µg/m³ |
| pm10 | open_meteo_air_quality | 台北 PM10 | µg/m³ |
| no2 | open_meteo_air_quality | 台北 NO₂ | µg/m³ |
| o3 | open_meteo_air_quality | 台北臭氧 | µg/m³ |
| co | open_meteo_air_quality | 台北 CO | µg/m³ |
| aqi | open_meteo_air_quality / aqicn | 空氣品質指數 | - |

**Sparkline 白名單：**
- open_meteo_air_quality: `pm2_5`, `pm10`, `no2`, `o3`

**排除：** latitude, longitude, facility_id, year, co2e_emission, pm25（重複）, so2（只 1 筆）

---

### Agriculture（農業）

**KPI 白名單：**
| KPI Key | 來源 | 說明 | 單位 |
|---------|------|------|------|
| price | eu_agri_food | 農產品價格指數 | - |

**Sparkline 白名單：**
- eu_agri_food: `price`

**排除：** latitude, longitude（GBIF 座標，不是 KPI）

**特殊處理：** GBIF biodiversity 的 record_count 本身就是 KPI（觀測數量），
不需要從數值欄位提取。在頁面直接用 `data.record_count`。

---

### Carbon（碳排放）

**KPI 白名單：**
| KPI Key | 來源 | 說明 | 單位 |
|---------|------|------|------|
| co2 | owid_carbon | 全球 CO₂ 排放 | Mt |
| co2_per_capita | owid_carbon | 人均 CO₂ | t/人 |
| energy_per_capita | owid_carbon | 人均能源消耗 | kWh |
| Fossil-Fuel-And-Industry | open_climate_data | 化石+工業排放 | GtC |
| Land-Use-Change-Emissions | open_climate_data | 土地利用排放 | GtC |
| Ocean-Sink | open_climate_data | 海洋碳匯 | GtC |
| Land-Sink | open_climate_data | 陸地碳匯 | GtC |

**Sparkline 白名單：**
- owid_carbon: `co2`, `co2_per_capita`
- open_climate_data: `Fossil-Fuel-And-Industry`

**排除：** year, population, gdp, value（不明確）, Year（重複）, Budget-Imbalance, Atmospheric-Growth

---

## 首頁 6 張 KPI 卡片重新設計

每張卡片的**標題、數值、sparkline 必須來自同一主題**：

| # | 標題 | 數值來源 | 單位 | Sparkline | 顏色 |
|---|------|---------|------|-----------|------|
| 1 | 全球 CO₂ 濃度 | climate → co2_ppm latest | ppm | noaa_ghg → co2_ppm 趨勢 | 紅 |
| 2 | 台北太陽輻射 | energy → shortwave_radiation mean | W/m² | open_meteo_solar → shortwave_radiation | 綠 |
| 3 | 台北空氣品質 | environment → pm2_5 latest | µg/m³ | open_meteo_air_quality → pm2_5 | 綠/紅 |
| 4 | 全球碳排放 | carbon → co2 latest | Mt CO₂ | owid_carbon → co2 | 紅 |
| 5 | 台北氣溫 | climate → temperature_max latest | °C | open_meteo_climate → temperature_max | 藍 |
| 6 | API 健康 | status → healthy/total | - | 無 | 灰 |

**原則：**
- 每張卡片只看一個指標
- sparkline 就是該指標的時間序列，不是別的東西
- 趨勢箭頭根據 latest vs mean 判斷（PM2.5 下降=好，CO₂ 上升=壞）

---

## 各 Domain 頁面 Sparkline 設計

每個 domain 頁面的大型趨勢圖：
- **Energy:** 台北 24 小時太陽輻射曲線（shortwave_radiation）
- **Climate:** CO₂ ppm 歷史月度趨勢 或 台北溫度 7 天趨勢
- **Environment:** 台北 PM2.5 7 天趨勢
- **Agriculture:** 價格指數趨勢（如果有足夠數據點）
- **Carbon:** 全球年度 CO₂ 排放趨勢

---

## 時間序列取樣策略

- 每個 source 的 time_series：取最後 **168 筆**（7 天 × 24 小時）而非 30 筆
- 如果是日級數據（NASA POWER）：取最後 **90 筆**（90 天）
- 如果是年度數據（OWID）：取最後 **30 筆**（30 年）
