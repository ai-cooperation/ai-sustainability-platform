"""Live integration test for all no-key-required connectors.

Calls each connector's .run() with default/minimal parameters and reports
status, record count, and a sample of returned data.
"""

from __future__ import annotations

import signal
import sys
import time
from dataclasses import dataclass

# Ensure project root is on sys.path so `src.*` imports work.
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Energy connectors
from src.connectors.agriculture.eu_agri_food import EUAgriFoodConnector

# Agriculture connectors
from src.connectors.agriculture.faostat import FAOSTATConnector
from src.connectors.agriculture.gbif import GBIFConnector
from src.connectors.carbon.open_climate_data import OpenClimateDataConnector

# Carbon connectors
from src.connectors.carbon.owid_carbon import OWIDCarbonConnector
from src.connectors.climate.open_meteo_climate import OpenMeteoClimateConnector

# Climate connectors
from src.connectors.climate.open_meteo_weather import OpenMeteoWeatherConnector
from src.connectors.climate.world_bank_climate import WorldBankClimateConnector
from src.connectors.energy.carbon_intensity_uk import CarbonIntensityUKConnector
from src.connectors.energy.nasa_power import NASAPowerConnector
from src.connectors.energy.open_meteo_solar import OpenMeteoSolarConnector
from src.connectors.energy.open_power_system import OpenPowerSystemConnector
from src.connectors.environment.emissions_api import EmissionsAPIConnector

# Environment connectors
from src.connectors.environment.open_meteo_air_quality import OpenMeteoAirQualityConnector

TIMEOUT_SECONDS = 10


class TimeoutError(Exception):
    """Raised when a connector call exceeds the timeout."""


def _timeout_handler(_signum: int, _frame: Any) -> None:
    raise TimeoutError(f"Exceeded {TIMEOUT_SECONDS}s timeout")


@dataclass
class TestResult:
    """Outcome of a single connector test."""

    name: str
    domain: str
    status: str           # "OK" or "FAIL"
    record_count: int
    elapsed_s: float
    sample: str
    error: str


def _truncate(text: str, max_len: int = 120) -> str:
    """Truncate text to max_len, appending '...' if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# Each entry: (ConnectorClass, run_kwargs)
# Use small/fast parameters to keep within the 10 s timeout.
CONNECTORS: list[tuple[type, dict[str, Any]]] = [
    # --- Energy ---
    (OpenMeteoSolarConnector, {}),
    (NASAPowerConnector, {}),
    (CarbonIntensityUKConnector, {}),
    (OpenPowerSystemConnector, {"nrows": 50}),
    # --- Climate ---
    (OpenMeteoWeatherConnector, {}),
    (OpenMeteoClimateConnector, {
        "start_date": "2020-01-01",
        "end_date": "2020-01-31",
    }),
    (WorldBankClimateConnector, {}),
    # --- Environment ---
    (OpenMeteoAirQualityConnector, {}),
    (EmissionsAPIConnector, {"limit": 10}),
    # --- Agriculture ---
    (FAOSTATConnector, {
        "faostat_domain": "QCL",
        "area_code": "5000",
        "year": "2022",
    }),
    (EUAgriFoodConnector, {}),
    (GBIFConnector, {"country": "TW", "limit": 20}),
    # --- Carbon ---
    (OWIDCarbonConnector, {"country": "World", "start_year": 2020, "end_year": 2022}),
    (OpenClimateDataConnector, {"dataset": "global-carbon-budget"}),
]


def test_connector(cls: type, kwargs: dict[str, Any]) -> TestResult:
    """Instantiate and run a single connector, respecting the timeout."""
    connector = cls()
    name = connector.name
    domain_str = connector.domain

    start = time.time()
    try:
        # Set an alarm-based timeout (Unix only).
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

        result = connector.run(**kwargs)

        signal.alarm(0)  # cancel alarm
        signal.signal(signal.SIGALRM, old_handler)

        elapsed = time.time() - start
        df = result.data
        record_count = result.record_count

        # Build a small sample string: first row as dict.
        if not df.empty:
            sample_row = df.iloc[0].to_dict()
            sample_str = _truncate(str(sample_row))
        else:
            sample_str = "(empty)"

        return TestResult(
            name=name,
            domain=domain_str,
            status="OK",
            record_count=record_count,
            elapsed_s=round(elapsed, 2),
            sample=sample_str,
            error="",
        )

    except Exception as exc:
        signal.alarm(0)
        elapsed = time.time() - start
        err_line = _truncate(str(exc), 200)
        return TestResult(
            name=name,
            domain=domain_str,
            status="FAIL",
            record_count=0,
            elapsed_s=round(elapsed, 2),
            sample="",
            error=err_line,
        )


def main() -> None:
    print("=" * 80)
    print("  LIVE CONNECTOR TEST")
    print(f"  Timeout per connector: {TIMEOUT_SECONDS}s")
    print("=" * 80)
    print()

    results: list[TestResult] = []

    for cls, kwargs in CONNECTORS:
        # Print progress inline.
        connector_name = cls.__name__
        print(f"  Testing {connector_name} ... ", end="", flush=True)
        tr = test_connector(cls, kwargs)
        results.append(tr)

        if tr.status == "OK":
            print(f"OK  ({tr.record_count} records, {tr.elapsed_s}s)")
        else:
            print(f"FAIL  ({tr.elapsed_s}s)")

    # --- Detailed results ---
    print()
    print("=" * 80)
    print("  DETAILED RESULTS")
    print("=" * 80)

    for tr in results:
        icon = "[OK]  " if tr.status == "OK" else "[FAIL]"
        print(f"\n{icon} {tr.name} ({tr.domain})")
        print(f"      Status:  {tr.status}")
        print(f"      Records: {tr.record_count}")
        print(f"      Time:    {tr.elapsed_s}s")
        if tr.sample:
            print(f"      Sample:  {tr.sample}")
        if tr.error:
            print(f"      Error:   {tr.error}")

    # --- Summary ---
    ok_count = sum(1 for r in results if r.status == "OK")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    total = len(results)

    print()
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"  Total:  {total}")
    print(f"  OK:     {ok_count}")
    print(f"  FAIL:   {fail_count}")
    print(f"  Pass rate: {ok_count}/{total} ({ok_count * 100 // total}%)")
    print("=" * 80)

    if fail_count > 0:
        print("\n  Failed connectors:")
        for r in results:
            if r.status == "FAIL":
                print(f"    - {r.name}: {r.error}")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
