# AI Sustainability Platform — 建置工作清單

Generated: 2026-03-08 | Updated: 2026-03-08 v3

---

# 核心策略

> **數據來源串接最優先**。先把 31 個資料來源全部接通，系統架構完整跑起來。
> ac-3090 ML 訓練/推論暫不進行，後續再接入。

### 執行順序

```
Phase 1  專案骨架 + 基礎框架
   ↓
Phase 2  31 個 Connectors 全部串接（核心工作）
   ↓
Phase 3  資料 Pipeline — 整合各來源數據
   ↓
Phase 4  Dashboard — 展示真實數據
   ↓
Phase 5  API 健康監控
   ↓
Phase 6  多代理決策系統（Groq LLM）
   ↓
Phase 7  AI 模型層（ac-3090，後續再做）
```

### 機器分工（本階段）

| 機器 | 角色 | 任務 |
|------|------|------|
| **MacBook Pro** | 開發 + 執行 | 所有開發、connector 測試、pipeline 執行 |
| **ac-mac** | 排程 + 監控 | cron 定時擷取、API 監控、TG 通知 |
| **GitHub Actions** | CI/CD | lint/test、每日更新、dashboard 部署 |
| **ac-3090** | 暫不使用 | Phase 7 再接入做 ML 訓練/推論 |

---

# Phase 0: 環境確認 (0.5 天)

- [ ] 確認 `ai-cooperation` org 可建立 repo
- [ ] 申請 Groq API Key（https://console.groq.com）
- [ ] MacBook Python 版本確認（需 3.11+）
- [ ] MacBook Node.js 版本確認（需 20+）
- [ ] ac-mac Python 版本 + 可用性確認

---

# Phase 1: 專案骨架 + 基礎框架 (1-2 天)

## 1.1 Repo 初始化

- [ ] 在 `ai-cooperation` org 建立 `ai-sustainability-platform` repo
- [ ] 目錄結構建立：
  ```
  ai-sustainability-platform/
  ├── src/
  │   ├── registry/           # 資料集 registry
  │   │   ├── models.py       # Pydantic schema
  │   │   ├── loader.py       # YAML 載入驗證
  │   │   └── cli.py          # CLI 工具
  │   ├── connectors/         # 31 個 API 連接器
  │   │   ├── base.py         # BaseConnector ABC
  │   │   ├── energy/
  │   │   ├── climate/
  │   │   ├── environment/
  │   │   ├── agriculture/
  │   │   ├── transport/
  │   │   └── carbon/
  │   ├── pipelines/          # ETL 管線
  │   │   └── base.py
  │   ├── agents/             # 多代理系統（Phase 6）
  │   ├── monitor/            # API 健康監控
  │   └── utils/
  │       ├── config.py       # 環境變數管理
  │       ├── logging.py      # 統一 logging
  │       └── telegram.py     # TG 通知
  ├── data/
  │   ├── registry/           # datasets.yaml
  │   ├── raw/                # 原始資料（gitignore）
  │   ├── processed/          # 處理後（gitignore）
  │   └── cache/              # API 快取（gitignore）
  ├── dashboard/              # TailAdmin Next.js（Phase 4）
  ├── tests/
  │   ├── unit/
  │   └── integration/
  ├── scripts/
  ├── .github/workflows/
  ├── pyproject.toml
  ├── CLAUDE.md
  └── .gitignore
  ```
- [ ] `pyproject.toml`（uv，依賴分組）
- [ ] `.gitignore`
- [ ] `CLAUDE.md`
- [ ] `.env.example`

## 1.2 開發環境

- [ ] uv 虛擬環境 + 依賴安裝
- [ ] pre-commit hooks（ruff）
- [ ] GitHub Actions CI（lint + test）

## 1.3 核心框架

- [ ] `BaseConnector` ABC：
  - `fetch()` → 抓原始資料
  - `validate()` → schema 驗證
  - `normalize()` → 標準化 DataFrame
  - `cache_key()` → 快取識別
  - `health_check()` → API 可用性
- [ ] `Config`（.env 讀取）
- [ ] `Logger`（統一格式 + TG hook）
- [ ] 錯誤類別（ConnectorError, ValidationError）
- [ ] `datasets.yaml` Pydantic schema

---

# Phase 2: 31 個 Connectors 串接 (5-8 天) ⭐ 核心

> 按「無需 Key → 需 Key」順序開發，每完成一個立即測試驗證。

## 2.1 Dataset Registry

- [ ] 設計 `datasets.yaml` 完整格式
- [ ] 寫入全部 31 個資料集定義
- [ ] Registry CLI：list / search / validate / info

## 2.2 能源領域 (7 個)

| # | Connector | API | Key | 優先 |
|---|-----------|-----|-----|------|
| 1 | `OpenMeteoSolarConnector` | Open-Meteo Solar | 無需 | P1 |
| 2 | `NASAPowerConnector` | NASA POWER | 無需 | P1 |
| 3 | `CarbonIntensityUKConnector` | UK Grid CO2 | 無需 | P1 |
| 4 | `OpenPowerSystemConnector` | EU Power Data | 無需 | P1 |
| 5 | `EIAConnector` | US Energy | 需申請 | P2 |
| 6 | `ElectricityMapsConnector` | Global CO2 | 需申請 | P2 |
| 7 | `NRELConnector` | Solar+Wind+PV | 需申請 | P2 |

- [ ] #1 OpenMeteoSolarConnector + test
- [ ] #2 NASAPowerConnector + test
- [ ] #3 CarbonIntensityUKConnector + test
- [ ] #4 OpenPowerSystemConnector + test
- [ ] #5 EIAConnector + test
- [ ] #6 ElectricityMapsConnector + test
- [ ] #7 NRELConnector + test

## 2.3 氣候領域 (6 個)

| # | Connector | API | Key |
|---|-----------|-----|-----|
| 8 | `OpenMeteoWeatherConnector` | Weather forecast+history | 無需 |
| 9 | `OpenMeteoClimateConnector` | IPCC projections | 無需 |
| 10 | `NOAAGHGConnector` | Mauna Loa CO2/CH4 | 無需 |
| 11 | `WorldBankClimateConnector` | Country climate data | 無需 |
| 12 | `NOAACDOConnector` | Historical observations | 需申請 |
| 13 | `CopernicusCDSConnector` | ERA5 reanalysis | 需申請 |

- [ ] #8 OpenMeteoWeatherConnector + test
- [ ] #9 OpenMeteoClimateConnector + test
- [ ] #10 NOAAGHGConnector + test
- [ ] #11 WorldBankClimateConnector + test
- [ ] #12 NOAACDOConnector + test
- [ ] #13 CopernicusCDSConnector + test

## 2.4 環境領域 (7 個)

| # | Connector | API | Key |
|---|-----------|-----|-----|
| 14 | `OpenMeteoAirQualityConnector` | Global AQ | 無需 |
| 15 | `EPAEnvirofactsConnector` | US emissions/water/waste | 無需 |
| 16 | `EPAWaterQualityConnector` | US water quality | 無需 |
| 17 | `EmissionsAPIConnector` | Sentinel-5P satellite | 無需 |
| 18 | `OpenAQConnector` | Global AQ stations | 需申請 |
| 19 | `AQICNConnector` | Real-time AQI | 需申請 |
| 20 | `GlobalForestWatchConnector` | Deforestation | 需申請 |

- [ ] #14 OpenMeteoAirQualityConnector + test
- [ ] #15 EPAEnvirofactsConnector + test
- [ ] #16 EPAWaterQualityConnector + test
- [ ] #17 EmissionsAPIConnector + test
- [ ] #18 OpenAQConnector + test
- [ ] #19 AQICNConnector + test
- [ ] #20 GlobalForestWatchConnector + test

## 2.5 農業領域 (4 個)

| # | Connector | API | Key |
|---|-----------|-----|-----|
| 21 | `FAOSTATConnector` | UN agriculture | 無需 |
| 22 | `EUAgriFoodConnector` | EU agriculture | 無需 |
| 23 | `USDANASSConnector` | US agriculture | 需申請 |
| 24 | `GBIFConnector` | Biodiversity | 需申請 |

- [ ] #21 FAOSTATConnector + test
- [ ] #22 EUAgriFoodConnector + test
- [ ] #23 USDANASSConnector + test
- [ ] #24 GBIFConnector + test

## 2.6 碳排/ESG 領域 (5 個)

| # | Connector | API | Key |
|---|-----------|-----|-----|
| 25 | `OWIDCarbonConnector` | OWID CO2 dataset | 無需 |
| 26 | `ClimateWatchConnector` | GHG + NDC | 無需 |
| 27 | `OpenClimateDataConnector` | UNFCCC data | 無需 |
| 28 | `ClimateTRACEConnector` | Global emissions | 無需(beta) |
| 29 | `ClimatiqConnector` | Emission factors | 需申請 |

- [ ] #25 OWIDCarbonConnector + test
- [ ] #26 ClimateWatchConnector + test
- [ ] #27 OpenClimateDataConnector + test
- [ ] #28 ClimateTRACEConnector + test
- [ ] #29 ClimatiqConnector + test

## 2.7 交通/城市領域 (2 個)

| # | Connector | API | Key |
|---|-----------|-----|-----|
| 30 | `OpenChargeMapConnector` | EV charging | 可選 |
| 31 | `NRELAltFuelConnector` | Alt fuel stations | 需申請 |

- [ ] #30 OpenChargeMapConnector + test
- [ ] #31 NRELAltFuelConnector + test

## 2.8 測試驗收

- [ ] 31 個 connector 全部通過 unit test
- [ ] Integration test（實際 API 呼叫）通過
- [ ] 一鍵執行全部 connector 的 smoke test 腳本
- [ ] 覆蓋率 > 80%

---

# Phase 3: 資料 Pipeline (3-4 天)

## 3.1 ETL 框架

- [ ] `BasePipeline`（extract → transform → load → notify）
- [ ] 資料驗證層（schema check, 缺值偵測）
- [ ] Parquet 分區存放（`data/processed/{domain}/{dataset}/{date}.parquet`）
- [ ] 元數據追蹤（`metadata.json`）

## 3.2 領域 Pipeline（6 條）

- [ ] `EnergyPipeline` — 合併 7 個能源來源
- [ ] `ClimatePipeline` — 整合 6 個氣候來源
- [ ] `EnvironmentPipeline` — 整合 7 個環境來源
- [ ] `AgriculturePipeline` — 整合 4 個農業來源
- [ ] `CarbonPipeline` — 整合 5 個碳排來源
- [ ] `CrossDomainPipeline` — 跨領域關聯分析

## 3.3 排程

- [ ] GitHub Actions `daily-update.yml`（每日 UTC 06:00）
- [ ] GitHub Actions `hourly-realtime.yml`（碳強度、空品）
- [ ] ac-mac cron（高頻：每 30 分鐘 Carbon Intensity UK）
- [ ] 失敗 → TG 告警
- [ ] 每日執行摘要 → TG 訊息

---

# Phase 4: Dashboard (5-7 天)

## 4.1 前端建置

- [ ] Clone TailAdmin Free Next.js Dashboard
- [ ] 客製化主題（永續綠色色系）
- [ ] 8 個頁面：
  - **Overview** — 全球永續 KPI 總覽
  - **Energy** — 電力/太陽能/碳強度地圖 + 圖表
  - **Climate** — CO2 濃度、氣溫趨勢、氣候預測
  - **Environment** — 空品地圖、水質、森林覆蓋
  - **Agriculture** — 產量趨勢、食品價格
  - **Carbon** — 國家排放排名、設施追蹤
  - **Forecasts** — AI 預測 + 代理辯論（Phase 6 後啟用）
  - **Status** — API 健康狀態

## 4.2 資料接入

- [ ] 靜態 JSON API（GitHub Actions 更新 → Pages 提供）
- [ ] Dashboard 讀取 processed data 產生圖表
- [ ] 自動 rebuild（data 更新 → trigger build）

## 4.3 部署

- [ ] GitHub Pages 部署 workflow
- [ ] 自動部署（push → build → deploy）

---

# Phase 5: API 健康監控 (1-2 天)

- [ ] `HealthChecker`（31 個 API 全面檢查）
- [ ] `status.json` 產出
- [ ] 30 天 uptime 追蹤
- [ ] API down → TG 通知
- [ ] GitHub Actions 每 6 小時執行
- [ ] Dashboard Status 頁面對接

---

# Phase 6: 多代理決策系統 (5-7 天)

## 6.1 Groq LLM 整合

- [ ] `GroqClient`（Llama 3.3 70B，14,400 req/day 免費）
- [ ] Rate limiting + retry + token 計數
- [ ] MCP LLM fallback

## 6.2 代理實作（7 個）

- [ ] `SignalAgent` — 資料異常/趨勢偵測
- [ ] `NewsAgent` — 新聞事件 + 情感分析
- [ ] `AnalystAgent` — 信號分析 + 假設生成
- [ ] `DebateAgent (Optimist)` — 樂觀情境
- [ ] `DebateAgent (Pessimist)` — 悲觀情境
- [ ] `DebateAgent (Statistician)` — 統計模型
- [ ] `JudgeAgent` — 綜合裁決

## 6.3 預測工作流

- [ ] `ForecastOrchestrator`（信號→分析→辯論→裁決）
- [ ] 預測結果 JSON 輸出
- [ ] Dashboard Forecasts 頁面對接
- [ ] 定期 Claude 對話 review 預測品質

---

# Phase 7: AI 模型層 — ac-3090 (後續再做)

> 待 Phase 1-6 完成後，再接入 ac-3090：
> - PyTorch 時序預測模型訓練
> - FastAPI 推論服務
> - 模型自動 retrain 排程

---

# 預估時程

| Phase | 內容 | 天數 | 累計 |
|-------|------|------|------|
| 0 | 環境確認 | 0.5 | 0.5 |
| 1 | 專案骨架 + 框架 | 1-2 | 1.5-2.5 |
| 2 | **31 個 Connectors** | **5-8** | **6.5-10.5** |
| 3 | 6 條 Pipeline | 3-4 | 9.5-14.5 |
| 4 | Dashboard 8 頁面 | 5-7 | 14.5-21.5 |
| 5 | API 監控 | 1-2 | 15.5-23.5 |
| 6 | 多代理系統 | 5-7 | 20.5-30.5 |

**Phase 1-6 約 3-5 週完成，系統完整可用**
**Phase 7 (ac-3090 ML) 後續再接入**

---

# 立即執行：Phase 0 確認清單

- [ ] `ai-cooperation` org 建 repo 權限
- [ ] Groq API Key
- [ ] MacBook: `python3 --version` (需 3.11+)
- [ ] MacBook: `node --version` (需 20+)
- [ ] ac-mac: Python 版本 + 負載

**確認完畢後 → 開始 Phase 1**
