#!/usr/bin/env python3
"""
WENDELL Core 33 - Base Agent
Abstract base class for all WENDELL agents (Python side).
Provides common lifecycle, health-check, and messaging primitives.
"""

import abc
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """Abstract base for every WENDELL agent."""

    agent_id: str = "base"
    agent_type: str = "generic"
    capabilities: list = []

    def __init__(self, agent_id: str, input_queue: str, output_queue: str):
        self.agent_id = agent_id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._start_time = time.time()
        self._healthy = True
        logger.info(f"BaseAgent.__init__ agent_id={agent_id}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def initialize(self, config_override: Optional[Dict] = None) -> Dict:
        """Initialise the agent; return status dict."""
        ...

    @abc.abstractmethod
    def run(self):
        """Main blocking loop."""
        ...

    def shutdown(self):
        """Graceful shutdown (override if needed)."""
        logger.info(f"Agent {self.agent_id} shutting down")

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy" if self._healthy else "degraded",
            "uptime": time.time() - self._start_time,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def uptime(self) -> float:
        return time.time() - self._start_time
