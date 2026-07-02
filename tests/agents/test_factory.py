"""Tests for the strategy factory (issue #37)."""

from __future__ import annotations

import pytest

from copthief.agents import HeuristicStrategy, QLearningStrategy, create_strategy


def test_factory_defaults_to_heuristic() -> None:
    strategy = create_strategy({}, grid_size=(5, 5))
    assert isinstance(strategy, HeuristicStrategy)


def test_factory_selects_qlearning() -> None:
    strategy = create_strategy(
        {"strategy": {"type": "qlearning", "params": {"alpha": 0.2, "seed": 7}}},
        grid_size=(5, 5),
    )
    assert isinstance(strategy, QLearningStrategy)
    assert strategy.alpha == 0.2


def test_factory_rejects_unknown_strategy() -> None:
    with pytest.raises(ValueError, match="Unknown strategy type"):
        create_strategy({"strategy": {"type": "magic"}}, grid_size=(5, 5))
