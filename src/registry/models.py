"""Pydantic models for dataset registry schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AccessInfo(BaseModel):
    """API access configuration."""

    type: str = Field(description="Access type: api|download|github")
    endpoint: str = Field(description="API endpoint URL")
    auth: str = Field(description="Auth method: none|api_key|token|oauth")
    rate_limit: str = Field(default="", description="Rate limit description")


class DatasetEntry(BaseModel):
    """A single dataset/API entry in the registry."""

    id: str = Field(description="Unique identifier (snake_case)")
    name: str = Field(description="Human-readable name")
    domain: str = Field(description="Domain: energy|climate|environment|agriculture|transport|carbon")
    provider: str = Field(description="Data provider name")
    access: AccessInfo
    update_frequency: str = Field(description="e.g., hourly, daily, weekly, monthly, annual")
    data_format: str = Field(description="e.g., json, csv, netcdf")
    connector_class: str = Field(description="Python class name")
    connector_module: str = Field(description="Python module path")
    fields: list[str] = Field(default_factory=list, description="Key data fields")
    status: str = Field(default="active", description="active|inactive|deprecated")
    description: str = Field(default="", description="Brief description")


class DatasetRegistry(BaseModel):
    """Root model for the dataset registry."""

    datasets: list[DatasetEntry]
