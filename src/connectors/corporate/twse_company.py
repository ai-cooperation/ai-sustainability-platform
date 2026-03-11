"""台灣上市櫃公司基本資料連接器。

資料來源：
- TWSE 上市公司: https://openapi.twse.com.tw/v1/opendata/t187ap03_L
- TPEx 上櫃公司: https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O
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


class TWSECompanyConnector(BaseConnector):
    """台灣上市櫃公司基本資料連接器。

    合併 TWSE（上市）與 TPEx（上櫃）公司基本資料，
    包含股票代號、公司名稱、產業別、董事長、上市日期等。
    """

    TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"

    @property
    def name(self) -> str:
        return "twse_company"

    @property
    def domain(self) -> str:
        return "corporate"

    def fetch(self, **params: Any) -> list:
        """從 TWSE 與 TPEx 取得上市櫃公司基本資料。

        Returns:
            合併後的公司資料列表，每筆附加 _market 標記。

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
        """將原始資料轉換為標準化 DataFrame。

        TWSE 欄位為中文，TPEx 欄位為英文，需分別對應。
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: 無公司資料")

        rows = []
        now = datetime.now(tz=UTC)

        for r in raw_data:
            market = r.get("_market", "")
            if market == "twse":
                rows.append({
                    "stock_id": r.get("公司代號", ""),
                    "company_name": r.get("公司名稱", ""),
                    "company_abbr": r.get("公司簡稱", ""),
                    "industry": r.get("產業別", ""),
                    "chairman": r.get("董事長", ""),
                    "listing_date": r.get("上市日期", ""),
                    "paid_in_capital": _safe_numeric(r.get("實收資本額")),
                    "address": r.get("住址", ""),
                    "website": r.get("網址", ""),
                    "market": "twse",
                    "timestamp": now,
                })
            else:
                rows.append({
                    "stock_id": r.get("SecuritiesCompanyCode", ""),
                    "company_name": r.get("CompanyName", ""),
                    "company_abbr": r.get("CompanyAbbreviation", ""),
                    "industry": r.get("SecuritiesIndustryCode", ""),
                    "chairman": r.get("Chairman", ""),
                    "listing_date": r.get("DateOfListing", ""),
                    "paid_in_capital": _safe_numeric(
                        r.get("Paidin.Capital.NTDollars")
                    ),
                    "address": r.get("Address", ""),
                    "website": r.get("WebAddress", ""),
                    "market": "tpex",
                    "timestamp": now,
                })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用較短超時。"""
        return {"timeout": 10}
