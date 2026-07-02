"""Tests for the heuristic strategy (issue #34)."""

from __future__ import annotations

import pytest

from copthief.agents.heuristic import HeuristicStrategy
from copthief.constants import ActionType, Role
from copthief.services.dialogue import Observation


def _observation(
    role: Role,
    my_pos: tuple[int, int],
    opponent_pos: tuple[int, int] | None,
) -> Observation:
    return Observation(
        role=role,
        my_position=my_pos,
        opponent_position=opponent_pos,
        barriers=set(),
        last_message="",
        move_number=0,
    )


def test_cop_moves_toward_visible_thief() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5))
    action = strategy.choose_action(_observation(Role.COP, my_pos=(0, 0), opponent_pos=(2, 2)), "")

    assert action.type == ActionType.MOVE
    assert action.d_row in {-1, 0, 1}
    assert action.d_col in {-1, 0, 1}


def test_thief_moves_away_from_visible_cop() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5))
    action = strategy.choose_action(
        _observation(Role.THIEF, my_pos=(2, 2), opponent_pos=(0, 0)), ""
    )

    assert action.type == ActionType.MOVE
    assert (action.d_row, action.d_col) != (0, 0)


def test_thief_never_places_barrier() -> None:
    strategy = HeuristicStrategy(grid_size=(2, 2))
    action = strategy.choose_action(_observation(Role.THIEF, my_pos=(0, 0), opponent_pos=None), "")

    assert action.type == ActionType.MOVE


def test_cop_places_barrier_when_no_legal_move() -> None:
    # 1x1 board has no legal moves.
    strategy = HeuristicStrategy(grid_size=(1, 1))
    action = strategy.choose_action(_observation(Role.COP, my_pos=(0, 0), opponent_pos=None), "")

    assert action.type == ActionType.PLACE_BARRIER


@pytest.mark.parametrize("grid_size", [(2, 2), (3, 3), (5, 5)])
def test_action_is_always_legal(grid_size: tuple[int, int]) -> None:
    strategy = HeuristicStrategy(grid_size)
    rows, cols = grid_size

    for row in range(rows):
        for col in range(cols):
            for role in (Role.COP, Role.THIEF):
                action = strategy.choose_action(
                    _observation(role, my_pos=(row, col), opponent_pos=None), ""
                )
                if action.type == ActionType.MOVE:
                    new_row, new_col = row + action.d_row, col + action.d_col
                    assert 0 <= new_row < rows
                    assert 0 <= new_col < cols
