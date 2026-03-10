"""Export pipeline parquet data to JSON for the dashboard.

Reads the latest parquet files from data/processed/ and writes
summary JSON to data/dashboard/ for the Next.js frontend to consume.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")
DASHBOARD_DIR = Path("data/dashboard")
DOMAINS = ["energy", "climate", "environment", "agriculture", "carbon"]

# Only these columns will be exported as KPIs per domain
KPI_WHITELIST: dict[str, list[str]] = {
    "energy": [
        "shortwave_radiation", "direct_radiation", "diffuse_radiation",
        "solar_radiation", "temperature", "intensity_forecast",
        "DE_solar_generation_actual", "DE_wind_generation_actual",
        "DE_load_actual_entsoe_transparency", "DE_price_day_ahead",
    ],
    "climate": [
        "co2_ppm", "trend", "temperature_max", "temperature_min", "precipitation",
    ],
    "environment": [
        "pm2_5", "pm10", "no2", "o3", "co", "aqi",
    ],
    "agriculture": [
        "price",
    ],
    "carbon": [
        "co2", "co2_per_capita", "energy_per_capita",
        "Fossil-Fuel-And-Industry", "Land-Use-Change-Emissions",
        "Ocean-Sink", "Land-Sink",
    ],
}

# Only these columns will appear in time_series sparklines
SPARKLINE_WHITELIST: dict[str, list[str]] = {
    "energy": [
        "shortwave_radiation", "direct_radiation",
        "solar_radiation", "temperature",
        "DE_solar_generation_actual", "DE_wind_generation_actual",
    ],
    "climate": [
        "co2_ppm", "temperature_max", "precipitation",
    ],
    "environment": [
        "pm2_5", "pm10", "no2", "o3",
    ],
    "agriculture": [
        "price",
    ],
    "carbon": [
        "co2", "co2_per_capita", "Fossil-Fuel-And-Industry",
    ],
}


def find_latest_parquet(domain: str) -> Path | None:
    """Find the most recent parquet file for a domain."""
    domain_dir = PROCESSED_DIR / domain
    if not domain_dir.exists():
        return None
    files = sorted(domain_dir.glob("*.parquet"), reverse=True)
    return files[0] if files else None


def safe_json_value(val):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if pd.isna(val):
        return None
    if hasattr(val, "item"):  # numpy scalar
        return val.item()
    return val


def export_domain(domain: str) -> dict | None:
    """Read latest parquet and return a summary dict."""
    path = find_latest_parquet(domain)
    if path is None:
        print(f"  {domain}: no parquet found, skipping")
        return None

    df = pd.read_parquet(path)
    print(f"  {domain}: {len(df)} records from {path.name}")

    summary = {
        "domain": domain,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "record_count": len(df),
        "file": path.name,
        "sources": sorted(df["source"].unique().tolist()) if "source" in df.columns else [],
        "columns": list(df.columns),
    }

    # Extract KPIs — only whitelisted columns
    allowed_kpis = KPI_WHITELIST.get(domain, [])
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    kpi_cols = [c for c in numeric_cols if c in allowed_kpis]
    kpis = {}
    for col in kpi_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        kpis[col] = {
            "latest": safe_json_value(series.iloc[-1]),
            "mean": safe_json_value(series.mean()),
            "min": safe_json_value(series.min()),
            "max": safe_json_value(series.max()),
            "count": len(series),
        }
    summary["kpis"] = kpis

    # Extract time series for sparklines (last 168 points = 7 days × 24 hours)
    allowed_sparklines = SPARKLINE_WHITELIST.get(domain, [])
    time_series = {}
    if "timestamp" in df.columns:
        for source in summary["sources"]:
            source_df = df[df["source"] == source].sort_values("timestamp").tail(168)
            ts_data = {}
            for col in numeric_cols:
                if col not in allowed_sparklines:
                    continue
                values = source_df[col].dropna().tolist()
                if values:
                    ts_data[col] = [safe_json_value(v) for v in values]
            if ts_data:
                time_series[source] = {
                    "timestamps": source_df["timestamp"].astype(str).tolist(),
                    "data": ts_data,
                }
    summary["time_series"] = time_series

    return summary


def main():
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    print("Exporting dashboard JSON...")

    overview = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "domains": {},
    }

    for domain in DOMAINS:
        result = export_domain(domain)
        if result is not None:
            # Save per-domain JSON
            domain_path = DASHBOARD_DIR / f"{domain}.json"
            with open(domain_path, "w") as f:
                json.dump(result, f, indent=2)

            # Add summary to overview
            overview["domains"][domain] = {
                "record_count": result["record_count"],
                "sources": result["sources"],
                "kpis": result["kpis"],
            }

    # Save overview JSON
    overview_path = DASHBOARD_DIR / "overview.json"
    with open(overview_path, "w") as f:
        json.dump(overview, f, indent=2)

    print(f"Dashboard JSON exported to {DASHBOARD_DIR}/")
    print(f"  Domains with data: {list(overview['domains'].keys())}")


if __name__ == "__main__":
    main()
