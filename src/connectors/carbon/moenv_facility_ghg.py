"""環境部事業溫室氣體排放量盤查資料連接器（設施層級）。

資料來源：環境部環境資料開放平臺
API: https://data.moenv.gov.tw/api/v2/GHG_P_01
包含個別事業（設施）的直接排放、能源間接排放、排放總量等。
可用於比對上市櫃公司的碳排放資料。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError

# MOENV API 預設每頁上限
_DEFAULT_PAGE_SIZE = 1000


class MoenvFacilityGhgConnector(BaseConnector):
    """環境部事業溫室氣體排放量盤查連接器（設施層級）。

    提供個別事業的年度溫室氣體直接排放與間接排放量，
    可與上市櫃公司名稱交叉比對。
    """

    BASE_URL = "https://data.moenv.gov.tw/api/v2/GHG_P_01"
    DEFAULT_API_KEY = "e8dd42e6-9b8b-43f8-991e-b3dee723a52d"

    # 原始欄位名稱對照（環境部 API 回傳的中文 key）
    FIELD_MAP = {
        "盤查年度": "report_year",
        "事業名稱": "facility_name",
        "登記編號": "registration_no",
        "行業代碼": "industry_code",
        "行業名稱": "industry_name",
        "縣市": "county",
        "直接排放(公噸CO2e)": "scope1_emissions",
        "能源間接排放(公噸CO2e)": "scope2_emissions",
        "排放總量(公噸CO2e)": "total_emissions",
    }

    @property
    def name(self) -> str:
        return "moenv_facility_ghg"

    @property
    def domain(self) -> str:
        return "carbon"

    def _api_key(self) -> str:
        """取得 API 金鑰，優先使用 settings。"""
        key = getattr(self._settings, "moenv_api_key", "")
        return key if key else self.DEFAULT_API_KEY

    def fetch(self, **params: Any) -> list[dict]:
        """從環境部 API 分頁取得所有設施排放資料。

        Args:
            limit: 每頁筆數（預設 1000）。
            offset: 起始偏移（預設 0，用於健康檢查等）。
            max_pages: 最大頁數限制（預設 100，防止無限迴圈）。

        Returns:
            所有頁面的 records 合併列表。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        limit = params.get("limit", _DEFAULT_PAGE_SIZE)
        offset = params.get("offset", 0)
        max_pages = params.get("max_pages", 100)

        all_records: list[dict] = []

        for _ in range(max_pages):
            query: dict[str, Any] = {
                "format": "json",
                "offset": offset,
                "limit": limit,
                "api_key": self._api_key(),
            }

            try:
                response = requests.get(self.BASE_URL, params=query, timeout=30)
                response.raise_for_status()
            except requests.RequestException as exc:
                raise ConnectorError(
                    f"{self.name}: API 請求失敗 - {exc}"
                ) from exc

            data = response.json()
            records = data.get("records", [])
            all_records.extend(records)

            # 最後一頁：回傳筆數少於 limit 表示已到底
            if len(records) < limit:
                break

            offset += limit

        return all_records

    def normalize(self, raw_data: list[dict]) -> pd.DataFrame:
        """將原始設施排放資料轉換為標準化 DataFrame。

        Args:
            raw_data: fetch() 回傳的 records 列表。

        Returns:
            包含標準化欄位的 DataFrame。
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: 回應中無設施排放資料")

        rows = []
        for record in raw_data:
            roc_year = record.get("盤查年度", "")
            ad_year = _safe_int(roc_year)
            year = ad_year + 1911 if ad_year else None
            timestamp = f"{year}-01-01" if year else ""

            rows.append({
                "facility_name": record.get("事業名稱", ""),
                "company_name": record.get("事業名稱", ""),
                "registration_no": record.get("登記編號", ""),
                "industry_code": record.get("行業代碼", ""),
                "industry_name": record.get("行業名稱", ""),
                "county": record.get("縣市", ""),
                "scope1_emissions": _safe_numeric(
                    record.get("直接排放(公噸CO2e)")
                ),
                "scope2_emissions": _safe_numeric(
                    record.get("能源間接排放(公噸CO2e)")
                ),
                "total_emissions": _safe_numeric(
                    record.get("排放總量(公噸CO2e)")
                ),
                "report_year": year,
                "timestamp": timestamp,
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用最小請求量。"""
        return {"limit": 1}


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為浮點數，無效值回傳 None。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        # 移除千分位逗號
        cleaned = str(value).replace(",", "")
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """安全地將字串轉為整數，無效值回傳 None。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None
