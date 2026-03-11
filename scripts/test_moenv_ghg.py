#!/usr/bin/env python3
"""Quick test: MOENV GHG facility data with real API key."""
from __future__ import annotations
import io, sys
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, ".")
from unittest.mock import MagicMock, patch

with patch("src.utils.config.get_settings") as mock_s:
    s = MagicMock()
    s.moenv_api_key = "c4427676-0b60-481e-a029-e97cc8f6b2ac"
    mock_s.return_value = s
    from src.connectors.carbon.moenv_facility_ghg import MoenvFacilityGhgConnector
    c = MoenvFacilityGhgConnector()

    print("=== Fetching MOENV GHG_P_01 (limit=20) ===")
    raw = c.fetch(limit=20)
    print(f"Raw records: {len(raw)}")

    for r in raw[:5]:
        name = r.get("companyname", "?")
        total = r.get("tot_value", "?")
        year = r.get("app_year", "?")
        print(f"  [{year}] {name}: {total} tCO2e")

    df = c.normalize(raw)
    print(f"\nDataFrame: {len(df)} rows x {len(df.columns)} cols")
    print(f"Columns: {list(df.columns)}")
    print(df[["facility_name", "total_emissions", "report_year"]].to_string())
