"""Immutable game constants: movement vectors, roles, outcomes, action types.

Kept free of behavior so every other module shares one definition of the rules'
vocabulary (guidelines §7.2 — constants live here, not as scattered literals).
"""

from __future__ import annotations

from enum import Enum

# 8-directional movement as (d_row, d_col) unit vectors: orthogonal + diagonal.
ORTHOGONAL_MOVES: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL_MOVES: tuple[tuple[int, int], ...] = ((-1, -1), (-1, 1), (1, -1), (1, 1))
MOVE_VECTORS: tuple[tuple[int, int], ...] = ORTHOGONAL_MOVES + DIAGONAL_MOVES


class Role(str, Enum):
    """The role an agent plays in a sub-game."""

    COP = "cop"
    THIEF = "thief"


class Outcome(str, Enum):
    """Terminal status of a sub-game."""

    ONGOING = "ongoing"
    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"


class ActionType(str, Enum):
    """The kind of action an agent takes on its turn."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"
