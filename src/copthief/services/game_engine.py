"""Game engine: grid state machine with 8-directional movement.

The engine owns the authoritative ground-truth board state. Every proposed
action is validated and either applied (mutating state) or rejected with an
``IllegalMoveError``. This module is free of LLM/MCP/network concerns so it is
fully deterministic and unit-testable (PRD_game_engine.md §1).
"""

from __future__ import annotations

from dataclasses import dataclass

from copthief.constants import MOVE_VECTORS, ActionType, Outcome, Role


class IllegalMoveError(ValueError):
    """Raised when a proposed action violates the game rules."""


@dataclass
class GridState:
    """Mutable ground-truth state of one sub-game."""

    cop_pos: tuple[int, int]
    thief_pos: tuple[int, int]
    turn: Role = Role.THIEF
    move_number: int = 0
    outcome: Outcome = Outcome.ONGOING


@dataclass(frozen=True, slots=True)
class Action:
    """A single agent intent: move one cell or place a barrier."""

    type: ActionType
    d_row: int = 0
    d_col: int = 0


class GameEngine:
    """State machine for a single sub-game.

    Input:  ``Action`` + current ``GridState``
    Output: new ``GridState`` + ``Outcome`` flag
    Validates: bounds, single-cell step, correct agent's turn.
    """

    def __init__(self, grid_size: tuple[int, int], max_moves: int):
        self.grid_size = grid_size
        self.max_moves = max_moves
        self.state = self._initial_state()

    def _initial_state(self) -> GridState:
        rows, cols = self.grid_size
        return GridState(cop_pos=(0, 0), thief_pos=(rows - 1, cols - 1))

    def reset(self) -> None:
        """Return the engine to the starting position for a new sub-game."""
        self.state = self._initial_state()

    def apply_action(self, role: Role, action: Action) -> Outcome:
        """Validate and apply ``role``'s ``action`` to the current state.

        Raises:
            IllegalMoveError: if the game is over, wrong turn, illegal vector,
                out-of-bounds destination, or barrier action is attempted.
        """
        state = self.state
        if state.outcome != Outcome.ONGOING:
            raise IllegalMoveError("Game already concluded")
        if state.turn != role:
            raise IllegalMoveError(f"Expected {state.turn.value} turn, got {role.value}")

        if action.type == ActionType.MOVE:
            return self._apply_move(role, action)

        raise IllegalMoveError(f"Unsupported action type: {action.type.value}")

    def _apply_move(self, role: Role, action: Action) -> Outcome:
        state = self.state
        if (action.d_row, action.d_col) not in MOVE_VECTORS:
            raise IllegalMoveError(
                f"Invalid move vector ({action.d_row}, {action.d_col})"
            )

        current = state.cop_pos if role == Role.COP else state.thief_pos
        new_pos = (current[0] + action.d_row, current[1] + action.d_col)
        if not self._in_bounds(new_pos):
            raise IllegalMoveError(f"Move out of bounds: {new_pos}")

        if role == Role.COP:
            state.cop_pos = new_pos
        else:
            state.thief_pos = new_pos

        state.move_number += 1
        state.turn = Role.COP if role == Role.THIEF else Role.THIEF
        return state.outcome

    def _in_bounds(self, pos: tuple[int, int]) -> bool:
        rows, cols = self.grid_size
        return 0 <= pos[0] < rows and 0 <= pos[1] < cols
