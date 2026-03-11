#!/usr/bin/env python3
"""從 Wayback Machine 下載 TWSE/TPEx ESG 種子資料。

證交所 ESG 端點 (t187ap46 系列) 僅於每年 7-11 月有資料，
非申報季回傳空陣列。此腳本從 Wayback Machine 取得 2024/11 快照，
作為 Layer 2 connector 的 seed data。

用法: uv run python scripts/fetch_wayback_esg.py
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

# 確保 stdout 使用 UTF-8（RPi5 可能是 Big5 locale）
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

import requests

# ── 設定 ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = PROJECT_ROOT / "data" / "seed" / "esg"

# Wayback Machine 已知有快照的時間戳（2024 年 11 月）
TIMESTAMPS = ["20241126", "20241116", "20241101"]

# TWSE 上市公司 — CSV 格式（mopsfin.twse.com.tw）
TWSE_DATASETS = {
    "t187ap46_L_1": {
        "desc": "溫室氣體排放",
        "original_url": "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv",
        "format": "csv",
    },
    "t187ap46_L_2": {
        "desc": "能源管理",
        "original_url": "https://mopsfin.twse.com.tw/opendata/t187ap46_L_2.csv",
        "format": "csv",
    },
    "t187ap46_L_3": {
        "desc": "水資源管理",
        "original_url": "https://mopsfin.twse.com.tw/opendata/t187ap46_L_3.csv",
        "format": "csv",
    },
    "t187ap46_L_4": {
        "desc": "廢棄物管理",
        "original_url": "https://mopsfin.twse.com.tw/opendata/t187ap46_L_4.csv",
        "format": "csv",
    },
}

# TPEx 上櫃公司 — JSON 格式（tpex.org.tw openapi）
TPEX_DATASETS = {
    "t187ap46_O_1": {
        "desc": "溫室氣體排放 (上櫃)",
        "original_url": "https://www.tpex.org.tw/openapi/v1/t187ap46_O_1",
        "format": "json",
    },
    "t187ap46_O_2": {
        "desc": "能源管理 (上櫃)",
        "original_url": "https://www.tpex.org.tw/openapi/v1/t187ap46_O_2",
        "format": "json",
    },
    "t187ap46_O_3": {
        "desc": "水資源管理 (上櫃)",
        "original_url": "https://www.tpex.org.tw/openapi/v1/t187ap46_O_3",
        "format": "json",
    },
    "t187ap46_O_4": {
        "desc": "廢棄物管理 (上櫃)",
        "original_url": "https://www.tpex.org.tw/openapi/v1/t187ap46_O_4",
        "format": "json",
    },
}

ALL_DATASETS = {**TWSE_DATASETS, **TPEX_DATASETS}

# ── 下載邏輯 ──────────────────────────────────────────────────────────


def build_wayback_url(timestamp: str, original_url: str) -> str:
    """組合 Wayback Machine 下載 URL（使用 id_ 前綴取得原始檔案）。"""
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"


def try_decode_csv(content: bytes) -> str | None:
    """嘗試以 UTF-8 或 Big5 解碼 CSV 內容。"""
    for encoding in ("utf-8-sig", "utf-8", "big5", "cp950"):
        try:
            text = content.decode(encoding)
            # 簡單驗證：CSV 應有逗號分隔的多行
            lines = text.strip().split("\n")
            if len(lines) >= 2 and "," in lines[0]:
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def download_one(
    dataset_id: str,
    info: dict,
    session: requests.Session,
) -> Path | None:
    """嘗試多個時間戳下載單一資料集，成功則存檔並回傳路徑。"""
    fmt = info["format"]
    ext = "csv" if fmt == "csv" else "json"
    out_path = SEED_DIR / f"{dataset_id}.{ext}"

    for ts in TIMESTAMPS:
        url = build_wayback_url(ts, info["original_url"])
        print(f"  嘗試 {ts} ... ", end="", flush=True)

        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as exc:
            print(f"連線失敗: {exc}")
            continue

        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}")
            continue

        # 驗證內容非空 / 非 HTML 錯誤頁
        content = resp.content
        if len(content) < 100:
            print(f"內容過短 ({len(content)} bytes)")
            continue

        # 檢查是否為 Wayback 的 HTML 錯誤頁面
        if b"<html" in content[:500].lower() or b"<!doctype" in content[:500].lower():
            print("收到 HTML 頁面（非資料）")
            continue

        if fmt == "csv":
            text = try_decode_csv(content)
            if text is None:
                print("解碼失敗")
                continue
            lines = text.strip().split("\n")
            data_rows = len(lines) - 1  # 扣掉 header
            if data_rows < 1:
                print("無資料列")
                continue
            out_path.write_text(text, encoding="utf-8")
            print(f"OK — {data_rows} 筆資料")
            return out_path

        elif fmt == "json":
            try:
                data = resp.json()
            except (json.JSONDecodeError, ValueError):
                # 可能是 Big5 編碼的 JSON
                text = try_decode_csv(content)
                if text is None:
                    print("JSON 解碼失敗")
                    continue
                try:
                    data = json.loads(text)
                except (json.JSONDecodeError, ValueError):
                    print("JSON parse 失敗")
                    continue

            if not isinstance(data, list) or len(data) == 0:
                print(f"空陣列或非陣列 (type={type(data).__name__})")
                continue

            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"OK — {len(data)} 筆資料")
            return out_path

    return None


def print_summary(path: Path, fmt: str) -> None:
    """印出已下載檔案的摘要統計。"""
    text = path.read_text(encoding="utf-8")

    if fmt == "csv":
        lines = text.strip().split("\n")
        header = lines[0]
        data_lines = lines[1:]
        print(f"    欄位: {header[:120]}{'...' if len(header) > 120 else ''}")
        print(f"    筆數: {len(data_lines)}")
        # 取前 3 筆的公司名稱
        companies = []
        for line in data_lines[:5]:
            cols = line.split(",")
            if len(cols) >= 2:
                companies.append(f"{cols[0].strip()} {cols[1].strip()}")
        if companies:
            print(f"    範例: {', '.join(companies)}")

    elif fmt == "json":
        data = json.loads(text)
        print(f"    筆數: {len(data)}")
        if data:
            keys = list(data[0].keys())
            print(f"    欄位: {', '.join(keys[:8])}{'...' if len(keys) > 8 else ''}")
            # 取前 3 筆公司
            companies = []
            for rec in data[:5]:
                cid = rec.get("公司代號", "")
                cname = rec.get("公司名稱", "")
                if cid or cname:
                    companies.append(f"{cid} {cname}")
            if companies:
                print(f"    範例: {', '.join(companies)}")


# ── 主程式 ────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("Wayback Machine ESG 種子資料下載器")
    print("=" * 60)

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n輸出目錄: {SEED_DIR}\n")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ESG-seed-fetcher/1.0; "
                "+https://github.com/ai-cooperation)"
            ),
        }
    )

    success_count = 0
    fail_count = 0
    results: list[tuple[str, dict, Path | None]] = []

    for dataset_id, info in ALL_DATASETS.items():
        print(f"\n[{dataset_id}] {info['desc']}")
        path = download_one(dataset_id, info, session)
        results.append((dataset_id, info, path))

        if path:
            success_count += 1
        else:
            fail_count += 1
            print("  ✗ 所有時間戳皆失敗")

        # 避免對 Wayback Machine 發送過多請求
        time.sleep(1)

    # ── 摘要 ──
    print("\n" + "=" * 60)
    print("下載摘要")
    print("=" * 60)
    print(f"成功: {success_count} / {len(ALL_DATASETS)}")
    print(f"失敗: {fail_count} / {len(ALL_DATASETS)}")

    for dataset_id, info, path in results:
        if path:
            print(f"\n  [{dataset_id}] {info['desc']} → {path.name}")
            print_summary(path, info["format"])
        else:
            print(f"\n  [{dataset_id}] {info['desc']} → 未取得")

    print()
    if fail_count > 0:
        print(
            "提示: 部分資料集下載失敗，可嘗試調整 TIMESTAMPS 或手動瀏覽"
        )
        print("      https://web.archive.org/web/*/mopsfin.twse.com.tw/opendata/t187ap46*")


if __name__ == "__main__":
    main()
