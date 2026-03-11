"""台灣上市櫃公司員工薪資與性別平等資料連接器。

資料來源（ESG 人力資源）：
- TWSE 上市: https://openapi.twse.com.tw/v1/opendata/t187ap46_L_5
- TPEx 上櫃: https://www.tpex.org.tw/openapi/v1/t187ap46_O_5
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError
from src.connectors.corporate._ssl_helper import create_tw_gov_session


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，處理逗號、百分號、空值、破折號。"""
    if value is None or str(value).strip() in ("", "-", "－"):
        return None
    s = str(value).replace(",", "").replace("%", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _find_field(record: dict, candidates: list[str]) -> Any:
    """從候選欄位名稱中找到第一個存在的值。

    TWSE 與 TPEx 的欄位名稱略有不同（TPEx 帶括號說明），
    使用模糊比對找到正確欄位。
    """
    for key in record:
        stripped = key.strip()
        for candidate in candidates:
            if candidate in stripped:
                return record[key]
    return None


class TWSEEmployeeConnector(BaseConnector):
    """台灣上市櫃公司員工薪資與性別平等資料連接器。

    合併 TWSE（上市）與 TPEx（上櫃）ESG 人力資源資料，
    包含員工福利平均、薪資平均、非主管薪資中位數、女性主管佔比等。
    """

    TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap46_L_5"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1/t187ap46_O_5"

    @property
    def name(self) -> str:
        return "twse_employee"

    @property
    def domain(self) -> str:
        return "corporate"

    def fetch(self, **params: Any) -> list:
        """從 TWSE 與 TPEx 取得員工薪資與性別平等資料。

        Returns:
            合併後的員工資料列表。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        timeout = params.get("timeout", 30)
        session = create_tw_gov_session()
        results = []

        for url, market in [(self.TWSE_URL, "twse"), (self.TPEX_URL, "tpex")]:
            try:
                resp = session.get(url, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                for record in data:
                    record["_market"] = market
                results.extend(data)
            except requests.RequestException as exc:
                raise ConnectorError(
                    f"{self.name}: {market} API 請求失敗 - {exc}"
                ) from exc

        return results

    def normalize(self, raw_data: list) -> pd.DataFrame:
        """將原始員工資料轉換為標準化 DataFrame。

        TWSE 與 TPEx 的欄位名稱略有不同，使用關鍵字比對。
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: 無員工資料")

        rows = []
        for r in raw_data:
            market = r.get("_market", "twse")
            stock_id = r.get("公司代號", "")
            company_name = r.get("公司名稱", "")

            roc_year = r.get("報告年度", "")
            try:
                year = int(roc_year) + 1911
                timestamp = datetime(year, 12, 31, tzinfo=UTC)
            except (ValueError, TypeError):
                year = None
                timestamp = datetime.now(tz=UTC)

            rows.append({
                "stock_id": stock_id,
                "company_name": company_name,
                "year": year,
                "avg_employee_benefit": _safe_numeric(
                    _find_field(r, ["員工福利平均數"])
                ),
                "avg_salary": _safe_numeric(
                    _find_field(r, ["員工薪資平均數"])
                ),
                "avg_salary_non_mgr": _safe_numeric(
                    _find_field(r, ["非擔任主管職務之全時員工薪資平均數"])
                ),
                "median_salary_non_mgr": _safe_numeric(
                    _find_field(r, ["非擔任主管之全時員工薪資中位數"])
                ),
                "female_mgr_ratio": _safe_numeric(
                    _find_field(r, ["管理職女性主管佔比"])
                ),
                "market": market,
                "timestamp": timestamp,
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用較短超時。"""
        return {"timeout": 10}
