"""SSL 相容性輔助工具。

台灣政府網站（TWSE、TPEx、MOENV）的 SSL 憑證缺少 Subject Key Identifier，
在 Python 3.13 + OpenSSL 3.5 的嚴格模式下會驗證失敗。
此模組提供安全的 requests Session，放寬 X509 strict flag 但仍驗證憑證。
"""

from __future__ import annotations

import ssl

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


class TwGovSSLAdapter(HTTPAdapter):
    """自訂 SSL Adapter，放寬 X509 strict mode 以相容台灣政府憑證。

    仍然驗證憑證鏈、hostname，僅不啟用 OpenSSL 3.x 的 X509_V_FLAG_X509_STRICT。
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.verify_flags = ssl.VERIFY_DEFAULT
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def create_tw_gov_session() -> requests.Session:
    """建立可相容台灣政府網站 SSL 的 requests Session。"""
    session = requests.Session()
    adapter = TwGovSSLAdapter()
    session.mount("https://openapi.twse.com.tw", adapter)
    session.mount("https://www.tpex.org.tw", adapter)
    session.mount("https://mopsfin.twse.com.tw", adapter)
    session.mount("https://mopsov.twse.com.tw", adapter)
    session.mount("https://esggenplus.twse.com.tw", adapter)
    session.mount("https://l40s.chase.com.tw", adapter)
    session.mount("https://doc.twse.com.tw", adapter)
    session.mount("https://data.moenv.gov.tw", adapter)
    return session
