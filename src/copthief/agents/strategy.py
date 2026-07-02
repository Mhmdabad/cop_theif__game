"""Strategy contract for agent decision making (issue #34).

A ``Strategy`` turns the agent's partial observation into a legal ``Action``.
The engine validates every returned action, so a misbehaving strategy falls
back to a safe heuristic rather than crashing the game (PRD §3.5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action


class Strategy(ABC):
    """Abstract agent policy."""

    @abstractmethod
    def choose_action(self, observation: Observation, last_message: str) -> Action:
        """Return the next action for the agent described by ``observation``."""
