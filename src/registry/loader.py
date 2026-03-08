"""Load and validate the dataset registry."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError

from src.registry.models import DatasetEntry, DatasetRegistry
from src.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_REGISTRY_PATH = Path("data/registry/datasets.yaml")


def load_registry(path: Path | None = None) -> DatasetRegistry:
    """Load and validate datasets.yaml.

    Args:
        path: Path to datasets.yaml. Defaults to data/registry/datasets.yaml.

    Returns:
        Validated DatasetRegistry.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If validation fails.
    """
    if path is None:
        path = DEFAULT_REGISTRY_PATH

    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    raw = yaml.safe_load(path.read_text())

    try:
        registry = DatasetRegistry.model_validate(raw)
    except PydanticValidationError as e:
        raise ValueError(f"Registry validation failed: {e}") from e

    logger.info(f"Loaded {len(registry.datasets)} datasets from {path}")
    return registry


def find_dataset(registry: DatasetRegistry, dataset_id: str) -> DatasetEntry | None:
    """Find a dataset by ID.

    Args:
        registry: Loaded registry.
        dataset_id: Dataset identifier.

    Returns:
        DatasetEntry if found, None otherwise.
    """
    for ds in registry.datasets:
        if ds.id == dataset_id:
            return ds
    return None


def filter_by_domain(registry: DatasetRegistry, domain: str) -> list[DatasetEntry]:
    """Filter datasets by domain.

    Args:
        registry: Loaded registry.
        domain: Domain to filter by.

    Returns:
        List of matching DatasetEntry.
    """
    return [ds for ds in registry.datasets if ds.domain == domain]
