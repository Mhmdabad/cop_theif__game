"""Tests for the upgraded heuristic: 8-dir movement, barrier use, avoidance."""

from __future__ import annotations

from copthief.agents.heuristic import HeuristicStrategy
from copthief.constants import ActionType, Role
from copthief.services.dialogue import Observation


def _observation(
    role: Role,
    my_pos: tuple[int, int],
    opponent_pos: tuple[int, int] | None,
    barriers: set[tuple[int, int]] | None = None,
    move_number: int = 0,
) -> Observation:
    return Observation(
        role=role,
        my_position=my_pos,
        opponent_position=opponent_pos,
        barriers=barriers or set(),
        last_message="",
        move_number=move_number,
    )


def test_cop_chases_diagonally() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5))
    action = strategy.choose_action(_observation(Role.COP, (0, 0), (2, 2)), "")
    assert action.type == ActionType.MOVE
    assert (action.d_row, action.d_col) == (1, 1)


def test_cop_plants_barrier_when_blind_on_alternating_turn() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5), max_barriers=5)
    action = strategy.choose_action(_observation(Role.COP, (2, 2), None, move_number=1), "")
    assert action.type == ActionType.PLACE_BARRIER


def test_cop_moves_when_blind_but_quota_exhausted() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5), max_barriers=1)
    barriers = {(1, 1)}
    action = strategy.choose_action(
        _observation(Role.COP, (2, 2), None, barriers=barriers, move_number=1), ""
    )
    assert action.type == ActionType.MOVE


def test_cop_moves_when_thief_visible_even_on_barrier_turn() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5))
    action = strategy.choose_action(_observation(Role.COP, (2, 2), (4, 4), move_number=1), "")
    assert action.type == ActionType.MOVE


def test_thief_avoids_barrier_cells() -> None:
    strategy = HeuristicStrategy(grid_size=(3, 3))
    # Fleeing from (0,0), the thief's best distance-maximising cell (2,2) is
    # barriered; it must pick a legal alternative, never the barrier.
    barriers = {(2, 2)}
    action = strategy.choose_action(_observation(Role.THIEF, (1, 1), (0, 0), barriers=barriers), "")
    assert action.type == ActionType.MOVE
    assert (1 + action.d_row, 1 + action.d_col) != (2, 2)


def test_thief_uses_diagonal_escape() -> None:
    strategy = HeuristicStrategy(grid_size=(5, 5))
    action = strategy.choose_action(_observation(Role.THIEF, (2, 2), (0, 0)), "")
    assert (action.d_row, action.d_col) == (1, 1)
