"""Tests for EsgReportDownloaderConnector（台灣上市櫃永續報告書下載連接器）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.esg_report_downloader import (
    ESGGENPLUS_FILE_STREAM,
    ESGGENPLUS_REPORT_DATA,
    ESGGENPLUS_REPORT_DATA_OLD,
    MOPS_REPORT_URL,
    EsgReportDownloaderConnector,
    _roc_year,
    _western_year,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
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
def sample_esggenplus_new_response():
    """2023+ API 回傳格式。"""
    return [
        {
            "code": "2330",
            "name": "台灣積體電路製造股份有限公司",
            "shortName": "台積電",
            "twDocLink": "https://esg.tsmc.com/2024-report.pdf",
            "twFirstReportDownloadId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "enDocLink": "https://esg.tsmc.com/2024-report-en.pdf",
            "enFirstReportDownloadId": "00000000-0000-0000-0000-000000000000",
        },
        {
            "code": "2317",
            "name": "鴻海精密工業股份有限公司",
            "shortName": "鴻海",
            "twDocLink": "https://esg.foxconn.com/report.pdf",
            "twFirstReportDownloadId": "00000000-0000-0000-0000-000000000000",
            "enDocLink": "",
            "enFirstReportDownloadId": "00000000-0000-0000-0000-000000000000",
        },
    ]


@pytest.fixture
def sample_esggenplus_old_response():
    """2022 以前 API 回傳格式。"""
    return [
        {
            "companY_ID": "2330",
            "companY_NAME": "台灣積體電路製造股份有限公司",
            "weB_INFO": "https://esg.tsmc.com/old-report.pdf",
            "filE_NAME": "",
        },
        {
            "companY_ID": "2317",
            "companY_NAME": "鴻海精密工業股份有限公司",
            "weB_INFO": "",
            "filE_NAME": "2317_report.pdf",
        },
    ]


@pytest.fixture
def sample_mops_html():
    return """
    <html><body>
    <table>
    <tr>
        <td>2330</td>
        <td>台積電</td>
        <td>111</td>
        <td><a href="/server-java/FileDownLoad?step=9&amp;filePath=/home/html/nas/protect/t100/&amp;fileName=t100sa11_2330_111.pdf">中文版</a></td>
    </tr>
    <tr>
        <td>2317</td>
        <td>鴻海精密</td>
        <td>111</td>
        <td><a href='https://esg.foxconn.com/download/2022_report.pdf'>中文版</a></td>
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
        <td>111</td>
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
            "year": 2024,
            "report_url": "https://example.com/2330_2024.pdf",
            "pdf_path": "",
            "report_type": "sustainability",
            "source": "esggenplus",
        },
        {
            "stock_id": "2317",
            "company_name": "鴻海精密",
            "year": 2024,
            "report_url": "https://example.com/2317_2024.pdf",
            "pdf_path": "",
            "report_type": "sustainability",
            "source": "esggenplus",
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
        assert params["strategy"] == "esggenplus"


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
    def test_fetch_new_api(self, connector_esggenplus, sample_esggenplus_new_response):
        """2023+ 使用 /data 端點。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_esggenplus_new_response
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            result = connector_esggenplus.fetch(year=2024)

        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[0]["source"] == "esggenplus"
        assert result[0]["report_url"] == "https://esg.tsmc.com/2024-report.pdf"
        assert result[0]["download_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        # 確認呼叫 /data（非 /data/old）
        mock_post.assert_called_once()
        assert ESGGENPLUS_REPORT_DATA in mock_post.call_args[0][0]
        assert "old" not in mock_post.call_args[0][0]

    def test_fetch_old_api(self, connector_esggenplus, sample_esggenplus_old_response):
        """2022 以前使用 /data/old 端點。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_esggenplus_old_response
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            result = connector_esggenplus.fetch(year=2022)

        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[0]["report_url"] == "https://esg.tsmc.com/old-report.pdf"
        assert result[1]["stock_id"] == "2317"
        assert result[1]["report_url"] == "2317_report.pdf"

        # 確認呼叫 /data/old
        assert ESGGENPLUS_REPORT_DATA_OLD in mock_post.call_args[0][0]

    def test_fetch_list_format(self, connector_esggenplus):
        """API 直接回傳 list 的情況（2023+）。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"code": "2330", "name": "台積電", "twDocLink": "https://x.pdf",
             "twFirstReportDownloadId": "00000000-0000-0000-0000-000000000000"}
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ):
            result = connector_esggenplus.fetch(year=2024)

        assert len(result) == 1

    def test_fetch_http_error(self, connector_esggenplus):
        with patch.object(
            connector_esggenplus._session,
            "post",
            side_effect=requests.RequestException("Connection refused"),
        ):
            with pytest.raises(ConnectorError, match="ESG GenPlus API 請求失敗"):
                connector_esggenplus.fetch(year=2024)

    def test_fetch_sends_correct_payload(self, connector_esggenplus):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_esggenplus.fetch(year=2024, stock_id="2330")

        mock_post.assert_called_once_with(
            ESGGENPLUS_REPORT_DATA,
            json={
                "year": 2024,
                "marketType": 0,
                "industryNameList": [],
                "companyCodeList": ["2330"],
            },
            timeout=30,
        )

    def test_fetch_all_companies(self, connector_esggenplus):
        """不指定 stock_id 時 companyCodeList 應為空。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_esggenplus.fetch(year=2024)

        payload = mock_post.call_args[1]["json"]
        assert payload["companyCodeList"] == []

    def test_fetch_otc_market(self, connector_esggenplus):
        """上櫃 market_type=1。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_esggenplus._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_esggenplus.fetch(year=2024, market_type=1)

        payload = mock_post.call_args[1]["json"]
        assert payload["marketType"] == 1


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
            result = connector_mops.fetch(year=2022)

        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[0]["company_name"] == "台積電"
        assert result[0]["source"] == "mops"
        assert "FileDownLoad" in result[0]["report_url"]
        assert result[1]["stock_id"] == "2317"
        assert result[1]["report_url"] == "https://esg.foxconn.com/download/2022_report.pdf"

        # 確認送出正確的 form data
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["data"]["year"] == "111"  # 民國年
        assert call_kwargs[1]["data"]["TYPEK"] == "sii"

    def test_fetch_with_stock_id(self, connector_mops):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><table></table></body></html>"
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector_mops._session, "post", return_value=mock_resp
        ) as mock_post:
            connector_mops.fetch(year=2022, stock_id="2330")

        form_data = mock_post.call_args[1]["data"]
        assert form_data["co_id"] == "2330"

    def test_fetch_http_error(self, connector_mops):
        with patch.object(
            connector_mops._session,
            "post",
            side_effect=requests.RequestException("Timeout"),
        ):
            with pytest.raises(ConnectorError, match="MOPS 請求失敗"):
                connector_mops.fetch(year=2022)

    def test_fetch_year_too_new_raises(self, connector_mops):
        """ROC 112+ (2023+) 應拋出錯誤。"""
        with pytest.raises(ConnectorError, match="esggenplus"):
            connector_mops.fetch(year=2023)

    def test_parse_html_no_pdf_links(self, connector_mops, sample_mops_html_no_links):
        reports = connector_mops._parse_mops_html(
            sample_mops_html_no_links, year=2022
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
    def test_auto_prefers_esggenplus(self, connector, sample_esggenplus_new_response):
        """auto 策略優先用 esggenplus。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_esggenplus_new_response
        mock_resp.raise_for_status = MagicMock()

        with patch.object(
            connector._session, "post", return_value=mock_resp
        ):
            result = connector.fetch(year=2024)

        assert len(result) == 2
        assert result[0]["source"] == "esggenplus"

    def test_auto_falls_back_to_mops(self, connector, sample_mops_html):
        """esggenplus 失敗時回退 MOPS（2022 以前）。"""
        mock_mops_resp = MagicMock()
        mock_mops_resp.text = sample_mops_html
        mock_mops_resp.raise_for_status = MagicMock()

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 第一次 esggenplus 失敗
                raise requests.ConnectionError("esggenplus down")
            # 第二次 MOPS 成功
            return mock_mops_resp

        with patch.object(connector._session, "post", side_effect=side_effect):
            result = connector.fetch(year=2022)

        assert len(result) == 2
        assert result[0]["source"] == "mops"

    def test_auto_no_mops_fallback_for_new_years(self, connector):
        """2023+ 沒有 MOPS 備援。"""
        with patch.object(
            connector._session,
            "post",
            side_effect=requests.ConnectionError("All down"),
        ):
            with pytest.raises(ConnectorError, match="所有策略均失敗"):
                connector.fetch(year=2024)

    def test_auto_all_fail_old_year(self, connector):
        with patch.object(
            connector._session,
            "post",
            side_effect=requests.ConnectionError("All down"),
        ):
            with pytest.raises(ConnectorError, match="所有策略均失敗"):
                connector.fetch(year=2022)


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
        assert df["year"].iloc[0] == 2024

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
    _ESGGENPLUS_RESPONSE = [
        {
            "code": "2330",
            "name": "台積電",
            "twDocLink": "https://esg.tsmc.com/report.pdf",
            "twFirstReportDownloadId": "a1b2c3d4-0000-0000-0000-000000000001",
        },
    ]

    def test_download_via_filestream(self, connector, tmp_path):
        """有 download_id 時優先用 FileStream。"""
        connector.output_dir = tmp_path
        pdf_content = b"%PDF-1.4 " + b"x" * 2000

        mock_list_resp = MagicMock()
        mock_list_resp.json.return_value = self._ESGGENPLUS_RESPONSE
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
        mock_pdf_resp.raise_for_status = MagicMock()
        mock_pdf_resp.iter_content = MagicMock(return_value=iter([pdf_content]))

        with patch.object(connector._session, "post", return_value=mock_list_resp):
            with patch.object(connector._session, "get", return_value=mock_pdf_resp) as mock_get:
                path = connector.download_report("2330", 2024)

        assert path is not None
        assert path.name == "2330_2024.pdf"
        # 確認使用 FileStream URL
        get_url = mock_get.call_args[0][0]
        assert ESGGENPLUS_FILE_STREAM in get_url
        assert "a1b2c3d4" in get_url

    def test_download_via_external_url(self, connector, tmp_path):
        """download_id 為空 UUID 時用外部連結。"""
        connector.output_dir = tmp_path
        pdf_content = b"%PDF-1.4 " + b"x" * 2000

        response_no_download_id = [
            {
                "code": "2317",
                "name": "鴻海",
                "twDocLink": "https://esg.foxconn.com/report.pdf",
                "twFirstReportDownloadId": "00000000-0000-0000-0000-000000000000",
            },
        ]

        mock_list_resp = MagicMock()
        mock_list_resp.json.return_value = response_no_download_id
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
        mock_pdf_resp.raise_for_status = MagicMock()
        mock_pdf_resp.iter_content = MagicMock(return_value=iter([pdf_content]))

        with patch.object(connector._session, "post", return_value=mock_list_resp):
            with patch.object(connector._session, "get", return_value=mock_pdf_resp) as mock_get:
                path = connector.download_report("2317", 2024)

        assert path is not None
        get_url = mock_get.call_args[0][0]
        assert get_url == "https://esg.foxconn.com/report.pdf"

    def test_download_no_report_found(self, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch.object(connector._session, "post", return_value=mock_resp):
            result = connector.download_report("9999", 2024)

        assert result is None

    def test_download_empty_url(self, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "code": "2330",
                "name": "台積電",
                "twDocLink": "",
                "twFirstReportDownloadId": "00000000-0000-0000-0000-000000000000",
            },
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch.object(connector._session, "post", return_value=mock_resp):
            result = connector.download_report("2330", 2024)

        assert result is None

    def test_download_too_small_raises(self, connector, tmp_path):
        connector.output_dir = tmp_path

        mock_list_resp = MagicMock()
        mock_list_resp.json.return_value = self._ESGGENPLUS_RESPONSE
        mock_list_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock()
        mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
        mock_pdf_resp.raise_for_status = MagicMock()
        mock_pdf_resp.iter_content = MagicMock(return_value=iter([b"tiny"]))

        with patch.object(connector._session, "post", return_value=mock_list_resp):
            with patch.object(connector._session, "get", return_value=mock_pdf_resp):
                with pytest.raises(ConnectorError, match="檔案過小"):
                    connector.download_report("2330", 2024)

    def test_download_network_error(self, connector, tmp_path):
        connector.output_dir = tmp_path

        mock_list_resp = MagicMock()
        mock_list_resp.json.return_value = self._ESGGENPLUS_RESPONSE
        mock_list_resp.raise_for_status = MagicMock()

        with patch.object(connector._session, "post", return_value=mock_list_resp):
            with patch.object(
                connector._session,
                "get",
                side_effect=requests.ConnectionError("Download failed"),
            ):
                with pytest.raises(ConnectorError, match="PDF 下載失敗"):
                    connector.download_report("2330", 2024)


# =====================================================================
# list_available_reports
# =====================================================================


class TestListAvailableReports:
    def test_returns_list(self, connector, sample_esggenplus_new_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_esggenplus_new_response
        mock_resp.raise_for_status = MagicMock()

        with patch.object(connector._session, "post", return_value=mock_resp):
            reports = connector.list_available_reports(year=2024)

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
            c.fetch(year=2024)
