"""台灣環境部溫室氣體排放統計連接器。

資料來源：環境部環境資料開放平臺
API: https://data.moenv.gov.tw/api/v2/GHP_P_01
此為年度統計資料（非即時），包含各部門溫室氣體排放量。

備註：台灣 EPA（現環境部）的溫室氣體排放資料主要為年度彙整，
並非即時 API。若此 API 無法使用，可退回為 Climate Watch
或 OWID Carbon 中的台灣資料。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class TwEpaGhgConnector(BaseConnector):
    """台灣溫室氣體排放統計連接器。

    提供台灣各部門（能源、工業、農業、廢棄物等）的年度溫室氣體排放量。
    資料來自環境部國家溫室氣體排放清冊。
    """

    # 環境部溫室氣體排放統計資料集
    BASE_URL = "https://data.moenv.gov.tw/api/v2/GHP_P_01"
    DEFAULT_API_KEY = "e8dd42e6-9b8b-43f8-991e-b3dee723a52d"

    # 備用：若主要 API 不可用，嘗試 CSV 下載
    FALLBACK_URL = (
        "https://data.moenv.gov.tw/api/v2/GHP_P_01"
    )

    @property
    def name(self) -> str:
        return "tw_epa_ghg"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict:
        """從環境部 API 取得溫室氣體排放統計資料。

        Args:
            api_key: API 金鑰（預設使用公開金鑰）。
            limit: 回傳筆數上限（預設 1000）。

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

        # 環境部 API 回傳格式可能包含 records 或直接是資料
        if isinstance(data, dict) and "records" not in data:
            # 某些資料集用不同 key
            for key in ("data", "Data", "result"):
                if key in data:
                    return {"records": data[key]} if isinstance(data[key], list) else data
            # 若有 total 但無 records，可能是空結果
            if data.get("total", 0) == 0:
                return {"records": []}
            # 回傳原始 dict，由 normalize 處理
            return data

        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """將原始資料轉換為標準化 DataFrame。

        Args:
            raw_data: fetch() 回傳的原始資料。

        Returns:
            包含以下欄位的 DataFrame：
            timestamp, sector, gas_type, emissions_kt, unit, country
        """
        records = raw_data.get("records", [])
        if not records:
            raise ConnectorError(f"{self.name}: 回應中無排放資料")

        rows = []
        for record in records:
            # 環境部資料欄位可能使用中文或英文 key
            year = (
                record.get("Year")
                or record.get("year")
                or record.get("統計年")
                or record.get("盤查年度")
                or ""
            )
            sector = (
                record.get("Sector")
                or record.get("sector")
                or record.get("部門")
                or record.get("排放源類別")
                or ""
            )
            gas_type = (
                record.get("GasType")
                or record.get("gas_type")
                or record.get("氣體別")
                or record.get("溫室氣體種類")
                or "CO2e"
            )
            emissions = _safe_numeric(
                record.get("Emissions")
                or record.get("emissions")
                or record.get("排放量")
                or record.get("排放量(公噸CO2e)")
                or record.get("value")
            )

            # 將年份轉為 timestamp（以年度 1/1 表示）
            timestamp = f"{year}-01-01" if year else ""

            rows.append({
                "timestamp": timestamp,
                "sector": sector,
                "gas_type": gas_type,
                "emissions_kt": emissions,
                "unit": "kt CO2e",
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
