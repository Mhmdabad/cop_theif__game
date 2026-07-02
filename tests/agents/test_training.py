"""Tests for the Q-Learning training routine (issue #36)."""

from __future__ import annotations

from copthief.agents.training import train_cop_q_learning


def test_training_produces_history_of_right_length() -> None:
    strategy, history = train_cop_q_learning(
        grid_size=(3, 3), thief_pos=(2, 2), episodes=20, seed=1
    )

    assert len(history) == 20
    assert all(isinstance(value, float) for value in history)
    assert strategy.grid_size == (3, 3)


def test_trained_strategy_chooses_legal_actions() -> None:
    strategy, _history = train_cop_q_learning(
        grid_size=(3, 3), thief_pos=(2, 2), episodes=50, seed=2
    )

    for row in range(3):
        for col in range(3):
            q_values = strategy.q[row * 3 + col]
            assert len(q_values) == 4
