"""copthief.agents — move-selection strategies (heuristic, optional Q-learning)."""

from __future__ import annotations

from typing import Any

from copthief import __version__ as __version__
from copthief.agents.heuristic import HeuristicStrategy
from copthief.agents.qlearning import QLearningStrategy
from copthief.agents.strategy import Strategy

__all__ = ["__version__", "HeuristicStrategy", "QLearningStrategy", "Strategy", "create_strategy"]


def create_strategy(config: dict[str, Any], grid_size: tuple[int, int]) -> Strategy:
    """Build the strategy named in ``config["strategy"]``.

    Defaults to ``HeuristicStrategy`` so the core run never depends on the
    optional Q-learning path.
    """
    strategy_cfg = config.get("strategy", {"type": "heuristic"})
    stype = strategy_cfg.get("type", "heuristic")
    params = strategy_cfg.get("params", {})

    if stype == "heuristic":
        return HeuristicStrategy(grid_size, max_barriers=int(config.get("max_barriers", 5)))
    if stype == "qlearning":
        return QLearningStrategy(grid_size, **params)

    raise ValueError(f"Unknown strategy type: {stype!r}")
