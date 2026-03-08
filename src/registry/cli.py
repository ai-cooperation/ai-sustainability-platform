"""CLI for dataset registry management."""

from __future__ import annotations

import argparse
import sys

from src.registry.loader import filter_by_domain, find_dataset, load_registry


def cmd_list(args: argparse.Namespace) -> None:
    """List all datasets."""
    registry = load_registry()
    domain_filter = getattr(args, "domain", None)

    datasets = (
        filter_by_domain(registry, domain_filter) if domain_filter else registry.datasets
    )

    print(f"\n{'ID':<35} {'Domain':<15} {'Provider':<25} {'Auth':<10} {'Status'}")
    print("-" * 100)
    for ds in datasets:
        print(f"{ds.id:<35} {ds.domain:<15} {ds.provider:<25} {ds.access.auth:<10} {ds.status}")
    print(f"\nTotal: {len(datasets)} datasets")


def cmd_info(args: argparse.Namespace) -> None:
    """Show detailed info for a dataset."""
    registry = load_registry()
    ds = find_dataset(registry, args.id)

    if ds is None:
        print(f"Dataset not found: {args.id}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  ID:        {ds.id}")
    print(f"  Name:      {ds.name}")
    print(f"  Domain:    {ds.domain}")
    print(f"  Provider:  {ds.provider}")
    print(f"  Endpoint:  {ds.access.endpoint}")
    print(f"  Auth:      {ds.access.auth}")
    print(f"  Rate:      {ds.access.rate_limit}")
    print(f"  Update:    {ds.update_frequency}")
    print(f"  Format:    {ds.data_format}")
    print(f"  Connector: {ds.connector_class}")
    print(f"  Module:    {ds.connector_module}")
    print(f"  Fields:    {', '.join(ds.fields)}")
    print(f"  Status:    {ds.status}")
    if ds.description:
        print(f"  Desc:      {ds.description}")
    print(f"{'='*60}\n")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate the registry file."""
    try:
        registry = load_registry()
        print(f"✓ Registry valid: {len(registry.datasets)} datasets")

        # Check for duplicate IDs
        ids = [ds.id for ds in registry.datasets]
        dupes = [x for x in ids if ids.count(x) > 1]
        if dupes:
            print(f"✗ Duplicate IDs found: {set(dupes)}")
            sys.exit(1)

        # Check domains
        valid_domains = {"energy", "climate", "environment", "agriculture", "transport", "carbon"}
        for ds in registry.datasets:
            if ds.domain not in valid_domains:
                print(f"✗ Invalid domain '{ds.domain}' for {ds.id}")
                sys.exit(1)

        print("✓ All checks passed")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset Registry CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List all datasets")
    list_parser.add_argument("--domain", help="Filter by domain")

    info_parser = sub.add_parser("info", help="Show dataset details")
    info_parser.add_argument("id", help="Dataset ID")

    sub.add_parser("validate", help="Validate registry file")

    args = parser.parse_args()
    commands = {"list": cmd_list, "info": cmd_info, "validate": cmd_validate}
    commands[args.command](args)


if __name__ == "__main__":
    main()
