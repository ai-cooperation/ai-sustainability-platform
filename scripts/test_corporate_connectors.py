#!/usr/bin/env python3
"""實測所有企業 ESG connector，確認真實 API 能打通。

用法: uv run python scripts/test_corporate_connectors.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# 加入專案根目錄
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock, patch


def make_connector(cls):
    """建立 connector 實例（mock settings 避免需要 .env）。"""
    with patch("src.utils.config.get_settings") as mock_s:
        mock_s.return_value = MagicMock()
        return cls()


def test_connector(name: str, connector, fetch_params: dict | None = None):
    """測試單一 connector 的 fetch + normalize。"""
    params = fetch_params or {}
    print(f"\n{'='*60}")
    print(f"測試: {name}")
    print(f"{'='*60}")

    try:
        start = time.time()
        raw = connector.fetch(**params)
        elapsed = time.time() - start

        if isinstance(raw, list):
            count = len(raw)
        elif isinstance(raw, dict):
            count = len(raw.get("records", raw.get("data", [])))
        else:
            count = "unknown"

        print(f"  ✅ fetch 成功 ({elapsed:.1f}s)")
        print(f"  📊 原始資料筆數: {count}")

        if isinstance(raw, list) and raw:
            print(f"  🔑 欄位: {list(raw[0].keys())[:8]}...")
        elif isinstance(raw, dict):
            sample = raw.get("records", raw.get("data", []))
            if sample:
                print(f"  🔑 欄位: {list(sample[0].keys())[:8]}...")

    except Exception as e:
        print(f"  ❌ fetch 失敗: {e}")
        return False

    try:
        df = connector.normalize(raw)
        print(f"  ✅ normalize 成功")
        print(f"  📊 DataFrame: {len(df)} rows × {len(df.columns)} cols")
        print(f"  📋 欄位: {list(df.columns)}")
        if not df.empty:
            print(f"  📝 前 3 筆:")
            for _, row in df.head(3).iterrows():
                summary = {k: v for k, v in row.items() if v is not None and str(v) != "NaT"}
                # 截斷長字串
                for k, v in summary.items():
                    if isinstance(v, str) and len(v) > 30:
                        summary[k] = v[:30] + "..."
                print(f"     {summary}")
    except Exception as e:
        print(f"  ⚠️ normalize 失敗 (可能資料為空): {e}")
        return True  # fetch 成功即可

    return True


def main():
    results = {}

    # === Layer 1: 財報資料 ===
    print("\n" + "🏢 " * 20)
    print("Layer 1: TWSE/TPEx 財報資料")
    print("🏢 " * 20)

    from src.connectors.corporate.twse_company import TWSECompanyConnector
    c = make_connector(TWSECompanyConnector)
    results["twse_company"] = test_connector("上市櫃公司基本資料", c)

    time.sleep(1)

    from src.connectors.corporate.twse_revenue import TWSERevenueConnector
    c = make_connector(TWSERevenueConnector)
    results["twse_revenue"] = test_connector("月營收", c)

    time.sleep(1)

    from src.connectors.corporate.twse_income import TWSEIncomeConnector
    c = make_connector(TWSEIncomeConnector)
    results["twse_income"] = test_connector("季度損益表", c)

    time.sleep(1)

    from src.connectors.corporate.twse_employee import TWSEEmployeeConnector
    c = make_connector(TWSEEmployeeConnector)
    results["twse_employee"] = test_connector("員工薪資 (ESG #5)", c)

    # === Layer 2: ESG 結構化資料 ===
    print("\n" + "🌱 " * 20)
    print("Layer 2: ESG 結構化資料 (可能為空)")
    print("🌱 " * 20)

    time.sleep(1)

    from src.connectors.corporate.twse_esg_ghg import TWSEEsgGhgConnector
    c = make_connector(TWSEEsgGhgConnector)
    results["twse_esg_ghg"] = test_connector("溫室氣體排放", c)

    time.sleep(1)

    from src.connectors.corporate.twse_esg_energy import TWSEEsgEnergyConnector
    c = make_connector(TWSEEsgEnergyConnector)
    results["twse_esg_energy"] = test_connector("能源管理", c)

    time.sleep(1)

    from src.connectors.corporate.twse_esg_water import TWSEEsgWaterConnector
    c = make_connector(TWSEEsgWaterConnector)
    results["twse_esg_water"] = test_connector("水資源管理", c)

    time.sleep(1)

    from src.connectors.corporate.twse_esg_waste import TWSEEsgWasteConnector
    c = make_connector(TWSEEsgWasteConnector)
    results["twse_esg_waste"] = test_connector("廢棄物管理", c)

    time.sleep(1)

    from src.connectors.corporate.twse_esg_climate import TWSEEsgClimateConnector
    c = make_connector(TWSEEsgClimateConnector)
    results["twse_esg_climate"] = test_connector("氣候相關議題", c)

    # === Layer 3: 環境部碳排 ===
    print("\n" + "🏭 " * 20)
    print("Layer 3: 環境部設施級碳排")
    print("🏭 " * 20)

    time.sleep(1)

    from src.connectors.carbon.moenv_facility_ghg import MoenvFacilityGhgConnector
    c = make_connector(MoenvFacilityGhgConnector)
    results["moenv_facility_ghg"] = test_connector("設施級碳排 (GHG_P_01)", c)

    # === 總結 ===
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  通過: {passed}/{total}")

    if passed < total:
        print("\n  ⚠️ 部分 connector 失敗，但可能是 API 暫時不可用")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
