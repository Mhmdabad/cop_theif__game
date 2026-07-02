"""Tests for game constants and enums (issue #11)."""

from __future__ import annotations

from copthief.constants import (
    DIAGONAL_MOVES,
    MOVE_VECTORS,
    ORTHOGONAL_MOVES,
    ActionType,
    Outcome,
    Role,
)


def test_move_vectors_are_eight_unique_units() -> None:
    assert len(MOVE_VECTORS) == 8
    assert len(set(MOVE_VECTORS)) == 8
    assert set(MOVE_VECTORS) == set(ORTHOGONAL_MOVES) | set(DIAGONAL_MOVES)
    for d_row, d_col in MOVE_VECTORS:
        assert (d_row, d_col) != (0, 0)
        assert -1 <= d_row <= 1
        assert -1 <= d_col <= 1


def test_orthogonal_and_diagonal_split() -> None:
    assert len(ORTHOGONAL_MOVES) == 4
    assert len(DIAGONAL_MOVES) == 4
    assert all(0 in v for v in ORTHOGONAL_MOVES)
    assert all(0 not in v for v in DIAGONAL_MOVES)


def test_enum_values() -> None:
    assert Role.COP.value == "cop"
    assert Role.THIEF.value == "thief"
    assert Outcome.ONGOING.value == "ongoing"
    assert Outcome.COP_WIN.value == "cop_win"
    assert Outcome.THIEF_WIN.value == "thief_win"
    assert ActionType.MOVE.value == "move"
    assert ActionType.PLACE_BARRIER.value == "place_barrier"
