"""Tests for game-engine terminal conditions: capture and timeout (issue #14)."""

from __future__ import annotations

import pytest

from copthief.constants import ActionType, Outcome, Role
from copthief.services.exceptions import IllegalMoveError
from copthief.services.game_engine import Action, GameEngine


def _move(d_row: int, d_col: int) -> Action:
    return Action(ActionType.MOVE, d_row, d_col)


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
