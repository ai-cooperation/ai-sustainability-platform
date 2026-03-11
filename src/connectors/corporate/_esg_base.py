"""TWSE/TPEx ESG 結構化資料連接器基底類別。

證交所與櫃買中心依據「上市/櫃公司永續發展行動方案」公開之
ESG 結構化資料 (t187ap46 系列)。各主題端點於每年中旬更新，
非申報季期間回傳空陣列為正常現象。
"""

from __future__ import annotations

import csv
import io
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError
from src.connectors.corporate._ssl_helper import create_tw_gov_session

# 種子資料目錄（由 scripts/fetch_wayback_esg.py 下載）
_SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed" / "esg"


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

    @classmethod
    def load_seed_data(cls, topic_id: str) -> list[dict]:
        """從本地種子資料載入 ESG 資料（Wayback Machine 快照）。

        當 live API 回傳空陣列（非申報季）時，可用種子資料作為 fallback。
        支援 CSV (TWSE L_*) 與 JSON (TPEx O_*) 兩種格式。

        Args:
            topic_id: 主題編號，例如 '1', '2', '3', '4'。

        Returns:
            合併上市 + 上櫃的 JSON 陣列，若無種子資料則回傳空陣列。
        """
        combined: list[dict] = []

        # TWSE 上市 — CSV 格式
        csv_path = _SEED_DIR / f"t187ap46_L_{topic_id}.csv"
        if csv_path.exists():
            text = csv_path.read_text(encoding="utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                record = dict(row)
                record["_market"] = "TWSE"
                record["_source"] = "seed"
                combined.append(record)

        # TPEx 上櫃 — JSON 格式
        json_path = _SEED_DIR / f"t187ap46_O_{topic_id}.json"
        if json_path.exists():
            text = json_path.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, list):
                for record in data:
                    record["_market"] = "TPEx"
                    record["_source"] = "seed"
                    combined.append(record)

        return combined

    def fetch(self, **params: Any) -> list[dict]:
        """從 TWSE + TPEx 端點取得 ESG 資料。

        若 live API 回傳空陣列（非申報季），自動 fallback 至種子資料。

        Returns:
            合併後的 JSON 陣列（可能為空）。

        Raises:
            ConnectorError: 兩個端點皆失敗且無種子資料時。
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

        # 兩個端點都失敗 → 拋錯（但仍可透過 seed fallback 取得資料）
        if len(errors) == 2 and not combined:
            self.logger.warning(
                f"{self.name}: TWSE 與 TPEx 端點皆請求失敗，嘗試載入種子資料"
            )

        # 非申報季 fallback：live 資料為空時，改用種子資料
        if not combined:
            seed = self.load_seed_data(self.topic_id)
            if seed:
                self.logger.info(
                    f"{self.name}: 使用種子資料 ({len(seed)} 筆)"
                )
                return seed

        # 若連種子資料都沒有，且兩端點都失敗，才拋錯
        if len(errors) == 2 and not combined:
            raise ConnectorError(
                f"{self.name}: TWSE 與 TPEx 端點皆請求失敗且無種子資料 - {errors}"
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
