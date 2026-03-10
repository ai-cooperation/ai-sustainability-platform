"""台灣水利署水庫即時水情資料連接器。

資料來源：經濟部水利署開放資料
API: https://data.wra.gov.tw/Service/OpenData.aspx
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class TwWraReservoirConnector(BaseConnector):
    """台灣水庫即時水情連接器。

    提供全台主要水庫的即時水位、蓄水量百分比、進水量、出水量等資訊。
    此 API 為台灣政府公開資料，無需認證。
    """

    BASE_URL = (
        "https://data.wra.gov.tw/Service/OpenData.aspx"
    )
    DATASET_ID = "50C8256D-30C5-4B8D-9B84-2E14D5C6DF71"

    @property
    def name(self) -> str:
        return "tw_wra_reservoir"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict | list:
        """從水利署 API 取得水庫即時水情。

        Args:
            dataset_id: 資料集 ID（預設為水庫水情）。

        Returns:
            原始 API 回應（dict 或 list）。

        Raises:
            ConnectorError: API 呼叫失敗時。
        """
        dataset_id = params.get("dataset_id", self.DATASET_ID)

        query: dict[str, str] = {
            "format": "json",
            "id": dataset_id,
        }

        try:
            response = requests.get(self.BASE_URL, params=query, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API 請求失敗 - {exc}"
            ) from exc

        data = response.json()

        # 水利署 API 可能回傳 list 或包在 dict 中
        if isinstance(data, dict):
            # 嘗試常見的外層結構
            for key in ("data", "Data", "records", "Records"):
                if key in data:
                    return data
            # 如果沒有已知 key，直接回傳
            return data
        if isinstance(data, list):
            return {"records": data}

        raise ConnectorError(
            f"{self.name}: 回應格式異常 - 預期 dict 或 list"
        )

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """將原始資料轉換為標準化 DataFrame。

        Args:
            raw_data: fetch() 回傳的原始資料。

        Returns:
            包含以下欄位的 DataFrame：
            timestamp, reservoir_name, water_level, storage_percentage,
            inflow_cms, outflow_cms, country
        """
        # 從各種可能的結構中取出 records
        records = _extract_records(raw_data)
        if not records:
            raise ConnectorError(f"{self.name}: 回應中無水庫資料")

        rows = []
        now = datetime.now(tz=UTC)

        for record in records:
            update_time = (
                record.get("ObservationTime")
                or record.get("RecordTime")
                or record.get("updatetime")
                or now.isoformat()
            )
            rows.append({
                "timestamp": update_time,
                "reservoir_name": (
                    record.get("ReservoirName")
                    or record.get("reservoirname")
                    or record.get("StationName")
                    or ""
                ),
                "water_level": _safe_numeric(
                    record.get("WaterLevel")
                    or record.get("waterlevel")
                ),
                "storage_percentage": _safe_numeric(
                    record.get("PercentageOfStorage")
                    or record.get("percentageofstorage")
                    or record.get("StoragePercentage")
                ),
                "inflow_cms": _safe_numeric(
                    record.get("InflowDischarge")
                    or record.get("inflowdischarge")
                    or record.get("Inflow")
                ),
                "outflow_cms": _safe_numeric(
                    record.get("OutflowDischarge")
                    or record.get("outflowdischarge")
                    or record.get("Outflow")
                ),
                "country": "TW",
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        """健康檢查使用預設參數。"""
        return {}


def _extract_records(data: dict | list) -> list:
    """從各種回應格式中提取 records 列表。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in (
            "records", "Records", "data", "Data",
            "RainStationCollection", "WaterLevelStationOutput",
        ):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    return val
                # 可能還有一層
                if isinstance(val, dict):
                    for inner_key in ("records", "Records", "data"):
                        if inner_key in val and isinstance(val[inner_key], list):
                            return val[inner_key]
    return []


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，無效值回傳 None。"""
    if value is None or value == "" or value == "-" or value == "--":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
