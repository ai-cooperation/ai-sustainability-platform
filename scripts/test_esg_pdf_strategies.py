#!/usr/bin/env python3
"""測試 ESG 永續報告書下載器的三種策略。

小規模測試：10 家代表性公司，確認哪種策略可用。
用法: uv run python scripts/test_esg_pdf_strategies.py
"""

from __future__ import annotations

import io
import sys
import time

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, ".")

from unittest.mock import MagicMock, patch

# 10 家代表性公司（大型股 + 不同產業）
TEST_COMPANIES = [
    ("2330", "台積電"),
    ("2317", "鴻海"),
    ("2454", "聯發科"),
    ("2303", "聯電"),
    ("1301", "台塑"),
    ("2882", "國泰金"),
    ("2412", "中華電"),
    ("2308", "台達電"),
    ("3711", "日月光投控"),
    ("6505", "台塑化"),
]

TEST_YEAR = 2023  # 報告年度


def test_strategy(strategy_name: str, connector, year: int) -> dict:
    """測試單一策略，回傳結果摘要。"""
    print(f"\n{'='*60}")
    print(f"策略: {strategy_name.upper()}")
    print(f"{'='*60}")

    try:
        start = time.time()
        result = connector.fetch(year=year, strategy=strategy_name)
        elapsed = time.time() - start

        records = result if isinstance(result, list) else result.get("reports", [])
        with_url = [r for r in records if r.get("report_url")]

        print(f"  耗時: {elapsed:.1f}s")
        print(f"  總筆數: {len(records)}")
        print(f"  有下載連結: {len(with_url)}")

        # 顯示前 10 筆
        for r in records[:10]:
            sid = r.get("stock_id", "?")
            name = r.get("company_name", "?")
            url = r.get("report_url", "")
            url_display = url[:60] + "..." if len(url) > 60 else url
            has_url = "OK" if url else "--"
            print(f"    [{sid}] {name}: {has_url} {url_display}")

        return {
            "strategy": strategy_name,
            "status": "OK",
            "total": len(records),
            "with_url": len(with_url),
            "elapsed": elapsed,
        }

    except Exception as exc:
        print(f"  FAILED: {exc}")
        return {
            "strategy": strategy_name,
            "status": "FAILED",
            "error": str(exc),
        }


def test_single_company(connector, stock_id: str, name: str, year: int) -> dict:
    """以 auto 策略測試單一公司。"""
    try:
        start = time.time()
        result = connector.fetch(stock_id=stock_id, year=year, strategy="auto")
        elapsed = time.time() - start

        records = result if isinstance(result, list) else result.get("reports", [])
        matched = [r for r in records if str(r.get("stock_id")) == stock_id]

        has_url = bool(matched and matched[0].get("report_url"))
        source = matched[0].get("source", "?") if matched else "?"
        url = matched[0].get("report_url", "") if matched else ""

        status = "OK" if has_url else ("found" if matched else "miss")
        print(f"  [{stock_id}] {name}: {status} via {source} ({elapsed:.1f}s)")
        if url:
            print(f"         URL: {url[:80]}")

        return {
            "stock_id": stock_id,
            "name": name,
            "status": status,
            "source": source,
            "has_url": has_url,
            "elapsed": elapsed,
        }
    except Exception as exc:
        print(f"  [{stock_id}] {name}: FAILED - {exc}")
        return {"stock_id": stock_id, "name": name, "status": "FAILED", "error": str(exc)}


def test_download_one(connector, stock_id: str, name: str, year: int) -> dict:
    """實際下載一份 PDF 並驗證。"""
    print(f"\n--- 試下載 [{stock_id}] {name} 年度 {year} ---")
    try:
        start = time.time()
        path = connector.download_report(stock_id=stock_id, year=year)
        elapsed = time.time() - start

        if path and path.exists():
            size = path.stat().st_size
            print(f"  下載成功: {path} ({size:,} bytes, {elapsed:.1f}s)")
            return {"stock_id": stock_id, "status": "OK", "size": size, "path": str(path)}
        else:
            print(f"  無法取得 PDF ({elapsed:.1f}s)")
            return {"stock_id": stock_id, "status": "no_pdf"}

    except Exception as exc:
        print(f"  下載失敗: {exc}")
        return {"stock_id": stock_id, "status": "FAILED", "error": str(exc)}


def main():
    print("=" * 60)
    print("ESG 永續報告書下載策略測試")
    print(f"測試年度: {TEST_YEAR}")
    print(f"測試公司: {len(TEST_COMPANIES)} 家")
    print("=" * 60)

    with patch("src.connectors.base.get_settings") as mock_s:
        mock_s.return_value = MagicMock()
        from src.connectors.corporate.esg_report_downloader import (
            EsgReportDownloaderConnector,
        )

        connector = EsgReportDownloaderConnector(
            output_dir="data/raw/esg_reports_test"
        )

    # --- Phase 1: 測試各策略（全量列表） ---
    print("\n" + "#" * 60)
    print("Phase 1: 各策略全量列表測試")
    print("#" * 60)

    strategy_results = []
    for strat in ["esggenplus", "mops"]:
        result = test_strategy(strat, connector, TEST_YEAR)
        strategy_results.append(result)
        time.sleep(1)

    # --- Phase 2: 逐家公司 auto 模式 ---
    print("\n" + "#" * 60)
    print("Phase 2: 逐家公司測試 (auto 策略)")
    print("#" * 60)

    company_results = []
    for stock_id, name in TEST_COMPANIES:
        result = test_single_company(connector, stock_id, name, TEST_YEAR)
        company_results.append(result)
        time.sleep(0.5)

    # --- Phase 3: 試下載第一家有 URL 的 PDF ---
    print("\n" + "#" * 60)
    print("Phase 3: 實際 PDF 下載測試")
    print("#" * 60)

    first_ok = next(
        (r for r in company_results if r.get("has_url")),
        None,
    )
    download_result = None
    if first_ok:
        download_result = test_download_one(
            connector, first_ok["stock_id"], first_ok["name"], TEST_YEAR
        )
    else:
        print("  無可下載的報告，跳過下載測試")

    # --- 總結 ---
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)

    print("\n策略測試:")
    for r in strategy_results:
        if r["status"] == "OK":
            print(f"  {r['strategy']:15s}: OK — {r['total']} 筆, {r['with_url']} 有URL ({r['elapsed']:.1f}s)")
        else:
            print(f"  {r['strategy']:15s}: FAILED — {r.get('error', '?')}")

    print(f"\n逐家公司 ({len(company_results)} 家):")
    ok = sum(1 for r in company_results if r.get("has_url"))
    found = sum(1 for r in company_results if r.get("status") == "found")
    fail = sum(1 for r in company_results if r.get("status") == "FAILED")
    print(f"  有下載連結: {ok}")
    print(f"  找到但無URL: {found}")
    print(f"  失敗: {fail}")

    if download_result:
        print(f"\nPDF 下載: {download_result['status']}")
        if download_result.get("size"):
            print(f"  大小: {download_result['size']:,} bytes")


if __name__ == "__main__":
    main()
