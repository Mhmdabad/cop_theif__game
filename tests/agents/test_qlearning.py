"""Tests for tabular Q-Learning strategy (issue #35)."""

from __future__ import annotations

from copthief.agents.qlearning import QLearningStrategy
from copthief.constants import ActionType, Role
from copthief.services.dialogue import Observation


def _observation(my_pos: tuple[int, int]) -> Observation:
    return Observation(
        role=Role.COP,
        my_position=my_pos,
        opponent_position=None,
        barriers=set(),
        last_message="",
        move_number=0,
    )


def test_q_table_initialised_to_zeros() -> None:
    strategy = QLearningStrategy(grid_size=(5, 5))
    assert len(strategy.q) == 25
    assert all(len(row) == 4 for row in strategy.q)
    assert all(value == 0.0 for row in strategy.q for value in row)


def test_choose_action_respects_grid_bounds() -> None:
    strategy = QLearningStrategy(grid_size=(3, 3), epsilon=0.0)

    action = strategy.choose_action(_observation((0, 0)), "")
    assert action.type == ActionType.MOVE
    assert (
        (action.d_row, action.d_col) in {(-1, 0), (0, -1)}
        or (action.d_row, action.d_col) == (1, 0)
        or (action.d_row, action.d_col) == (0, 1)
    )
    new_row, new_col = action.d_row, action.d_col
    assert 0 <= new_row < 3 and 0 <= new_col < 3


def test_bellman_update_changes_q_value() -> None:
    strategy = QLearningStrategy(grid_size=(5, 5), alpha=0.5, gamma=0.9)
    state_before = strategy.q[0][0]

    strategy.update((0, 0), 0, reward=1.0, next_position=(1, 0))

    assert strategy.q[0][0] != state_before
    assert strategy.q[0][0] == 0.5


def test_seeded_selection_is_deterministic() -> None:
    strategy = QLearningStrategy(grid_size=(5, 5), epsilon=0.3, seed=42)

    actions = [strategy.choose_action(_observation((2, 2)), "") for _ in range(20)]

    strategy2 = QLearningStrategy(grid_size=(5, 5), epsilon=0.3, seed=42)
    actions2 = [strategy2.choose_action(_observation((2, 2)), "") for _ in range(20)]

    assert actions == actions2
