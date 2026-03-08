"""Forecast orchestrator that coordinates the multi-agent decision flow."""

from __future__ import annotations

from src.decision.analyst_agent import AnalystAgent
from src.decision.debate_agent import create_debate_agents
from src.decision.groq_client import GroqClient
from src.decision.judge_agent import JudgeAgent
from src.decision.models import ForecastResult
from src.decision.signal_agent import SignalAgent
from src.utils.logging import get_logger
from src.utils.telegram import send_telegram

logger = get_logger(__name__)


class ForecastOrchestrator:
    """Coordinates the full forecast pipeline.

    Flow: SignalAgent -> AnalystAgent -> DebateAgents -> JudgeAgent
    """

    def __init__(self, groq_client: GroqClient | None = None):
        self._client = groq_client or GroqClient()
        self._signal_agent = SignalAgent()
        self._analyst = AnalystAgent(self._client)
        self._debate_agents = create_debate_agents(self._client)
        self._judge = JudgeAgent(self._client)

    def run_forecast(self, question: str) -> ForecastResult:
        """Execute the full forecast pipeline.

        Args:
            question: The forecast question to answer.

        Returns:
            ForecastResult with synthesized prediction.
        """
        logger.info(f"Starting forecast: {question}")

        # Step 1: Collect signals
        signals = self._signal_agent.collect()
        logger.info(f"Collected {len(signals.get('signals', []))} signals")

        # Step 2: Analyze trends
        analysis = self._analyst.analyze(signals)
        logger.info("Analysis complete")

        # Step 3: Run debate (sequential to respect rate limits)
        positions = []
        for agent in self._debate_agents:
            position = agent.debate(analysis, question)
            positions.append(position)
            logger.info(
                f"{agent.name}: p={position.probability:.2f}, "
                f"confidence={position.confidence}"
            )

        # Step 4: Judge synthesizes
        result = self._judge.judge(positions, analysis, question)
        logger.info(
            f"Final forecast: p={result.probability:.2f}, "
            f"confidence={result.confidence}"
        )

        # Step 5: Send Telegram notification
        self._notify(result)

        return result

    def _notify(self, result: ForecastResult) -> None:
        """Send forecast result summary via Telegram."""
        positions_text = "\n".join(
            f"  - {p.agent_name}: {p.probability:.0%} ({p.confidence})"
            for p in result.positions
        )

        message = (
            f"<b>Forecast Result</b>\n\n"
            f"<b>Q:</b> {result.question}\n"
            f"<b>Probability:</b> {result.probability:.0%}\n"
            f"<b>Confidence:</b> {result.confidence}\n\n"
            f"<b>Agent Positions:</b>\n{positions_text}\n\n"
            f"<b>Reasoning:</b> {result.reasoning[:300]}"
        )

        send_telegram(message)
