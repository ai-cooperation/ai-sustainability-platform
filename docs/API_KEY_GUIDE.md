# API Key 申請指引

本平台整合 31 個永續發展資料來源，其中 13 個免費無需金鑰，18 個需要申請 API Key。

## 快速申請（免費、5 分鐘內搞定）

### 1. EIA — 美國能源資訊署
- **申請網址**: https://www.eia.gov/opendata/register.php
- **步驟**: 填 email → 收信 → 拿 key
- **GitHub Secret 名稱**: `EIA_API_KEY`
- **提供資料**: 美國能源生產、消費、價格、排放數據
- **狀態**: ✅ 已設定

### 2. NREL — 美國國家再生能源實驗室
- **申請網址**: https://developer.nrel.gov/signup/
- **步驟**: 填 email + 姓名 → 即時拿 key
- **GitHub Secret 名稱**: `NREL_API_KEY`
- **提供資料**: 太陽能資源、風力數據、替代燃料站
- **狀態**: ✅ 已設定

### 3. NOAA CDO — 美國國家氣候資料中心
- **申請網址**: https://www.ncdc.noaa.gov/cdo-web/token
- **步驟**: 填 email → 收信 → 拿 token
- **GitHub Secret 名稱**: `NOAA_CDO_TOKEN`
- **提供資料**: 歷史天氣與氣候紀錄
- **狀態**: ✅ 已設定

### 4. OpenAQ — 全球開源空氣品質
- **申請網址**: https://docs.openaq.org/using-the-api/quick-start
- **步驟**: 註冊帳號 → Dashboard 拿 key
- **GitHub Secret 名稱**: `OPENAQ_API_KEY`
- **提供資料**: 100+ 國家、300+ 資料來源的即時空氣品質
- **狀態**: ✅ 已設定

### 5. AQICN — 世界空氣品質指數
- **申請網址**: https://aqicn.org/data-platform/token/
- **步驟**: 填 email → 收信 → 拿 token
- **GitHub Secret 名稱**: `AQICN_API_TOKEN`
- **提供資料**: 12,000+ 監測站即時 AQI（PM2.5, PM10, O3, NO2, SO2, CO）
- **狀態**: ✅ 已設定

### 6. USDA NASS — 美國農業部統計
- **申請網址**: https://quickstats.nass.usda.gov/api/
- **步驟**: 填 email → 即時拿 key
- **GitHub Secret 名稱**: `USDA_NASS_API_KEY`
- **提供資料**: 美國農作物面積、產量、收成、畜牧、價格
- **狀態**: ✅ 已設定

---

## 需要帳號註冊（免費，10-15 分鐘）

### 7. Electricity Maps — 全球電力碳排
- **申請網址**: https://api-portal.electricitymaps.com/
- **步驟**: 註冊 → 選 Free tier → Dashboard 拿 key
- **GitHub Secret 名稱**: `ELECTRICITY_MAPS_API_KEY`
- **提供資料**: 160+ 電力區域即時碳排強度與電力結構
- **狀態**: ✅ 已設定

### 8. Climatiq — 碳排放因子
- **申請網址**: https://www.climatiq.io/pricing
- **步驟**: 註冊 → 選 Free plan → API key
- **GitHub Secret 名稱**: `CLIMATIQ_API_KEY`
- **提供資料**: 碳足跡計算排放因子資料庫
- **狀態**: ✅ 已設定

### 9. Copernicus CDS — 歐盟哥白尼氣候資料庫
- **申請網址**: https://cds.climate.copernicus.eu/user/register
- **步驟**: 註冊 → 接受授權 → Profile 頁面拿 key
- **GitHub Secret 名稱**: `COPERNICUS_CDS_KEY`
- **提供資料**: ERA5 再分析資料、全球大氣與地表變量
- **狀態**: ✅ 已設定

### 10. Open Charge Map — 全球電動車充電站
- **申請網址**: https://openchargemap.org/site/develop/api
- **步驟**: 可選（無 key 也能用，有限速）
- **GitHub Secret 名稱**: `OPEN_CHARGE_MAP_KEY`
- **提供資料**: 300,000+ 充電站位置、即時可用性、定價
- **狀態**: ✅ 已設定

---

## 不需要額外申請的 API（已設定或不需要 key）

### 已設定的 Secrets
| Secret | 用途 | 狀態 |
|--------|------|------|
| `GROQ_API_KEY` | AI 預測 (Groq LLM) | ✅ 已設定 |
| `TELEGRAM_BOT_TOKEN` | 每日通知 | ✅ 已設定 |
| `TELEGRAM_CHAT_ID` | 通知對象 | ✅ 已設定 |

### 免費無需金鑰的 API（13 個）
| API | Domain | 說明 |
|-----|--------|------|
| Open-Meteo Solar | Energy | 太陽輻射預報 |
| NASA POWER | Energy | 衛星氣象與太陽能資料 |
| UK Carbon Intensity | Energy | 英國電網碳排強度 |
| Open Power System | Energy | 歐洲電力系統資料 |
| Open-Meteo Weather | Climate | 全球天氣預報 |
| Open-Meteo Climate | Climate | CMIP6 氣候模型預測 |
| NOAA GHG | Climate | 溫室氣體濃度 |
| World Bank Climate | Climate | 各國氣候發展指標 |
| Open-Meteo Air Quality | Environment | 全球空氣品質預報 |
| EPA Envirofacts | Environment | 美國環境資料 |
| EPA Water Quality | Environment | 美國水質監測 |
| Emissions API | Environment | 衛星 CO2 排放估算 |
| Global Forest Watch | Environment | 森林變化監測 |
| FAOSTAT | Agriculture | 聯合國糧農統計 |
| EU Agriculture | Agriculture | 歐盟農業統計 |
| GBIF | Agriculture | 全球生物多樣性 |
| OWID Carbon | Carbon | Our World in Data CO2 |
| Climate Watch | Carbon | WRI 氣候觀測 |
| Open Climate Data | Carbon | 開放氣候資料集 |
| Climate TRACE | Carbon | 設施級排放追蹤 |

---

## 拿到 Key 後怎麼設定？

### 方法：加到 GitHub Repository Secrets

1. 前往 https://github.com/ai-cooperation/ai-sustainability-platform/settings/secrets/actions
2. 點 **New repository secret**
3. Name 填上面列出的 **GitHub Secret 名稱**
4. Secret 填你拿到的 **API Key**
5. 點 **Add secret**

每加一個 key，對應的 connector 就會在下次排程自動啟用。

### 驗證方式

加完 secret 後，可以手動觸發 workflow 來測試：

```bash
# 觸發每日管線（含 AI 預測）
gh workflow run "Daily Pipeline Update" --repo ai-cooperation/ai-sustainability-platform

# 觸發 API 健康檢查
gh workflow run "API Health Check" --repo ai-cooperation/ai-sustainability-platform
```

在 https://github.com/ai-cooperation/ai-sustainability-platform/actions 查看結果。
