"""Tests for dataset registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.registry.loader import filter_by_domain, find_dataset, load_registry


class TestRegistry:
    def test_load_registry(self):
        registry = load_registry()
        assert len(registry.datasets) == 31

    def test_all_ids_unique(self):
        registry = load_registry()
        ids = [ds.id for ds in registry.datasets]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"

    def test_valid_domains(self):
        registry = load_registry()
        valid = {"energy", "climate", "environment", "agriculture", "transport", "carbon"}
        for ds in registry.datasets:
            assert ds.domain in valid, f"{ds.id} has invalid domain: {ds.domain}"

    def test_domain_counts(self):
        registry = load_registry()
        counts = {}
        for ds in registry.datasets:
            counts[ds.domain] = counts.get(ds.domain, 0) + 1
        assert counts["energy"] == 7
        assert counts["climate"] == 6
        assert counts["environment"] == 7
        assert counts["agriculture"] == 4
        assert counts["carbon"] == 5
        assert counts["transport"] == 2

    def test_find_dataset(self):
        registry = load_registry()
        ds = find_dataset(registry, "open_meteo_solar")
        assert ds is not None
        assert ds.domain == "energy"

    def test_find_dataset_not_found(self):
        registry = load_registry()
        assert find_dataset(registry, "nonexistent") is None

    def test_filter_by_domain(self):
        registry = load_registry()
        energy = filter_by_domain(registry, "energy")
        assert len(energy) == 7
        assert all(ds.domain == "energy" for ds in energy)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_registry(Path("/nonexistent/path.yaml"))

    def test_all_have_connector_class(self):
        registry = load_registry()
        for ds in registry.datasets:
            assert ds.connector_class, f"{ds.id} missing connector_class"
            assert ds.connector_module, f"{ds.id} missing connector_module"
