"""台灣上市櫃公司月營收連接器。

資料來源：
- TWSE 上市: https://openapi.twse.com.tw/v1/opendata/t187ap05_L
- TPEx 上櫃: https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，處理逗號、空值、破折號。"""
    if value is None or str(value).strip() in ("", "-", "－"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_roc_year_month(ym_str: str) -> datetime | None:
    """將民國年月（如 '11501'）轉為西元 datetime。

    格式：前 3~4 碼為民國年，後 2 碼為月份。
    """
    if not ym_str or not ym_str.strip():
        return None
    s = ym_str.strip()
    if len(s) < 4:
        return None
    try:
        month = int(s[-2:])
        roc_year = int(s[:-2])
        ad_year = roc_year + 1911
        return datetime(ad_year, month, 1, tzinfo=UTC)
    except (ValueError, TypeError):
        return None


class TWSERevenueConnector(BaseConnector):
    """台灣上市櫃公司月營收連接器。

    合併 TWSE（上市）與 TPEx（上櫃）公司月營收資料，
    包含當月營收、上月營收、年增率、月增率、累計營收等。
    """

    TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O"

    @property
    def name(self) -> str:
        return "twse_revenue"

    @property
    def domain(self) -> str:
        return "corporate"

    def fetch(self, **params: Any) -> list:
        """從 TWSE 與 TPEx 取得月營收資料。

        Returns:
            合併後的營收資料列表。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        timeout = params.get("timeout", 30)
        results = []

        for url, market in [(self.TWSE_URL, "twse"), (self.TPEX_URL, "tpex")]:
            try:
                resp = requests.get(url, timeout=timeout)
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
        """將原始營收資料轉換為標準化 DataFrame。

        TWSE 與 TPEx 的欄位名稱相同（皆為中文）。
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: 無營收資料")

        rows = []
        for r in raw_data:
            market = r.get("_market", "twse")
            ym_str = r.get("資料年月", "")
            timestamp = _parse_roc_year_month(ym_str)

            rows.append({
                "stock_id": r.get("公司代號", ""),
                "company_name": r.get("公司名稱", ""),
                "industry": r.get("產業別", ""),
                "revenue_current_month": _safe_numeric(
                    r.get("營業收入-當月營收")
                ),
                "revenue_prev_month": _safe_numeric(
                    r.get("營業收入-上月營收")
                ),
                "revenue_yoy_same_month": _safe_numeric(
                    r.get("營業收入-去年當月營收")
                ),
                "mom_change_pct": _safe_numeric(
                    r.get("營業收入-上月比較增減(%)")
                ),
                "yoy_change_pct": _safe_numeric(
                    r.get("營業收入-去年同月增減(%)")
                ),
                "ytd_revenue": _safe_numeric(
                    r.get("累計營業收入-當月累計營收")
                ),
                "ytd_yoy_change_pct": _safe_numeric(
                    r.get("累計營業收入-前期比較增減(%)")
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
