"""台灣上市櫃公司永續報告書下載連接器。

資料來源（優先順序）：
1. TWSE ESG GenPlus API — esggenplus.twse.com.tw 的內部 API
2. MOPS 公開資訊觀測站 — mopsov.twse.com.tw 永續報告書查詢頁面
3. Playwright 瀏覽器自動化（僅介面，需外部執行）

ESG GenPlus 為 React SPA，背後透過 l40s.chase.com.tw:4500/api 提供資料。
已知 API 路徑：
- /api/mopsEsg/allCompanyCode — 所有公司代碼
- /api/mopsEsg/singleCompanyData — 單一公司 ESG 資料
- /api/DeclareDataManage/sustain-report/list — 永續報告書列表

MOPS 備援：
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

ESGGENPLUS_API_BASE = "https://l40s.chase.com.tw:4500/api"
ESGGENPLUS_REPORT_LIST = f"{ESGGENPLUS_API_BASE}/DeclareDataManage/sustain-report/list"
ESGGENPLUS_COMPANY_LIST = f"{ESGGENPLUS_API_BASE}/mopsEsg/allCompanyCode"

MOPS_BASE = "https://mopsov.twse.com.tw"
MOPS_REPORT_URL = f"{MOPS_BASE}/mops/web/ajax_t100sb11"

DEFAULT_TIMEOUT = 30
DEFAULT_OUTPUT_DIR = "data/raw/esg_reports"

# MOPS 回傳 HTML 中 PDF 連結的 pattern
# 連結格式例：/mops/web/ajax_t100sb11?...(含 step=2 和 filename)
MOPS_PDF_LINK_PATTERN = re.compile(
    r'href=["\']([^"\']*ajax_t100sb11[^"\']*step=2[^"\']*)["\']',
    re.IGNORECASE,
)

# 從 HTML 行中提取公司代號 / 名稱 / 年度
MOPS_ROW_PATTERN = re.compile(
    r"<td[^>]*>\s*(\d{4})\s*</td>"  # 股票代號
    r"\s*<td[^>]*>\s*(.*?)\s*</td>"  # 公司名稱
    r"\s*<td[^>]*>\s*(\d{3,4})\s*</td>",  # 民國年度
    re.DOTALL,
)


def _roc_year(western_year: int) -> int:
    """西元年轉民國年。"""
    return western_year - 1911


def _western_year(roc_year: int) -> int:
    """民國年轉西元年。"""
    return roc_year + 1911


class EsgReportDownloaderConnector(BaseConnector):
    """台灣上市櫃公司永續報告書下載連接器。

    支援三種策略：
    - esggenplus: 透過 ESG GenPlus 內部 API 取得報告列表與下載連結
    - mops: 透過 MOPS 公開資訊觀測站查詢頁面
    - playwright: 瀏覽器自動化介面（僅提供參數，不直接執行）

    使用方式：
        connector = EsgReportDownloaderConnector()
        # 列出某年度所有報告
        reports = connector.list_available_reports(year=2023)
        # 下載單一公司報告
        path = connector.download_report(stock_id="2330", year=2023)
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
        self._strategy = strategy  # auto | esggenplus | mops | playwright
        self._session = requests.Session()
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
            strategy: 覆蓋預設策略。

        Returns:
            報告資料列表。

        Raises:
            ConnectorError: 所有策略都失敗時。
        """
        stock_id = params.get("stock_id")
        year = params.get("year", datetime.now(tz=UTC).year - 1)
        strategy = params.get("strategy", self._strategy)

        if strategy == "auto":
            return self._fetch_auto(stock_id=stock_id, year=year)
        if strategy == "esggenplus":
            return self._fetch_esggenplus(stock_id=stock_id, year=year)
        if strategy == "mops":
            return self._fetch_mops(stock_id=stock_id, year=year)
        if strategy == "playwright":
            return self._build_playwright_params(stock_id=stock_id, year=year)

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
        """健康檢查：嘗試取得最近一年的報告列表。"""
        return {"year": datetime.now(tz=UTC).year - 1, "strategy": "mops"}

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def list_available_reports(
        self, *, year: int | None = None, stock_id: str | None = None
    ) -> list[dict]:
        """列出可下載的永續報告書。

        Args:
            year: 西元年度（預設前一年）。
            stock_id: 篩選特定公司。

        Returns:
            報告資訊字典列表。
        """
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

        Args:
            stock_id: 股票代號。
            year: 報告年度（西元）。
            timeout: 下載超時秒數。

        Returns:
            下載的 PDF 檔案路徑；若無法取得則回傳 None。

        Raises:
            ConnectorError: 下載失敗時。
        """
        reports = self.list_available_reports(year=year, stock_id=stock_id)
        matched = [r for r in reports if str(r.get("stock_id")) == str(stock_id)]

        if not matched:
            self.logger.warning(f"找不到 {stock_id} 年度 {year} 的永續報告書")
            return None

        report = matched[0]
        url = report.get("report_url", "")
        if not url:
            self.logger.warning(f"{stock_id} 缺少報告下載連結")
            return None

        return self._download_pdf(url, stock_id=stock_id, year=year, timeout=timeout)

    # ------------------------------------------------------------------
    # 策略實作：自動嘗試
    # ------------------------------------------------------------------

    def _fetch_auto(self, *, stock_id: str | None, year: int) -> list:
        """依序嘗試各策略，回傳第一個成功的結果。"""
        errors = []

        for strategy_name, fetcher in [
            ("esggenplus", self._fetch_esggenplus),
            ("mops", self._fetch_mops),
        ]:
            try:
                result = fetcher(stock_id=stock_id, year=year)
                self.logger.info(f"策略 '{strategy_name}' 成功取得資料")
                return result
            except (ConnectorError, requests.RequestException) as exc:
                self.logger.warning(f"策略 '{strategy_name}' 失敗: {exc}")
                errors.append(f"{strategy_name}: {exc}")

        raise ConnectorError(
            f"{self.name}: 所有策略均失敗 — " + "; ".join(errors)
        )

    # ------------------------------------------------------------------
    # 策略 A: ESG GenPlus API
    # ------------------------------------------------------------------

    def _fetch_esggenplus(self, *, stock_id: str | None, year: int) -> list:
        """透過 ESG GenPlus 內部 API 取得報告列表。"""
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)

        try:
            resp = self._session.post(
                ESGGENPLUS_REPORT_LIST,
                json={"year": str(year), "companyCode": stock_id or ""},
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: ESG GenPlus API 請求失敗 - {exc}"
            ) from exc

        # API 回傳格式可能是 {"data": [...]} 或直接 [...]
        items = data if isinstance(data, list) else data.get("data", [])

        reports = []
        for item in items:
            report_url = item.get("fileUrl", item.get("downloadUrl", ""))
            if report_url and not report_url.startswith("http"):
                report_url = urljoin(ESGGENPLUS_API_BASE, report_url)

            reports.append({
                "stock_id": item.get("companyCode", item.get("co_id", "")),
                "company_name": item.get("companyName", item.get("co_name", "")),
                "year": year,
                "report_url": report_url,
                "pdf_path": "",
                "report_type": item.get("reportType", "sustainability"),
                "source": "esggenplus",
            })

        return reports

    # ------------------------------------------------------------------
    # 策略 B: MOPS 公開資訊觀測站
    # ------------------------------------------------------------------

    def _fetch_mops(self, *, stock_id: str | None, year: int) -> list:
        """透過 MOPS 查詢永續報告書。

        POST 至 ajax_t100sb11，解析回傳的 HTML 表格。
        """
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        roc = _roc_year(year)

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

        return self._parse_mops_html(html, year=year)

    def _parse_mops_html(self, html: str, *, year: int) -> list:
        """解析 MOPS 回傳的 HTML，提取報告資訊與 PDF 連結。"""
        reports: list[dict] = []

        # 嘗試逐行配對：每一列 <tr> 可能包含公司代號 + PDF 連結
        rows = re.split(r"<tr[^>]*>", html, flags=re.IGNORECASE)

        for row in rows:
            # 提取股票代號與公司名稱
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
            if len(cells) < 3:
                continue

            sid = re.sub(r"<[^>]+>", "", cells[0]).strip()
            cname = re.sub(r"<[^>]+>", "", cells[1]).strip()

            # 股票代號應為 4 位數字
            if not re.match(r"^\d{4,6}$", sid):
                continue

            # 找 PDF 連結
            pdf_links = MOPS_PDF_LINK_PATTERN.findall(row)
            report_url = ""
            if pdf_links:
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
    # 策略 C: Playwright 參數產生（不直接執行）
    # ------------------------------------------------------------------

    def _build_playwright_params(
        self, *, stock_id: str | None, year: int
    ) -> dict:
        """產生 Playwright 瀏覽器自動化所需的參數。

        不執行瀏覽器，僅回傳設定，可由外部 script 使用。
        """
        return {
            "strategy": "playwright",
            "url": "https://esggenplus.twse.com.tw",
            "actions": [
                {"type": "wait_for_selector", "selector": "#root"},
                {"type": "navigate", "path": "/report/list"},
                {
                    "type": "fill",
                    "selector": "input[name='year']",
                    "value": str(year),
                },
                *(
                    [
                        {
                            "type": "fill",
                            "selector": "input[name='companyCode']",
                            "value": stock_id,
                        }
                    ]
                    if stock_id
                    else []
                ),
                {"type": "click", "selector": "button[type='submit']"},
                {"type": "wait_for_selector", "selector": ".report-table"},
                {"type": "extract", "selector": ".report-table tr"},
            ],
            "reports": [],  # 由外部 script 填入
        }

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

            content_type = resp.headers.get("Content-Type", "")
            if "html" in content_type.lower() and "pdf" not in content_type.lower():
                raise ConnectorError(
                    f"{self.name}: 下載回傳 HTML 而非 PDF（可能被擋）"
                )

            with open(filepath, "wb") as f:
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
