"""台灣環境部空氣品質即時監測資料連接器。

資料來源：環境部環境資料開放平臺
API: https://data.moenv.gov.tw/api/v2/aqx_p_432
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class TwEpaAqiConnector(BaseConnector):
    """台灣 EPA 空氣品質指標 (AQI) 即時資料連接器。

    提供全台各監測站的即時空氣品質數據，包含 AQI、PM2.5、PM10、O3 等指標。
    此 API 為台灣政府公開資料，使用公開 API Key。
    """

    BASE_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    # 台灣環境部公開資料 API Key（公開金鑰，非機密）
    DEFAULT_API_KEY = "e8dd42e6-9b8b-43f8-991e-b3dee723a52d"

    @property
    def name(self) -> str:
        return "tw_epa_aqi"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict:
        """從環境部 API 取得即時空氣品質資料。

        Args:
            limit: 回傳筆數上限（預設 1000）。
            api_key: API 金鑰（預設使用公開金鑰）。

        Returns:
            原始 API 回應 dict。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        api_key = params.get("api_key", self.DEFAULT_API_KEY)
        limit = params.get("limit", 1000)

        query: dict[str, Any] = {
            "api_key": api_key,
            "limit": limit,
            "sort": "ImportDate desc",
            "format": "JSON",
        }

        try:
            response = requests.get(self.BASE_URL, params=query, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
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
            timestamp, station, county, aqi, pm25, pm10, o3, status
        """
        records = raw_data.get("records", [])
        if not records:
            raise ConnectorError(f"{self.name}: 回應中無監測資料")

        rows = []
        for record in records:
            rows.append({
                "timestamp": record.get("publishtime", ""),
                "station": record.get("sitename", ""),
                "county": record.get("county", ""),
                "aqi": _safe_numeric(record.get("aqi")),
                "pm25": _safe_numeric(record.get("pm2.5", record.get("pm25"))),
                "pm10": _safe_numeric(record.get("pm10")),
                "o3": _safe_numeric(record.get("o3")),
                "status": record.get("status", ""),
                "country": "TW",
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用最小請求量。"""
        return {"limit": 1}


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，無效值回傳 None。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
