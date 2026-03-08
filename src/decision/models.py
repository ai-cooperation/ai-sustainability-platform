"""Data models for the decision intelligence system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class SignalData:
    """Immutable data signal from a connector."""

    source: str
    value: float
    unit: str
    timestamp: datetime


@dataclass(frozen=True)
class ForecastPosition:
    """Immutable debate position from an agent."""

    agent_name: str
    probability: float  # 0.0 to 1.0
    reasoning: str
    confidence: str  # low | medium | high


@dataclass(frozen=True)
class ForecastResult:
    """Immutable final forecast from the judge."""

    question: str
    probability: float
    confidence: str
    reasoning: str
    positions: tuple[ForecastPosition, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
