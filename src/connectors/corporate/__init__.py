"""台灣上市櫃公司財務資料連接器。"""

from src.connectors.corporate.esg_report_downloader import EsgReportDownloaderConnector
from src.connectors.corporate.twse_company import TWSECompanyConnector
from src.connectors.corporate.twse_employee import TWSEEmployeeConnector
from src.connectors.corporate.twse_income import TWSEIncomeConnector
from src.connectors.corporate.twse_revenue import TWSERevenueConnector

__all__ = [
    "EsgReportDownloaderConnector",
    "TWSECompanyConnector",
    "TWSERevenueConnector",
    "TWSEIncomeConnector",
    "TWSEEmployeeConnector",
]
