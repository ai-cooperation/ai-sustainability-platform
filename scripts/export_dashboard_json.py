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

    # Extract numeric columns for KPI summary
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    kpis = {}
    for col in numeric_cols:
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

    # Extract time series for sparklines (last 30 data points per source)
    time_series = {}
    if "timestamp" in df.columns:
        for source in summary["sources"]:
            source_df = df[df["source"] == source].sort_values("timestamp").tail(30)
            ts_data = {}
            for col in numeric_cols:
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
