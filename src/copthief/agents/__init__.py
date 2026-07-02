"""copthief.agents — move-selection strategies (heuristic, optional Q-learning)."""

from copthief import __version__ as __version__
from copthief.agents.heuristic import HeuristicStrategy
from copthief.agents.strategy import Strategy

__all__ = ["__version__", "HeuristicStrategy", "Strategy"]
