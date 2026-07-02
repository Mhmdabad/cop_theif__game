"""CopThiefSDK — single entry point for all business logic (issue #20).

CLI, GUI, and external consumers drive the game through this class rather than
touching engine/orchestrator internals directly (guidelines §4.1; PLAN ADR-5).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from copthief.constants import Outcome, Role
from copthief.llm.provider import LLMProvider, create_provider
from copthief.services.game_engine import Action, GameEngine
from copthief.services.scoring import ScoreBook
from copthief.shared.config import Config
from copthief.shared.gatekeeper import ApiGatekeeper

Strategy = Callable[[Role, GameEngine], Action]


class CopThiefSDK:
    """High-level facade that wires config, engine, scoring, gatekeeper, and LLM."""

    def __init__(
        self,
        config: Config,
        *,
        gatekeeper: ApiGatekeeper | None = None,
        provider: LLMProvider | None = None,
        rate_limits_config: dict[str, Any] | None = None,
    ):
        self.config = config
        self.engine = GameEngine(config.grid_size, config.max_moves, config.max_barriers)
        self.scorebook = ScoreBook(config.scoring)
        self.gatekeeper = gatekeeper or self._default_gatekeeper(rate_limits_config)
        self.provider = provider or create_provider(config.llm)
        self._sub_game_moves: list[int] = []

    @staticmethod
    def _default_gatekeeper(rate_limits_config: dict[str, Any] | None) -> ApiGatekeeper:
        if rate_limits_config is None:
            path = Path(__file__).resolve().parents[3] / "config" / "rate_limits.json"
            rate_limits_config = json.loads(path.read_text(encoding="utf-8"))
        return ApiGatekeeper(rate_limits_config)

    def play_sub_game(
        self,
        strategy_a: Strategy,
        strategy_b: Strategy,
        cop_agent: str,
        thief_agent: str,
    ) -> Outcome:
        """Run one pursuit round and record its score.

        ``strategy_a``/``strategy_b`` receive the role they are playing this
        sub-game and the current engine, and must return a legal ``Action``.
        """
        self.engine.reset()
        strategies = {"A": strategy_a, "B": strategy_b}
        while self.engine.state.outcome == Outcome.ONGOING:
            role = self.engine.state.turn
            agent = cop_agent if role == Role.COP else thief_agent
            strategy = strategies[agent]
            action = strategy(role, self.engine)
            self.engine.apply_action(role, action)

        self.scorebook.record(cop_agent, thief_agent, self.engine.state.outcome)
        self._sub_game_moves.append(self.engine.state.move_number)
        return self.engine.state.outcome

    def play_game(
        self,
        strategy_a: Strategy,
        strategy_b: Strategy,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Run ``num_games`` sub-games with the configured role swap and report."""
        self.scorebook = ScoreBook(self.config.scoring)
        self._sub_game_moves = []
        swap_at = self.config.swap_at_subgame
        for index in range(1, self.config.num_games + 1):
            if index < swap_at:
                cop_agent, thief_agent = "A", "B"
            else:
                cop_agent, thief_agent = "B", "A"
            self.play_sub_game(strategy_a, strategy_b, cop_agent, thief_agent)
        return self.build_report(metadata)

    def build_report(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Assemble the internal JSON game report from recorded sub-games."""
        totals = self.scorebook.totals()
        sub_games = [
            {
                "index": i + 1,
                "cop_agent": entry.cop_agent,
                "thief_agent": entry.thief_agent,
                "winner": entry.outcome.value,
                "moves": self._sub_game_moves[i],
                "cop_score": entry.cop_score,
                "thief_score": entry.thief_score,
            }
            for i, entry in enumerate(self.scorebook.sub_games)
        ]
        return {
            **metadata,
            "sub_games": sub_games,
            "totals": {"by_role": totals.by_role, "by_agent": totals.by_agent},
        }
