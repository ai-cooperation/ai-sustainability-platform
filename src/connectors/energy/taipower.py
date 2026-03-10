"""TaiPower (台灣電力公司) real-time generation connector."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError

# Map HTML anchor names to English column prefixes and renewable flag
_TYPE_MAP: dict[str, tuple[str, bool]] = {
    "solar": ("solar", True),
    "wind": ("wind", True),
    "hydro": ("hydro", True),
    "lng": ("lng", False),
    "ipplng": ("ipp_lng", False),
    "coal": ("coal", False),
    "ippcoal": ("ipp_coal", False),
    "cogen": ("cogen", False),
    "fueloil": ("oil", False),
    "EnergyStorageSystem": ("storage", False),
    "OtherRenewableEnergy": ("other_renewable", True),
}

_ANCHOR_RE = re.compile(r"<A NAME='(\w+)'></A>")


def _parse_subtotal_mw(value: str) -> float | None:
    """Parse MW from subtotal format like '15918.1(27.068%)'."""
    if not value or not isinstance(value, str):
        return None
    # Extract the number before the parenthesis
    paren = value.find("(")
    num_str = value[:paren].strip() if paren > 0 else value.strip()
    try:
        return float(num_str)
    except (ValueError, TypeError):
        return None


def _parse_subtotal_pct(value: str) -> float | None:
    """Parse percentage from subtotal format like '15918.1(27.068%)'."""
    if not value or not isinstance(value, str):
        return None
    start = value.find("(")
    end = value.find("%")
    if start < 0 or end < 0:
        return None
    try:
        return float(value[start + 1 : end])
    except (ValueError, TypeError):
        return None


class TaiPowerConnector(BaseConnector):
    """Fetch real-time power generation mix from TaiPower.

    Endpoint: https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json
    Auth: None required.
    """

    BASE_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json"

    @property
    def name(self) -> str:
        return "taipower"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch real-time generation data from TaiPower."""
        try:
            response = requests.get(
                params.get("url", self.BASE_URL),
                timeout=30,
                headers={"User-Agent": "ai-sustainability-platform/1.0"},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"TaiPower API request failed: {exc}") from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Extract generation mix summary from TaiPower data.

        Returns a single-row DataFrame with:
        - timestamp, source
        - Per-type MW and capacity: solar_mw, wind_mw, hydro_mw, etc.
        - Totals: renewable_mw, total_mw, renewable_pct
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from TaiPower API")

        aa_data = raw_data.get("aaData", [])
        if not aa_data:
            raise ConnectorError("No aaData in TaiPower response")

        # Parse timestamp from response (format: "2026-03-10 12:00")
        ts_str = raw_data.get("", "")
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        # Find subtotal rows (小計) per energy type using HTML anchor name
        type_data: dict[str, dict[str, float | None]] = {}
        for row in aa_data:
            if not isinstance(row, list) or len(row) < 6:
                continue
            unit_name = row[2].strip() if isinstance(row[2], str) else ""
            if not unit_name.startswith("小計"):
                continue

            # Extract anchor name from HTML: <A NAME='solar'></A>
            energy_type_html = row[0] if isinstance(row[0], str) else ""
            match = _ANCHOR_RE.search(energy_type_html)
            if not match:
                continue
            anchor = match.group(1)

            capacity = _parse_subtotal_mw(str(row[3]))
            output = _parse_subtotal_mw(str(row[4]))

            type_data[anchor] = {
                "capacity_mw": capacity,
                "output_mw": output,
            }

        # Build summary row
        renewable_mw = 0.0
        total_mw = 0.0
        record: dict[str, Any] = {
            "timestamp": ts,
        }

        for anchor, (col_prefix, is_renewable) in _TYPE_MAP.items():
            data = type_data.get(anchor, {})
            mw = data.get("output_mw") or 0.0
            record[f"{col_prefix}_mw"] = data.get("output_mw")
            record[f"{col_prefix}_capacity_mw"] = data.get("capacity_mw")

            total_mw += mw
            if is_renewable:
                renewable_mw += mw

        record["renewable_mw"] = renewable_mw
        record["total_mw"] = total_mw
        record["renewable_pct"] = (
            round(renewable_mw / total_mw * 100, 2) if total_mw > 0 else 0.0
        )

        return pd.DataFrame([record])

    def _health_check_params(self) -> dict:
        """No special params needed for health check."""
        return {}
