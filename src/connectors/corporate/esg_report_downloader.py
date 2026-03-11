"""台灣上市櫃公司永續報告書下載連接器。

資料來源（優先順序）：
1. TWSE ESG GenPlus API — esggenplus.twse.com.tw 的公開 API
2. MOPS 公開資訊觀測站 — mopsov.twse.com.tw 永續報告書查詢頁面（僅 2022 以前）

ESG GenPlus API 端點（無需認證）：
- POST /api/api/MopsSustainReport/data           — 2023+ 報告列表
- POST /api/api/MopsSustainReport/data/old       — 2022 以前報告列表
- GET  /api/api/MopsSustainReport/data/FileStream?id={UUID} — TWSE 託管 PDF 下載
- GET  /api/api/MopsSustainReport/industryAndCompanyCode    — 產業/公司代碼列表

MOPS 備援（ROC 111 / 2022 以前）：
- POST https://mopsov.twse.com.tw/mops/web/ajax_t100sb11
- 回傳 HTML 表格，內含 PDF 連結
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError

# --- 常數 ---

ESGGENPLUS_API_BASE = "https://esggenplus.twse.com.tw/api/api"
ESGGENPLUS_REPORT_DATA = f"{ESGGENPLUS_API_BASE}/MopsSustainReport/data"
ESGGENPLUS_REPORT_DATA_OLD = f"{ESGGENPLUS_API_BASE}/MopsSustainReport/data/old"
ESGGENPLUS_FILE_STREAM = f"{ESGGENPLUS_API_BASE}/MopsSustainReport/data/FileStream"

# esggenplus 可查詢的最早年度（2023 起用新版 API，2022 以前用 /data/old）
ESGGENPLUS_NEW_API_START_YEAR = 2023

MOPS_BASE = "https://mopsov.twse.com.tw"
MOPS_REPORT_URL = f"{MOPS_BASE}/mops/web/ajax_t100sb11"

DEFAULT_TIMEOUT = 30
DEFAULT_OUTPUT_DIR = "data/raw/esg_reports"

# MOPS 回傳 HTML 中 PDF 下載連結的 pattern
MOPS_PDF_LINK_PATTERN = re.compile(
    r'href=["\']([^"\']*(?:\.pdf|FileDownLoad[^"\']*\.pdf)[^"\']*)["\']',
    re.IGNORECASE,
)

# MOPS 在 ROC 112 年 (2023) 起改用 esggenplus，此前版本透過 MOPS 直接取得
MOPS_LAST_DIRECT_ROC_YEAR = 111  # 西元 2022

# esggenplus FileStream 的空 UUID（表示無 TWSE 託管副本）
_NULL_UUID = "00000000-0000-0000-0000-000000000000"


def _roc_year(western_year: int) -> int:
    """西元年轉民國年。"""
    return western_year - 1911


def _western_year(roc_year: int) -> int:
    """民國年轉西元年。"""
    return roc_year + 1911


class EsgReportDownloaderConnector(BaseConnector):
    """台灣上市櫃公司永續報告書下載連接器。

    支援策略：
    - esggenplus: 透過 ESG GenPlus 公開 API（涵蓋 2013-2024 所有年度）
    - mops: 透過 MOPS 公開資訊觀測站（僅 2022 以前）
    - auto: 優先 esggenplus，失敗回退 MOPS（2022 以前）

    使用方式：
        connector = EsgReportDownloaderConnector()
        # 列出某年度所有報告
        reports = connector.list_available_reports(year=2024)
        # 下載單一公司報告
        path = connector.download_report(stock_id="2330", year=2024)
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        output_dir: str | Path | None = None,
        strategy: str = "auto",
    ):
        super().__init__(config)
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self._strategy = strategy  # auto | esggenplus | mops
        from src.connectors.corporate._ssl_helper import create_tw_gov_session
        self._session = create_tw_gov_session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    @property
    def name(self) -> str:
        return "esg_report_downloader"

    @property
    def domain(self) -> str:
        return "corporate"

    # ------------------------------------------------------------------
    # BaseConnector 必要介面
    # ------------------------------------------------------------------

    def fetch(self, **params: Any) -> dict | list:
        """取得永續報告書列表。

        Args:
            stock_id: 股票代號（選填）。指定時只查該公司。
            year: 西元年度（選填，預設前一年）。
            market_type: 市場類型 0=上市 1=上櫃（選填，預設 0）。
            strategy: 覆蓋預設策略。

        Returns:
            報告資料列表。

        Raises:
            ConnectorError: 所有策略都失敗時。
        """
        stock_id = params.get("stock_id")
        year = params.get("year", datetime.now(tz=UTC).year - 1)
        strategy = params.get("strategy", self._strategy)
        market_type = params.get("market_type", 0)

        if strategy == "auto":
            return self._fetch_auto(
                stock_id=stock_id, year=year, market_type=market_type,
            )
        if strategy == "esggenplus":
            return self._fetch_esggenplus(
                stock_id=stock_id, year=year, market_type=market_type,
            )
        if strategy == "mops":
            return self._fetch_mops(stock_id=stock_id, year=year)

        raise ConnectorError(f"{self.name}: 不支援的策略 '{strategy}'")

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """將原始報告列表轉換為標準 DataFrame。

        輸出欄位：
            stock_id, company_name, year, report_url, pdf_path,
            report_type, source, timestamp
        """
        records = raw_data if isinstance(raw_data, list) else raw_data.get("reports", [])

        if not records:
            raise ConnectorError(f"{self.name}: 無永續報告資料")

        now = datetime.now(tz=UTC)
        rows = []
        for r in records:
            rows.append({
                "stock_id": str(r.get("stock_id", "")),
                "company_name": r.get("company_name", ""),
                "year": int(r.get("year", 0)),
                "report_url": r.get("report_url", ""),
                "pdf_path": r.get("pdf_path", ""),
                "report_type": r.get("report_type", "sustainability"),
                "source": r.get("source", "unknown"),
                "timestamp": now,
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def _health_check_params(self) -> dict:
        """健康檢查：使用 esggenplus API 查最新年度。"""
        return {"year": datetime.now(tz=UTC).year - 1, "strategy": "esggenplus"}

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def list_available_reports(
        self, *, year: int | None = None, stock_id: str | None = None
    ) -> list[dict]:
        """列出可下載的永續報告書。"""
        target_year = year or (datetime.now(tz=UTC).year - 1)
        raw = self.fetch(stock_id=stock_id, year=target_year)
        records = raw if isinstance(raw, list) else raw.get("reports", [])
        return records

    def download_report(
        self,
        stock_id: str,
        year: int,
        *,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Path | None:
        """下載單一公司的永續報告書 PDF。

        Returns:
            下載的 PDF 檔案路徑；若無法取得則回傳 None。
        """
        reports = self.list_available_reports(year=year, stock_id=stock_id)
        matched = [r for r in reports if str(r.get("stock_id")) == str(stock_id)]

        if not matched:
            self.logger.warning(f"找不到 {stock_id} 年度 {year} 的永續報告書")
            return None

        report = matched[0]

        # 優先用 TWSE 託管的 FileStream，其次用外部連結
        download_id = report.get("download_id", "")
        if download_id and download_id != _NULL_UUID:
            url = f"{ESGGENPLUS_FILE_STREAM}?id={download_id}"
        else:
            url = report.get("report_url", "")

        if not url:
            self.logger.warning(f"{stock_id} 缺少報告下載連結")
            return None

        return self._download_pdf(url, stock_id=stock_id, year=year, timeout=timeout)

    # ------------------------------------------------------------------
    # 策略實作：自動嘗試
    # ------------------------------------------------------------------

    def _fetch_auto(
        self, *, stock_id: str | None, year: int, market_type: int = 0,
    ) -> list:
        """依據年度自動選擇策略。優先 esggenplus，失敗回退 MOPS。"""
        roc = _roc_year(year)
        errors: list[str] = []

        strategies: list[tuple[str, Any]] = [
            ("esggenplus", lambda: self._fetch_esggenplus(
                stock_id=stock_id, year=year, market_type=market_type,
            )),
        ]
        # 2022 以前可加 MOPS 備援
        if roc <= MOPS_LAST_DIRECT_ROC_YEAR:
            strategies.append(
                ("mops", lambda: self._fetch_mops(stock_id=stock_id, year=year)),
            )

        for strategy_name, fetcher in strategies:
            try:
                result = fetcher()
                if result is not None:  # 空列表也是合法結果
                    self.logger.info(f"策略 '{strategy_name}' 成功取得資料")
                    return result
            except (ConnectorError, requests.RequestException) as exc:
                self.logger.warning(f"策略 '{strategy_name}' 失敗: {exc}")
                errors.append(f"{strategy_name}: {exc}")

        raise ConnectorError(
            f"{self.name}: 所有策略均失敗（year={year}）— " + "; ".join(errors)
        )

    # ------------------------------------------------------------------
    # 策略 A: ESG GenPlus API（涵蓋所有年度）
    # ------------------------------------------------------------------

    def _fetch_esggenplus(
        self, *, stock_id: str | None, year: int, market_type: int = 0,
    ) -> list:
        """透過 ESG GenPlus 公開 API 取得報告列表。

        2023+ 使用 /data 端點，2022 以前使用 /data/old 端點。
        """
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        is_new = year >= ESGGENPLUS_NEW_API_START_YEAR

        url = ESGGENPLUS_REPORT_DATA if is_new else ESGGENPLUS_REPORT_DATA_OLD
        payload: dict[str, Any] = {
            "year": year,
            "marketType": market_type,
            "industryNameList": [],
            "companyCodeList": [stock_id] if stock_id else [],
        }

        try:
            resp = self._session.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: ESG GenPlus API 請求失敗 - {exc}"
            ) from exc

        items = data if isinstance(data, list) else data.get("data", data)
        if not isinstance(items, list):
            items = []

        if is_new:
            return self._parse_esggenplus_new(items, year=year)
        return self._parse_esggenplus_old(items, year=year)

    def _parse_esggenplus_new(self, items: list[dict], *, year: int) -> list[dict]:
        """解析 2023+ API 回傳欄位。

        欄位：code, name, shortName, twDocLink, twFirstReportDownloadId,
              enDocLink, enFirstReportDownloadId, ...
        """
        reports: list[dict] = []
        for item in items:
            tw_url = item.get("twDocLink", "") or ""
            download_id = item.get("twFirstReportDownloadId", "") or ""

            reports.append({
                "stock_id": item.get("code", ""),
                "company_name": item.get("name", item.get("shortName", "")),
                "year": year,
                "report_url": tw_url,
                "download_id": download_id,
                "pdf_path": "",
                "report_type": "sustainability",
                "source": "esggenplus",
            })
        return reports

    def _parse_esggenplus_old(self, items: list[dict], *, year: int) -> list[dict]:
        """解析 2022 以前 API 回傳欄位（legacy 大小寫混合欄名）。

        欄位：companY_ID, companY_NAME, weB_INFO, filE_NAME, ...
        """
        reports: list[dict] = []
        for item in items:
            sid = item.get("companY_ID", item.get("code", ""))
            cname = item.get("companY_NAME", item.get("name", ""))
            web_info = item.get("weB_INFO", "") or ""
            file_name = item.get("filE_NAME", "") or ""
            download_id = item.get("twFirstReportDownloadId", "") or ""

            # 優先用 web_info（公司外部 URL），或 file_name
            report_url = web_info or file_name

            reports.append({
                "stock_id": str(sid).strip(),
                "company_name": str(cname).strip(),
                "year": year,
                "report_url": report_url,
                "download_id": download_id,
                "pdf_path": "",
                "report_type": "sustainability",
                "source": "esggenplus",
            })
        return reports

    # ------------------------------------------------------------------
    # 策略 B: MOPS 公開資訊觀測站（僅 2022 以前）
    # ------------------------------------------------------------------

    def _fetch_mops(self, *, stock_id: str | None, year: int) -> list:
        """透過 MOPS 查詢永續報告書。

        注意：ROC 112+ (2023+) 會被重導向至 esggenplus，
        此策略僅適用於 ROC 111 (2022) 以前的年度。
        """
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        roc = _roc_year(year)

        if roc > MOPS_LAST_DIRECT_ROC_YEAR:
            raise ConnectorError(
                f"{self.name}: MOPS 自 ROC {MOPS_LAST_DIRECT_ROC_YEAR + 1} "
                f"({_western_year(MOPS_LAST_DIRECT_ROC_YEAR + 1)}) 起已轉移至 "
                f"esggenplus，請改用 esggenplus 策略"
            )

        form_data = {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": str(roc),
        }
        if stock_id:
            form_data["co_id"] = stock_id

        try:
            resp = self._session.post(
                MOPS_REPORT_URL,
                data=form_data,
                timeout=timeout,
            )
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: MOPS 請求失敗 - {exc}"
            ) from exc

        # 檢查是否被重導向至 esggenplus
        if "esggenplus" in html:
            raise ConnectorError(
                f"{self.name}: MOPS 已將此年度 ({year}) 轉移至 esggenplus"
            )

        return self._parse_mops_html(html, year=year)

    def _parse_mops_html(self, html: str, *, year: int) -> list:
        """解析 MOPS 回傳的 HTML，提取報告資訊與 PDF 連結。"""
        reports: list[dict] = []

        rows = re.split(r"<tr[^>]*>", html, flags=re.IGNORECASE)

        for row in rows:
            cells = re.findall(
                r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE
            )
            if len(cells) < 3:
                continue

            sid = re.sub(r"<[^>]+>", "", cells[0]).strip()
            cname = re.sub(r"<[^>]+>", "", cells[1]).strip()

            if not re.match(r"^\d{4,6}$", sid):
                continue

            # 蒐集所有 PDF 連結
            pdf_links = MOPS_PDF_LINK_PATTERN.findall(row)
            report_url = ""
            if pdf_links:
                # 優先選 MOPS 伺服器上的 PDF（穩定），其次外部連結
                mops_pdfs = [
                    u for u in pdf_links if "FileDownLoad" in u or "server-java" in u
                ]
                if mops_pdfs:
                    raw_url = mops_pdfs[0].replace("&amp;", "&")
                else:
                    raw_url = pdf_links[0].replace("&amp;", "&")
                report_url = (
                    raw_url
                    if raw_url.startswith("http")
                    else urljoin(MOPS_BASE + "/", raw_url)
                )

            reports.append({
                "stock_id": sid,
                "company_name": cname,
                "year": year,
                "report_url": report_url,
                "pdf_path": "",
                "report_type": "sustainability",
                "source": "mops",
            })

        return reports

    # ------------------------------------------------------------------
    # PDF 下載
    # ------------------------------------------------------------------

    def _download_pdf(
        self,
        url: str,
        *,
        stock_id: str,
        year: int,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Path:
        """下載 PDF 至本地檔案。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{stock_id}_{year}.pdf"
        filepath = self.output_dir / filename

        try:
            resp = self._session.get(url, timeout=timeout, stream=True)
            resp.raise_for_status()

            # FileStream 端點 Content-Type 可能回報 text/html 但實際內容是 PDF
            content_type = resp.headers.get("Content-Type", "")
            first_chunk = next(resp.iter_content(chunk_size=8192), b"")

            is_filestream = ESGGENPLUS_FILE_STREAM in url
            is_pdf_content = first_chunk[:5] == b"%PDF-"

            if (
                not is_filestream
                and not is_pdf_content
                and "html" in content_type.lower()
                and "pdf" not in content_type.lower()
            ):
                raise ConnectorError(
                    f"{self.name}: 下載回傳 HTML 而非 PDF（可能被擋）"
                )

            with open(filepath, "wb") as f:
                f.write(first_chunk)
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size = filepath.stat().st_size
            if size < 1024:
                filepath.unlink(missing_ok=True)
                raise ConnectorError(
                    f"{self.name}: 下載檔案過小 ({size} bytes)，可能不是有效 PDF"
                )

            self.logger.info(f"已下載: {filepath} ({size:,} bytes)")
            return filepath

        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: PDF 下載失敗 ({url}) - {exc}"
            ) from exc
