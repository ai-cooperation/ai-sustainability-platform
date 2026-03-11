"""台灣環境部紫外線即時監測資料連接器。

資料來源：環境部環境資料開放平臺
API: https://data.moenv.gov.tw/api/v2/UV_S_01
更新頻率：每小時
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.connectors.base import BaseConnector, ConnectorError
from src.connectors.corporate._ssl_helper import create_tw_gov_session


def _parse_coordinate(value: str | None) -> float | None:
    """解析座標值，支援十進位度數及度分秒 (DMS) 格式。

    十進位範例: "120.85985238" → 120.85985238
    DMS 範例: "121,45,24" → 121 + 45/60 + 24/3600 = 121.7567

    Args:
        value: 原始座標字串。

    Returns:
        十進位度數 float，無效值回傳 None。
    """
    if value is None or value == "":
        return None
    value = value.strip()
    if "," in value:
        parts = value.split(",")
        if len(parts) != 3:
            return None
        try:
            d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return d + m / 60 + s / 3600
        except (ValueError, TypeError):
            return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value: Any) -> float | None:
    """安全地將字串轉為 float，無效值回傳 None。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class MoenvUvConnector(BaseConnector):
    """台灣環境部紫外線指數 (UVI) 即時監測連接器。

    提供全台約 31 個監測站的即時紫外線指數，
    包含站名、縣市、座標、UVI 數值等資訊。
    """

    BASE_URL = "https://data.moenv.gov.tw/api/v2/UV_S_01"
    DEFAULT_API_KEY = "e8dd42e6-9b8b-43f8-991e-b3dee723a52d"

    @property
    def name(self) -> str:
        return "moenv_uv"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict:
        """從環境部 API 取得即時紫外線監測資料。

        Args:
            limit: 回傳筆數上限（預設 100）。
            api_key: API 金鑰（預設使用公開金鑰）。

        Returns:
            原始 API 回應 dict。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        api_key = params.get(
            "api_key",
            getattr(self._settings, "moenv_api_key", None) or self.DEFAULT_API_KEY,
        )
        limit = params.get("limit", 100)

        query: dict[str, Any] = {
            "api_key": api_key,
            "limit": limit,
            "offset": 0,
            "format": "json",
        }

        try:
            session = create_tw_gov_session()
            response = session.get(self.BASE_URL, params=query, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            raise ConnectorError(
                f"{self.name}: API 請求失敗 - {exc}"
            ) from exc

        data = response.json()
        if "records" not in data:
            raise ConnectorError(
                f"{self.name}: 回應格式異常 - 缺少 'records' 欄位"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """將原始資料轉換為標準化 DataFrame。

        Args:
            raw_data: fetch() 回傳的原始資料。

        Returns:
            包含以下欄位的 DataFrame：
            timestamp, station_name, county, uv_index,
            latitude, longitude, source_agency
        """
        records = raw_data.get("records", [])
        if not records:
            raise ConnectorError(f"{self.name}: 回應中無監測資料")

        rows = [
            {
                "timestamp": record.get("datacreationdate", ""),
                "station_name": record.get("sitename", ""),
                "county": record.get("county", ""),
                "uv_index": _safe_float(record.get("uvi")),
                "latitude": _parse_coordinate(record.get("wgs84_lat")),
                "longitude": _parse_coordinate(record.get("wgs84_lon")),
                "source_agency": record.get("unit", ""),
            }
            for record in records
        ]

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用最小請求量。"""
        return {"limit": 1}
