"""TWSE/TPEx ESG 結構化資料連接器基底類別。

證交所與櫃買中心依據「上市/櫃公司永續發展行動方案」公開之
ESG 結構化資料 (t187ap46 系列)。各主題端點於每年中旬更新，
非申報季期間回傳空陣列為正常現象。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError
from src.connectors.corporate._ssl_helper import create_tw_gov_session


def _safe_numeric(value: Any) -> float | None:
    """安全地將字串轉為數值，無效值回傳 None。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        cleaned = str(value).replace(",", "").strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def _safe_pct(value: Any) -> float | None:
    """安全地將百分比字串轉為數值（移除 % 符號）。"""
    if value is None or value == "" or value == "-":
        return None
    try:
        cleaned = str(value).replace("%", "").replace(",", "").strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


class TWSEEsgBaseConnector(BaseConnector):
    """TWSE/TPEx ESG 結構化資料共用基底。

    子類別只需實作 topic_id、name、COLUMN_MAP 即可。
    fetch() 會同時抓取上市 (TWSE) 與上櫃 (TPEx) 端點並合併。
    """

    TWSE_TEMPLATE = "https://openapi.twse.com.tw/v1/opendata/t187ap46_L_{topic_id}"
    TPEX_TEMPLATE = "https://www.tpex.org.tw/openapi/v1/t187ap46_O_{topic_id}"

    @property
    @abstractmethod
    def topic_id(self) -> str:
        """主題編號，例如 '1', '2', '3'。"""

    @property
    def domain(self) -> str:
        return "corporate"

    @property
    @abstractmethod
    def column_map(self) -> dict[str, str]:
        """原始中文欄位名 → 標準化英文欄位名的對應。

        不含 stock_id / company_name / report_year，這三者由基底處理。
        """

    @property
    def expected_columns(self) -> list[str]:
        """標準化後的完整欄位清單。"""
        return [
            "stock_id",
            "company_name",
            "market",
            "report_year",
            *self.column_map.values(),
        ]

    def fetch(self, **params: Any) -> list[dict]:
        """從 TWSE + TPEx 端點取得 ESG 資料。

        Returns:
            合併後的 JSON 陣列（可能為空）。

        Raises:
            ConnectorError: 兩個端點皆失敗時。
        """
        twse_url = self.TWSE_TEMPLATE.format(topic_id=self.topic_id)
        tpex_url = self.TPEX_TEMPLATE.format(topic_id=self.topic_id)

        combined: list[dict] = []
        errors: list[str] = []
        session = create_tw_gov_session()

        for label, url in [("TWSE", twse_url), ("TPEx", tpex_url)]:
            try:
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    for record in data:
                        record["_market"] = label
                    combined.extend(data)
                else:
                    self.logger.warning(
                        f"{self.name}: {label} 回傳非陣列格式"
                    )
            except requests.RequestException as exc:
                errors.append(f"{label}: {exc}")
                self.logger.warning(f"{self.name}: {label} 請求失敗 - {exc}")

        if errors and not combined:
            # 兩個都失敗才拋錯；只要有一個成功（即使空陣列）就算正常
            if len(errors) == 2:
                raise ConnectorError(
                    f"{self.name}: TWSE 與 TPEx 端點皆請求失敗 - {errors}"
                )

        return combined

    def normalize(self, raw_data: list[dict]) -> pd.DataFrame:
        """將原始 JSON 陣列轉換為標準化 DataFrame。

        非申報季期間回傳空陣列為正常，會回傳具有正確欄位的空 DataFrame。
        """
        if not raw_data:
            return pd.DataFrame(columns=self.expected_columns)

        rows: list[dict] = []
        for record in raw_data:
            row: dict[str, Any] = {
                "stock_id": record.get("公司代號", ""),
                "company_name": record.get("公司名稱", ""),
                "market": record.get("_market", ""),
                "report_year": _parse_roc_year(
                    record.get("報告年度", "")
                ),
            }
            for zh_key, en_key in self.column_map.items():
                raw_val = record.get(zh_key, None)
                row[en_key] = self._convert_field(en_key, raw_val)
            rows.append(row)

        return pd.DataFrame(rows, columns=self.expected_columns)

    def _convert_field(self, en_key: str, raw_val: Any) -> Any:
        """依欄位名猜測型別並轉換。子類別可覆寫。"""
        if raw_val is None or raw_val == "":
            return None
        if en_key.endswith("_pct"):
            return _safe_pct(raw_val)
        if any(
            kw in en_key
            for kw in (
                "emissions",
                "consumption",
                "energy",
                "withdrawal",
                "waste",
                "recycled",
                "intensity",
                "total",
                "fuel",
                "electricity",
                "hazardous",
            )
        ):
            return _safe_numeric(raw_val)
        # 文字欄位保持原樣
        return str(raw_val).strip() if raw_val else None

    def _health_check_params(self) -> dict:
        """健康檢查不需額外參數。"""
        return {}


def _parse_roc_year(value: Any) -> int | None:
    """將民國年轉為西元年。例如 '113' → 2024。"""
    if value is None or value == "":
        return None
    try:
        roc = int(str(value).strip())
        return roc + 1911 if roc < 1000 else roc
    except (ValueError, TypeError):
        return None
