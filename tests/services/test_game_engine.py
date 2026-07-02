"""Tests for game-engine happy path + edges (issues #14 and #16)."""

from __future__ import annotations

import pytest

from copthief.constants import ActionType, Outcome, Role
from copthief.services.exceptions import IllegalMoveError
from copthief.services.game_engine import Action, GameEngine


def _move(d_row: int, d_col: int) -> Action:
    return Action(ActionType.MOVE, d_row, d_col)


def _barrier() -> Action:
    return Action(ActionType.PLACE_BARRIER)


def test_cop_captures_thief_on_exact_cell() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    # Place cop and thief adjacent.
    engine.state.cop_pos = (1, 1)
    engine.state.thief_pos = (1, 2)
    engine.state.turn = Role.COP

    outcome = engine.apply_action(Role.COP, _move(0, 1))

    assert outcome == Outcome.COP_WIN
    assert engine.state.outcome == Outcome.COP_WIN


def test_no_capture_keeps_game_ongoing() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.cop_pos = (0, 0)
    engine.state.thief_pos = (2, 2)
    engine.state.turn = Role.COP

    outcome = engine.apply_action(Role.COP, _move(1, 0))

    assert outcome == Outcome.ONGOING
    assert engine.state.outcome == Outcome.ONGOING


def test_moves_after_capture_are_rejected() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.cop_pos = (0, 0)
    engine.state.thief_pos = (0, 1)
    engine.state.turn = Role.COP
    engine.apply_action(Role.COP, _move(0, 1))

    with pytest.raises(IllegalMoveError, match="concluded"):
        engine.apply_action(Role.THIEF, _move(1, 0))


def test_timeout_after_max_moves() -> None:
    engine = GameEngine(grid_size=(5, 5), max_moves=4)
    # Burn through moves without capture.
    engine.apply_action(Role.THIEF, _move(0, -1))
    engine.apply_action(Role.COP, _move(0, 1))
    engine.apply_action(Role.THIEF, _move(0, 1))
    outcome = engine.apply_action(Role.COP, _move(0, -1))

    assert outcome == Outcome.THIEF_WIN
    assert engine.state.move_number == 4


def test_capture_on_final_move_beats_timeout() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=2)
    engine.state.cop_pos = (0, 0)
    engine.state.thief_pos = (0, 2)
    engine.state.turn = Role.THIEF
    # Thief steps toward cop; cop captures on the final allowed move.
    engine.apply_action(Role.THIEF, _move(0, -1))
    outcome = engine.apply_action(Role.COP, _move(0, 1))

    assert outcome == Outcome.COP_WIN
    assert engine.state.move_number == 2


def test_reset_clears_state_and_barriers() -> None:
    engine = GameEngine(grid_size=(5, 5), max_moves=25)
    engine.apply_action(Role.THIEF, _move(-1, 0))
    engine.apply_action(Role.COP, _barrier())
    engine.state.cop_pos = (2, 2)

    engine.reset()

    assert engine.state.cop_pos == (0, 0)
    assert engine.state.thief_pos == (4, 4)
    assert engine.state.move_number == 0
    assert engine.state.turn == Role.THIEF
    assert engine.state.outcome == Outcome.ONGOING
    assert engine.state.barriers == set()


def test_wrong_turn_rejected() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    with pytest.raises(IllegalMoveError, match="Expected thief turn"):
        engine.apply_action(Role.COP, _move(1, 0))


def test_invalid_move_vector_rejected() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    with pytest.raises(IllegalMoveError, match="Invalid move vector"):
        engine.apply_action(Role.THIEF, _move(2, 0))


def test_out_of_bounds_move_rejected() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.cop_pos = (0, 0)
    engine.state.turn = Role.COP
    with pytest.raises(IllegalMoveError, match="out of bounds"):
        engine.apply_action(Role.COP, _move(-1, 0))


def test_thief_blocked_by_barrier() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.cop_pos = (1, 1)
    engine.state.thief_pos = (2, 1)
    engine.state.turn = Role.COP
    engine.apply_action(Role.COP, _barrier())
    engine.state.turn = Role.THIEF

    with pytest.raises(IllegalMoveError, match="cannot enter barrier"):
        engine.apply_action(Role.THIEF, _move(-1, 0))


def test_cop_passes_through_barrier() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.cop_pos = (0, 0)
    engine.state.turn = Role.COP
    engine.apply_action(Role.COP, _barrier())

    # Cop can move out of and back into its own barrier.
    engine.state.turn = Role.COP
    engine.apply_action(Role.COP, _move(1, 0))
    engine.state.turn = Role.COP
    outcome = engine.apply_action(Role.COP, _move(-1, 0))

    assert engine.state.cop_pos == (0, 0)
    assert outcome == Outcome.ONGOING


def test_thief_cannot_place_barrier() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.turn = Role.THIEF
    with pytest.raises(IllegalMoveError, match="Only the cop"):
        engine.apply_action(Role.THIEF, _barrier())


def test_unsupported_action_type_rejected() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)

    class FakeAction:
        type = "teleport"

    with pytest.raises(IllegalMoveError, match="Unsupported action type"):
        engine.apply_action(Role.THIEF, FakeAction())  # type: ignore[arg-type]



def test_cop_barrier_quota_enforced() -> None:
    engine = GameEngine(grid_size=(5, 5), max_moves=25, max_barriers=1)
    engine.state.turn = Role.COP
    engine.apply_action(Role.COP, _barrier())
    engine.state.turn = Role.COP
    with pytest.raises(IllegalMoveError, match="quota"):
        engine.apply_action(Role.COP, _barrier())


def test_corner_and_edge_moves() -> None:
    engine = GameEngine(grid_size=(3, 3), max_moves=25)
    engine.state.thief_pos = (0, 0)
    engine.state.turn = Role.THIEF
    engine.apply_action(Role.THIEF, _move(1, 1))
    assert engine.state.thief_pos == (1, 1)

    engine.state.turn = Role.THIEF
    engine.apply_action(Role.THIEF, _move(-1, 0))
    assert engine.state.thief_pos == (0, 1)

    engine.state.turn = Role.THIEF
    engine.apply_action(Role.THIEF, _move(0, -1))
    assert engine.state.thief_pos == (0, 0)
