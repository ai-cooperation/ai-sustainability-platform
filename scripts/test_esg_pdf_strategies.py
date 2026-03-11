#!/usr/bin/env python3
"""測試 ESG 永續報告書下載器的策略。

小規模測試：10 家代表性公司，確認 esggenplus API 是否可用。
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


def test_strategy(strategy_name: str, connector, year: int) -> dict:
    """測試單一策略，回傳結果摘要。"""
    print(f"\n{'='*60}")
    print(f"策略: {strategy_name.upper()} | 年度: {year}")
    print(f"{'='*60}")

    try:
        start = time.time()
        result = connector.fetch(year=year, strategy=strategy_name)
        elapsed = time.time() - start

        records = result if isinstance(result, list) else result.get("reports", [])
        with_url = [r for r in records if r.get("report_url")]
        with_download_id = [
            r for r in records
            if r.get("download_id") and r["download_id"] != "00000000-0000-0000-0000-000000000000"
        ]

        print(f"  耗時: {elapsed:.1f}s")
        print(f"  總筆數: {len(records)}")
        print(f"  有外部連結: {len(with_url)}")
        print(f"  有 TWSE FileStream: {len(with_download_id)}")

        # 顯示前 10 筆
        for r in records[:10]:
            sid = r.get("stock_id", "?")
            name = r.get("company_name", "?")
            url = r.get("report_url", "")
            did = r.get("download_id", "")
            url_display = url[:55] + "..." if len(url) > 55 else url
            has_url = "URL" if url else "--"
            has_fs = "FS" if (did and did != "00000000-0000-0000-0000-000000000000") else "--"
            print(f"    [{sid}] {name[:8]:8s}: {has_url} {has_fs} {url_display}")

        return {
            "strategy": strategy_name,
            "year": year,
            "status": "OK",
            "total": len(records),
            "with_url": len(with_url),
            "with_filestream": len(with_download_id),
            "elapsed": elapsed,
        }

    except Exception as exc:
        print(f"  FAILED: {exc}")
        return {
            "strategy": strategy_name,
            "year": year,
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
        did = matched[0].get("download_id", "") if matched else ""

        status = "OK" if has_url else ("found" if matched else "miss")
        fs_tag = " +FS" if (did and did != "00000000-0000-0000-0000-000000000000") else ""
        print(f"  [{stock_id}] {name}: {status} via {source}{fs_tag} ({elapsed:.1f}s)")
        if url:
            print(f"         URL: {url[:80]}")

        return {
            "stock_id": stock_id,
            "name": name,
            "status": status,
            "source": source,
            "has_url": has_url,
            "has_filestream": bool(did and did != "00000000-0000-0000-0000-000000000000"),
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
    print("=" * 60)

    with patch("src.connectors.base.get_settings") as mock_s:
        mock_s.return_value = MagicMock()
        from src.connectors.corporate.esg_report_downloader import (
            EsgReportDownloaderConnector,
        )

        connector = EsgReportDownloaderConnector(
            output_dir="data/raw/esg_reports_test"
        )

    # --- Phase 1: 測試 esggenplus 各年度 ---
    print("\n" + "#" * 60)
    print("Phase 1: esggenplus API 各年度測試")
    print("#" * 60)

    strategy_results = []
    for year in [2024, 2023, 2022]:
        result = test_strategy("esggenplus", connector, year)
        strategy_results.append(result)
        time.sleep(0.5)

    # MOPS 備援測試
    result = test_strategy("mops", connector, 2022)
    strategy_results.append(result)

    # --- Phase 2: 逐家公司 auto 模式（2024 年度）---
    print("\n" + "#" * 60)
    print("Phase 2: 逐家公司測試 (auto 策略, 2024 年度)")
    print("#" * 60)

    company_results = []
    for stock_id, name in TEST_COMPANIES:
        result = test_single_company(connector, stock_id, name, 2024)
        company_results.append(result)
        time.sleep(0.3)

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
            connector, first_ok["stock_id"], first_ok["name"], 2024
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
            fs = f", {r.get('with_filestream', 0)} 有FileStream" if r.get("with_filestream") else ""
            print(f"  {r['strategy']:12s} {r['year']}: OK — {r['total']} 筆, {r['with_url']} 有URL{fs} ({r['elapsed']:.1f}s)")
        else:
            print(f"  {r['strategy']:12s} {r['year']}: FAILED — {r.get('error', '?')}")

    print(f"\n逐家公司 ({len(company_results)} 家, 2024):")
    ok = sum(1 for r in company_results if r.get("has_url"))
    fs = sum(1 for r in company_results if r.get("has_filestream"))
    found = sum(1 for r in company_results if r.get("status") == "found")
    fail = sum(1 for r in company_results if r.get("status") == "FAILED")
    print(f"  有下載連結: {ok}")
    print(f"  有 FileStream: {fs}")
    print(f"  找到但無URL: {found}")
    print(f"  失敗: {fail}")

    if download_result:
        print(f"\nPDF 下載: {download_result['status']}")
        if download_result.get("size"):
            print(f"  大小: {download_result['size']:,} bytes")


if __name__ == "__main__":
    main()
