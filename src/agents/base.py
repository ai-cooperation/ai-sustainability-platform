"""Base agent interface for multi-agent decision system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.utils.logging import get_logger


@dataclass(frozen=True)
class AgentMessage:
    """Immutable message exchanged between agents."""

    role: str
    content: str
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResponse:
    """Immutable agent analysis result."""

    agent_name: str
    probability: float | None
    reasoning: str
    confidence: str  # low|medium|high
    data_sources: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self.logger = get_logger(self.__class__.__name__)
        self.memory: list[AgentMessage] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier."""

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role description."""

    @abstractmethod
    def perceive(self, data: dict) -> list[str]:
        """Extract relevant signals from input data.

        Args:
            data: Input data (connector results, signals, etc.).

        Returns:
            List of observations/signals.
        """

    @abstractmethod
    def reason(self, signals: list[str], context: list[AgentMessage] | None = None) -> str:
        """Analyze signals and produce reasoning.

        Args:
            signals: Observations from perceive().
            context: Optional conversation context from other agents.

        Returns:
            Reasoning text.
        """

    @abstractmethod
    def respond(self, reasoning: str) -> AgentResponse:
        """Produce a structured response based on reasoning.

        Args:
            reasoning: Output from reason().

        Returns:
            Structured agent response.
        """

    def run(self, data: dict, context: list[AgentMessage] | None = None) -> AgentResponse:
        """Execute full agent pipeline: perceive → reason → respond."""
        self.logger.info(f"Agent {self.name} running")
        signals = self.perceive(data)
        reasoning = self.reason(signals, context)
        response = self.respond(reasoning)
        self.memory.append(
            AgentMessage(
                role=self.role,
                content=reasoning,
                agent_name=self.name,
            )
        )
        return response
