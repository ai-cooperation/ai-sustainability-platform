"""Signal agent that collects real-time data from connectors."""

from __future__ import annotations

from datetime import UTC, datetime

from src.connectors.energy.carbon_intensity_uk import CarbonIntensityUKConnector
from src.connectors.environment.open_meteo_air_quality import (
    OpenMeteoAirQualityConnector,
)
from src.decision.models import SignalData
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SignalAgent:
    """Collects signals from sustainability data connectors.

    Runs key connectors and produces a summary of current conditions.
    Individual connector failures are caught and logged, not propagated.
    """

    def collect(self) -> dict:
        """Run connectors and return a summary dict of current conditions.

        Returns:
            Dict with keys like 'carbon_intensity', 'aqi', 'signals',
            plus a 'collected_at' timestamp. Failed sources are omitted.
        """
        summary: dict = {
            "signals": [],
            "collected_at": datetime.now(tz=UTC).isoformat(),
        }

        summary = self._collect_carbon_intensity(summary)
        summary = self._collect_air_quality(summary)

        logger.info(
            f"Collected {len(summary['signals'])} signals"
        )
        return summary

    def _collect_carbon_intensity(self, summary: dict) -> dict:
        """Collect carbon intensity signal from UK grid."""
        try:
            connector = CarbonIntensityUKConnector()
            result = connector.run(endpoint="current")
            if not result.data.empty:
                intensity = float(result.data["intensity_forecast"].iloc[0])
                index_val = str(result.data["index"].iloc[0])
                signal = SignalData(
                    source="carbon_intensity_uk",
                    value=intensity,
                    unit="gCO2/kWh",
                    timestamp=result.fetched_at,
                )
                return {
                    **summary,
                    "carbon_intensity": intensity,
                    "carbon_index": index_val,
                    "signals": [*summary["signals"], signal],
                }
        except Exception as e:
            logger.warning(f"Carbon intensity collection failed: {e}")
        return summary

    def _collect_air_quality(self, summary: dict) -> dict:
        """Collect air quality signal from Open-Meteo."""
        try:
            connector = OpenMeteoAirQualityConnector()
            result = connector.run(latitude=48.85, longitude=2.35)
            if not result.data.empty:
                latest = result.data.dropna(subset=["aqi"]).iloc[-1]
                aqi_val = float(latest["aqi"])
                signal = SignalData(
                    source="open_meteo_air_quality",
                    value=aqi_val,
                    unit="european_aqi",
                    timestamp=result.fetched_at,
                )
                return {
                    **summary,
                    "aqi": aqi_val,
                    "signals": [*summary["signals"], signal],
                }
        except Exception as e:
            logger.warning(f"Air quality collection failed: {e}")
        return summary
