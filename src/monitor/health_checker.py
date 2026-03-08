"""API health checker for all data sources."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.connectors.base import BaseConnector
from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_all_connectors() -> list[BaseConnector]:
    """Instantiate all 31 connectors with default config.

    Returns:
        List of BaseConnector instances.
    """
    from src.connectors.agriculture import (
        EUAgriFoodConnector,
        FAOSTATConnector,
        GBIFConnector,
        USDANASSConnector,
    )
    from src.connectors.carbon import (
        ClimateTRACEConnector,
        ClimateWatchConnector,
        ClimatiqConnector,
        OpenClimateDataConnector,
        OWIDCarbonConnector,
    )
    from src.connectors.climate import (
        CopernicusCDSConnector,
        NOAACDOConnector,
        NOAAGHGConnector,
        OpenMeteoClimateConnector,
        OpenMeteoWeatherConnector,
        WorldBankClimateConnector,
    )
    from src.connectors.energy import (
        CarbonIntensityUKConnector,
        EIAConnector,
        ElectricityMapsConnector,
        NASAPowerConnector,
        NRELConnector,
        OpenMeteoSolarConnector,
        OpenPowerSystemConnector,
    )
    from src.connectors.environment import (
        AQICNConnector,
        EmissionsAPIConnector,
        EPAEnvirofactsConnector,
        EPAWaterQualityConnector,
        GlobalForestWatchConnector,
        OpenAQConnector,
        OpenMeteoAirQualityConnector,
    )
    from src.connectors.transport import (
        NRELAltFuelConnector,
        OpenChargeMapConnector,
    )

    connector_classes: list[type[BaseConnector]] = [
        # Energy (7)
        OpenMeteoSolarConnector,
        NASAPowerConnector,
        CarbonIntensityUKConnector,
        OpenPowerSystemConnector,
        EIAConnector,
        ElectricityMapsConnector,
        NRELConnector,
        # Climate (6)
        OpenMeteoWeatherConnector,
        OpenMeteoClimateConnector,
        NOAAGHGConnector,
        WorldBankClimateConnector,
        NOAACDOConnector,
        CopernicusCDSConnector,
        # Environment (7)
        OpenMeteoAirQualityConnector,
        EPAEnvirofactsConnector,
        EPAWaterQualityConnector,
        EmissionsAPIConnector,
        OpenAQConnector,
        AQICNConnector,
        GlobalForestWatchConnector,
        # Agriculture (4)
        FAOSTATConnector,
        EUAgriFoodConnector,
        USDANASSConnector,
        GBIFConnector,
        # Carbon (5)
        OWIDCarbonConnector,
        ClimateWatchConnector,
        OpenClimateDataConnector,
        ClimateTRACEConnector,
        ClimatiqConnector,
        # Transport (2)
        OpenChargeMapConnector,
        NRELAltFuelConnector,
    ]

    connectors: list[BaseConnector] = []
    for cls in connector_classes:
        try:
            connectors.append(cls())
        except Exception as exc:
            logger.warning(f"Failed to instantiate {cls.__name__}: {exc}")
    return connectors


def check_connector_health(connector: BaseConnector) -> dict[str, Any]:
    """Run health check on a single connector, catching all errors.

    Args:
        connector: A BaseConnector instance.

    Returns:
        Health status dict with keys: id, domain, status, latency_ms, message, checked_at.
    """
    checked_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        result = connector.health_check()
        return {
            "id": connector.name,
            "domain": connector.domain,
            "status": result["status"],
            "latency_ms": result["latency_ms"],
            "message": result["message"],
            "checked_at": checked_at,
        }
    except Exception as exc:
        logger.error(f"Health check crashed for {connector.name}: {exc}")
        return {
            "id": connector.name,
            "domain": connector.domain,
            "status": "down",
            "latency_ms": 0,
            "message": f"health_check() error: {exc}",
            "checked_at": checked_at,
        }


def check_all(connectors: list[BaseConnector]) -> dict[str, Any]:
    """Run health checks on all connectors.

    Each connector is checked independently; failures in one connector
    do not affect others.

    Args:
        connectors: List of BaseConnector instances.

    Returns:
        Full status report dict.
    """
    apis: list[dict[str, Any]] = []
    for conn in connectors:
        logger.info(f"Checking {conn.name}...")
        status = check_connector_health(conn)
        apis.append(status)

    healthy = sum(1 for a in apis if a["status"] == "healthy")
    degraded = sum(1 for a in apis if a["status"] == "degraded")
    down = sum(1 for a in apis if a["status"] == "down")

    return {
        "checked_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(apis),
        "healthy": healthy,
        "degraded": degraded,
        "down": down,
        "apis": apis,
    }


def generate_summary(report: dict[str, Any]) -> str:
    """Generate a human-readable summary for Telegram notification.

    Args:
        report: Health check report from check_all().

    Returns:
        Formatted summary string.
    """
    lines = [
        f"API Health Check - {report['checked_at']}",
        f"Total: {report['total']} | "
        f"Healthy: {report['healthy']} | "
        f"Degraded: {report['degraded']} | "
        f"Down: {report['down']}",
    ]

    down_apis = [a for a in report["apis"] if a["status"] == "down"]
    if down_apis:
        lines.append("")
        lines.append("DOWN:")
        for api in down_apis:
            lines.append(f"  - {api['id']}: {api['message']}")

    degraded_apis = [a for a in report["apis"] if a["status"] == "degraded"]
    if degraded_apis:
        lines.append("")
        lines.append("DEGRADED:")
        for api in degraded_apis:
            lines.append(f"  - {api['id']}: {api['latency_ms']}ms")

    return "\n".join(lines)
