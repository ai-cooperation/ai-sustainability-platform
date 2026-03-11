"""台灣上市櫃公司綜合損益連接器。

資料來源：
- TWSE 上市: https://openapi.twse.com.tw/v1/opendata/t187ap14_L
- TPEx 上櫃: https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap14_O
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError
from src.connectors.corporate._ssl_helper import create_tw_gov_session


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，處理逗號、空值、破折號。"""
    if value is None or str(value).strip() in ("", "-", "－"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _quarter_to_timestamp(roc_year: str, quarter: str) -> datetime | None:
    """將民國年 + 季別轉為西元 datetime（季末月份首日）。

    例：年度=113, 季別=4 → 2024-12-01 UTC
    """
    try:
        ad_year = int(roc_year) + 1911
        q = int(quarter)
        month = {1: 3, 2: 6, 3: 9, 4: 12}.get(q, 12)
        return datetime(ad_year, month, 1, tzinfo=UTC)
    except (ValueError, TypeError):
        return None


class TWSEIncomeConnector(BaseConnector):
    """台灣上市櫃公司綜合損益表連接器。

    合併 TWSE（上市）與 TPEx（上櫃）公司損益資料，
    包含 EPS、營業收入、營業利益、營業外收支、稅後淨利等。
    """

    TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap14_L"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap14_O"

    @property
    def name(self) -> str:
        return "twse_income"

    @property
    def domain(self) -> str:
        return "corporate"

    def fetch(self, **params: Any) -> list:
        """從 TWSE 與 TPEx 取得綜合損益資料。

        Returns:
            合併後的損益資料列表。

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
        """將原始損益資料轉換為標準化 DataFrame。

        TWSE 使用中文欄位（年度、公司代號），TPEx 混用英文（Year、SecuritiesCompanyCode）。
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: 無損益資料")

        rows = []
        for r in raw_data:
            market = r.get("_market", "twse")

            if market == "twse":
                roc_year = r.get("年度", "")
                quarter = r.get("季別", "")
                stock_id = r.get("公司代號", "")
                company_name = r.get("公司名稱", "")
                industry = r.get("產業別", "")
                eps = _safe_numeric(r.get("基本每股盈餘(元)"))
            else:
                roc_year = r.get("Year", "")
                quarter = r.get("季別", "")
                stock_id = r.get("SecuritiesCompanyCode", "")
                company_name = r.get("CompanyName", "")
                industry = r.get("產業別", "")
                eps = _safe_numeric(r.get("基本每股盈餘"))

            try:
                year = int(roc_year) + 1911
            except (ValueError, TypeError):
                year = None

            timestamp = _quarter_to_timestamp(roc_year, quarter)

            rows.append({
                "stock_id": stock_id,
                "company_name": company_name,
                "industry": industry,
                "year": year,
                "quarter": _safe_numeric(quarter),
                "eps": eps,
                "revenue": _safe_numeric(r.get("營業收入")),
                "operating_profit": _safe_numeric(r.get("營業利益")),
                "non_operating_income": _safe_numeric(
                    r.get("營業外收入及支出")
                ),
                "net_income": _safe_numeric(r.get("稅後淨利")),
                "market": market,
                "timestamp": timestamp,
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用較短超時。"""
        return {"timeout": 10}
