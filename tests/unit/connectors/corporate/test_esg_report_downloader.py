"""Tests for EsgReportDownloaderConnector（台灣上市櫃永續報告書下載連接器）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.esg_report_downloader import (
    ESGGENPLUS_REPORT_LIST,
    MOPS_REPORT_URL,
    EsgReportDownloaderConnector,
    _roc_year,
    _western_year,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        mock_settings.return_value = settings_instance
        yield EsgReportDownloaderConnector(output_dir="/tmp/test_esg_reports")


@pytest.fixture
def connector_mops():
    """使用 MOPS 策略的連接器。"""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        yield EsgReportDownloaderConnector(
            output_dir="/tmp/test_esg_reports", strategy="mops"
        )


@pytest.fixture
def connector_esggenplus():
    """使用 ESG GenPlus 策略的連接器。"""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        yield EsgReportDownloaderConnector(
            output_dir="/tmp/test_esg_reports", strategy="esggenplus"
        )


@pytest.fixture
def sample_esggenplus_response():
    return {
        "data": [
            {
                "companyCode": "2330",
                "companyName": "台積電",
                "fileUrl": "/files/reports/2330_2023.pdf",
                "reportType": "sustainability",
            },
            {
                "companyCode": "2317",
                "companyName": "鴻海精密",
                "fileUrl": "https://example.com/reports/2317_2023.pdf",
                "reportType": "sustainability",
            },
        ]
    }


@pytest.fixture
def sample_mops_html():
    return """
    <html><body>
    <table>
    <tr>
        <td>2330</td>
        <td>台積電</td>
        <td>112</td>
        <td><a href="/mops/web/ajax_t100sb11?step=2&amp;co_id=2330&amp;year=112&amp;filename=2330_112.pdf">下載</a></td>
    </tr>
    <tr>
        <td>2317</td>
        <td>鴻海精密</td>
        <td>112</td>
        <td><a href='/mops/web/ajax_t100sb11?step=2&amp;co_id=2317&amp;year=112&amp;filename=2317_112.pdf'>下載</a></td>
    </tr>
    <tr>
        <td>Header</td>
        <td>Not a company</td>
        <td>abc</td>
    </tr>
    </table>
    </body></html>
    """


@pytest.fixture
def sample_mops_html_no_links():
    return """
    <html><body>
    <table>
    <tr>
        <td>2330</td>
        <td>台積電</td>
        <td>112</td>
        <td>尚未上傳</td>
    </tr>
    </table>
    </body></html>
    """


@pytest.fixture
def sample_reports_list():
    return [
        {
            "stock_id": "2330",
            "company_name": "台積電",
            "year": 2023,
            "report_url": "https://example.com/2330_2023.pdf",
            "pdf_path": "",
            "report_type": "sustainability",
            "source": "mops",
        },
        {
            "stock_id": "2317",
            "company_name": "鴻海精密",
            "year": 2023,
            "report_url": "https://example.com/2317_2023.pdf",
            "pdf_path": "",
            "report_type": "sustainability",
            "source": "mops",
        },
    ]


# =====================================================================
# 基本屬性
# =====================================================================


class TestBasicProperties:
    def test_name(self, connector):
        assert connector.name == "esg_report_downloader"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_default_output_dir(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            c = EsgReportDownloaderConnector()
            assert c.output_dir == Path("data/raw/esg_reports")

    def test_custom_output_dir(self, connector):
        assert connector.output_dir == Path("/tmp/test_esg_reports")

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert "year" in params
        assert params["strategy"] == "mops"


# =====================================================================
# 年度轉換
# =====================================================================


class TestYearConversion:
    def test_roc_year(self):
        assert _roc_year(2023) == 112
        assert _roc_year(2024) == 113

    def test_western_year(self):
        assert _western_year(112) == 2023
        assert _western_year(113) == 2024

    def test_roundtrip(self):
        assert _western_year(_roc_year(2023)) == 2023


# =====================================================================
# ESG GenPlus 策略
# =====================================================================


class TestEsgGenPlusStrategy:
    def test_fetch_success(self, connector_esggenplus, sample_esggenplus_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_esggenplus_response
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            result = connector_esggenplus.fetch(year=2023)

        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[0]["source"] == "esggenplus"
        mock_post.assert_called_once()

        # 相對 URL 應加上 base
        assert result[0]["report_url"].startswith("https://")
        # 絕對 URL 維持原樣
        assert result[1]["report_url"] == "https://example.com/reports/2317_2023.pdf"

    def test_fetch_list_format(self, connector_esggenplus):
        """API 直接回傳 list 的情況。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"companyCode": "2330", "companyName": "台積電", "fileUrl": "/f.pdf"}
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ):
            result = connector_esggenplus.fetch(year=2023)

        assert len(result) == 1

    def test_fetch_http_error(self, connector_esggenplus):
        with patch.object(
            connector_esggenplus._session,
            "post",
            side_effect=requests.RequestException("Connection refused"),
        ):
            with pytest.raises(ConnectorError, match="ESG GenPlus API 請求失敗"):
                connector_esggenplus.fetch(year=2023)

    def test_fetch_sends_correct_payload(self, connector_esggenplus):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_esggenplus.fetch(year=2023, stock_id="2330")

        mock_post.assert_called_once_with(
            ESGGENPLUS_REPORT_LIST,
            json={"year": "2023", "companyCode": "2330"},
            timeout=30,
        )


# =====================================================================
# MOPS 策略
# =====================================================================


class TestMopsStrategy:
    def test_fetch_success(self, connector_mops, sample_mops_html):
        mock_resp = MagicMock()
        mock_resp.text = sample_mops_html
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_mops._session, "post", return_value=mock_resp
        ) as mock_post:
            result = connector_mops.fetch(year=2023)

        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[0]["company_name"] == "台積電"
        assert result[0]["source"] == "mops"
        assert "ajax_t100sb11" in result[0]["report_url"]
        assert result[1]["stock_id"] == "2317"

        # 確認送出正確的 form data
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["data"]["year"] == "112"  # 民國年
        assert call_kwargs[1]["data"]["TYPEK"] == "sii"

    def test_fetch_with_stock_id(self, connector_mops):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><table></table></body></html>"
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_mops._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_mops.fetch(year=2023, stock_id="2330")

        form_data = mock_post.call_args[1]["data"]
        assert form_data["co_id"] == "2330"

    def test_fetch_http_error(self, connector_mops):
        with patch.object(
            connector_mops._session,
            "post",
            side_effect=requests.RequestException("Timeout"),
        ):
            with pytest.raises(ConnectorError, match="MOPS 請求失敗"):
                connector_mops.fetch(year=2023)

    def test_parse_html_no_pdf_links(self, connector_mops, sample_mops_html_no_links):
        reports = connector_mops._parse_mops_html(
            sample_mops_html_no_links, year=2023
        )
        assert len(reports) == 1
        assert reports[0]["stock_id"] == "2330"
        assert reports[0]["report_url"] == ""

    def test_parse_html_skips_non_numeric_rows(self, connector_mops):
        html = """
        <table>
        <tr><td>公司代號</td><td>公司名稱</td><td>年度</td></tr>
        <tr><td>2330</td><td>台積電</td><td>112</td></tr>
        </table>
        """
        reports = connector_mops._parse_mops_html(html, year=2023)
        assert len(reports) == 1
        assert reports[0]["stock_id"] == "2330"

    def test_parse_empty_html(self, connector_mops):
        reports = connector_mops._parse_mops_html("<html></html>", year=2023)
        assert reports == []


# =====================================================================
# 自動策略
# =====================================================================


class TestAutoStrategy:
    def test_auto_falls_back_to_mops(self, connector, sample_mops_html):
        """ESG GenPlus 失敗時自動切換到 MOPS。"""
        mock_mops_resp = MagicMock()
        mock_mops_resp.text = sample_mops_html
        mock_mops_resp.raise_for_status = MagicMock()

        def side_effect(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("Connection refused")
            return mock_mops_resp

        with patch.object(connector._session, "post", side_effect=side_effect):
            result = connector.fetch(year=2023)

        assert len(result) == 2
        assert result[0]["source"] == "mops"

    def test_auto_all_fail(self, connector):
        with patch.object(
            connector._session,
            "post",
            side_effect=requests.ConnectionError("All down"),
        ):
            with pytest.raises(ConnectorError, match="所有策略均失敗"):
                connector.fetch(year=2023)


# =====================================================================
# Playwright 策略
# =====================================================================


class TestPlaywrightStrategy:
    def test_returns_params_dict(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            c = EsgReportDownloaderConnector(strategy="playwright")
            result = c.fetch(year=2023)

        assert result["strategy"] == "playwright"
        assert result["url"] == "https://esggenplus.twse.com.tw"
        assert isinstance(result["actions"], list)

    def test_includes_stock_id_action(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            c = EsgReportDownloaderConnector(strategy="playwright")
            result = c.fetch(year=2023, stock_id="2330")

        fill_actions = [a for a in result["actions"] if a.get("type") == "fill"]
        values = [a["value"] for a in fill_actions]
        assert "2330" in values


# =====================================================================
# normalize
# =====================================================================


class TestNormalize:
    def test_normalize_list(self, connector, sample_reports_list):
        df = connector.normalize(sample_reports_list)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "stock_id",
            "company_name",
            "year",
            "report_url",
            "pdf_path",
            "report_type",
            "source",
            "timestamp",
        ]
        assert df["stock_id"].iloc[0] == "2330"
        assert df["year"].iloc[0] == 2023

    def test_normalize_dict_format(self, connector, sample_reports_list):
        df = connector.normalize({"reports": sample_reports_list})
        assert len(df) == 2

    def test_normalize_empty_raises(self, connector):
        with pytest.raises(ConnectorError, match="無永續報告資料"):
            connector.normalize([])

    def test_normalize_empty_dict_raises(self, connector):
        with pytest.raises(ConnectorError, match="無永續報告資料"):
            connector.normalize({"reports": []})

    def test_normalize_timestamp_is_datetime(self, connector, sample_reports_list):
        df = connector.normalize(sample_reports_list)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_preserves_all_fields(self, connector):
        records = [
            {
                "stock_id": "1234",
                "company_name": "測試公司",
                "year": 2022,
                "report_url": "https://example.com/test.pdf",
                "pdf_path": "/local/test.pdf",
                "report_type": "annual",
                "source": "esggenplus",
            }
        ]
        df = connector.normalize(records)
        assert df["report_type"].iloc[0] == "annual"
        assert df["source"].iloc[0] == "esggenplus"
        assert df["pdf_path"].iloc[0] == "/local/test.pdf"


# =====================================================================
# download_report
# =====================================================================


class TestDownloadReport:
    def test_download_success(self, connector, tmp_path):
        connector.output_dir = tmp_path
        pdf_content = b"%PDF-1.4 " + b"x" * 2000  # 模擬 PDF

        mock_list_resp = MagicMock()
        mock_list_resp.text = """
        <table><tr>
            <td>2330</td><td>台積電</td><td>112</td>
            <td><a href="/mops/web/ajax_t100sb11?step=2&amp;co_id=2330">PDF</a></td>
        </tr></table>
        """
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
        mock_pdf_resp.raise_for_status = MagicMock()
        mock_pdf_resp.iter_content = MagicMock(return_value=[pdf_content])

        call_count = 0

        def side_effect_post(url, **kwargs):
            # MOPS list request
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_list_resp

        def side_effect_get(url, **kwargs):
            return mock_pdf_resp

        with patch.object(connector._session, "post", side_effect=side_effect_post):
            with patch.object(connector._session, "get", side_effect=side_effect_get):
                path = connector.download_report("2330", 2023)

        assert path is not None
        assert path.name == "2330_2023.pdf"
        assert path.exists()
        assert path.stat().st_size > 1024

    def test_download_no_report_found(self, connector):
        """找不到報告時回傳 None。"""
        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        mock_resp.raise_for_status = MagicMock()

        def side_effect_post(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_resp

        with patch.object(connector._session, "post", side_effect=side_effect_post):
            result = connector.download_report("9999", 2023)

        assert result is None

    def test_download_empty_url(self, connector):
        """報告存在但無下載連結。"""
        mock_resp = MagicMock()
        mock_resp.text = """
        <table><tr>
            <td>2330</td><td>台積電</td><td>112</td>
            <td>尚未上傳</td>
        </tr></table>
        """
        mock_resp.raise_for_status = MagicMock()

        def side_effect(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_resp

        with patch.object(connector._session, "post", side_effect=side_effect):
            result = connector.download_report("2330", 2023)

        assert result is None

    def test_download_html_response_raises(self, connector, tmp_path):
        """下載到 HTML 而非 PDF 時拋出錯誤。"""
        connector.output_dir = tmp_path

        mock_list_resp = MagicMock()
        mock_list_resp.text = """
        <table><tr>
            <td>2330</td><td>台積電</td><td>112</td>
            <td><a href="/mops/web/ajax_t100sb11?step=2&amp;co_id=2330">PDF</a></td>
        </tr></table>
        """
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_pdf_resp.raise_for_status = MagicMock()

        def side_effect_post(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_list_resp

        with patch.object(connector._session, "post", side_effect=side_effect_post):
            with patch.object(connector._session, "get", return_value=mock_pdf_resp):
                with pytest.raises(ConnectorError, match="HTML 而非 PDF"):
                    connector.download_report("2330", 2023)

    def test_download_too_small_raises(self, connector, tmp_path):
        """下載檔案過小時拋出錯誤。"""
        connector.output_dir = tmp_path

        mock_list_resp = MagicMock()
        mock_list_resp.text = """
        <table><tr>
            <td>2330</td><td>台積電</td><td>112</td>
            <td><a href="/mops/web/ajax_t100sb11?step=2&amp;co_id=2330">PDF</a></td>
        </tr></table>
        """
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
        mock_pdf_resp.raise_for_status = MagicMock()
        mock_pdf_resp.iter_content = MagicMock(return_value=[b"tiny"])

        def side_effect_post(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_list_resp

        with patch.object(connector._session, "post", side_effect=side_effect_post):
            with patch.object(connector._session, "get", return_value=mock_pdf_resp):
                with pytest.raises(ConnectorError, match="檔案過小"):
                    connector.download_report("2330", 2023)

    def test_download_network_error(self, connector, tmp_path):
        """PDF 下載時網路錯誤。"""
        connector.output_dir = tmp_path

        mock_list_resp = MagicMock()
        mock_list_resp.text = """
        <table><tr>
            <td>2330</td><td>台積電</td><td>112</td>
            <td><a href="/mops/web/ajax_t100sb11?step=2&amp;co_id=2330">PDF</a></td>
        </tr></table>
        """
        mock_list_resp.raise_for_status = MagicMock()

        def side_effect_post(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_list_resp

        with patch.object(connector._session, "post", side_effect=side_effect_post):
            with patch.object(
                connector._session,
                "get",
                side_effect=requests.ConnectionError("Download failed"),
            ):
                with pytest.raises(ConnectorError, match="PDF 下載失敗"):
                    connector.download_report("2330", 2023)


# =====================================================================
# list_available_reports
# =====================================================================


class TestListAvailableReports:
    def test_returns_list(self, connector, sample_mops_html):
        mock_resp = MagicMock()
        mock_resp.text = sample_mops_html
        mock_resp.raise_for_status = MagicMock()

        def side_effect(url, **kwargs):
            if "chase.com.tw" in url:
                raise requests.ConnectionError("down")
            return mock_resp

        with patch.object(connector._session, "post", side_effect=side_effect):
            reports = connector.list_available_reports(year=2023)

        assert isinstance(reports, list)
        assert len(reports) == 2
        assert all(isinstance(r, dict) for r in reports)


# =====================================================================
# 不支援的策略
# =====================================================================


class TestUnsupportedStrategy:
    def test_invalid_strategy_raises(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            c = EsgReportDownloaderConnector(strategy="nonexistent")

        with pytest.raises(ConnectorError, match="不支援的策略"):
            c.fetch(year=2023)
