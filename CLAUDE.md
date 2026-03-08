# AI Sustainability Platform — 開發指引

## 專案結構

```
src/
├── registry/       # 資料集 registry (datasets.yaml 管理)
├── connectors/     # 31 個 API 連接器 (按領域分資料夾)
├── pipelines/      # 6 條 ETL 管線
├── agents/         # 多代理決策系統 (Groq LLM)
├── monitor/        # API 健康監控
└── utils/          # 共用工具 (config, logging, telegram)
```

## 開發慣例

- Python 3.12+，用 `uv` 管理依賴
- 所有 connector 繼承 `BaseConnector` (src/connectors/base.py)
- 所有 pipeline 繼承 `BasePipeline` (src/pipelines/base.py)
- 測試：`pytest`，mock API 呼叫，覆蓋率 > 80%
- Linting：`ruff`
- 不可 hardcode API key，一律從 Config 讀取

## 模組邊界（重要）

各模組只透過公開介面溝通，不 import 內部實作：
- `connectors` 不依賴 `pipelines` 或 `agents`
- `pipelines` 依賴 `connectors` 的 `ConnectorResult`
- `agents` 依賴 `pipelines` 的輸出資料
- `monitor` 依賴 `connectors` 的 `health_check()`
- `utils` 被所有模組共用

## 常用指令

```bash
uv run pytest                          # 跑測試
uv run pytest -m "not integration"     # 跳過 API 實測
uv run ruff check src/ tests/          # lint
uv run python -m src.registry.cli list # 列出所有資料集
```

## 資料流

```
API → Connector.fetch() → normalize() → ConnectorResult
  → Pipeline.extract() → transform() → load() → data/processed/*.parquet
  → Dashboard reads JSON → GitHub Pages
```
