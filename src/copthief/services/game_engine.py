"""Game engine: grid state machine with 8-directional movement and barriers.

The engine owns the authoritative ground-truth board state. Every proposed
action is validated and either applied (mutating state) or rejected with an
``IllegalMoveError``. This module is free of LLM/MCP/network concerns so it is
fully deterministic and unit-testable (PRD_game_engine.md §1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copthief.constants import MOVE_VECTORS, ActionType, Outcome, Role
from copthief.services.barriers import BarrierManager
from copthief.services.exceptions import IllegalMoveError


@dataclass
class GridState:
    """Mutable ground-truth state of one sub-game."""

    cop_pos: tuple[int, int]
    thief_pos: tuple[int, int]
    barriers: set[tuple[int, int]] = field(default_factory=set)
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
    Validates: bounds, single-cell step, barrier quota/asymmetry,
                correct agent's turn.
    Terminates: Cop win on exact capture; Thief win when ``max_moves``
                elapse without capture.
    """

    def __init__(
        self,
        grid_size: tuple[int, int],
        max_moves: int,
        max_barriers: int = 5,
    ):
        self.grid_size = grid_size
        self.max_moves = max_moves
        self.barrier_manager = BarrierManager(max_barriers)
        self.state = self._initial_state()

    def _initial_state(self) -> GridState:
        rows, cols = self.grid_size
        return GridState(
            cop_pos=(0, 0),
            thief_pos=(rows - 1, cols - 1),
            barriers=self.barrier_manager.barriers,
        )

    def reset(self) -> None:
        """Return the engine to the starting position for a new sub-game."""
        self.barrier_manager.clear()
        self.state = self._initial_state()

    def apply_action(self, role: Role, action: Action) -> Outcome:
        """Validate and apply ``role``'s ``action`` to the current state.

        Raises:
            IllegalMoveError: if the game is over, wrong turn, illegal vector,
                out-of-bounds destination, barrier quota exhausted, or the
                Thief attempts to place a barrier.
        """
        state = self.state
        if state.outcome != Outcome.ONGOING:
            raise IllegalMoveError("Game already concluded")
        if state.turn != role:
            raise IllegalMoveError(f"Expected {state.turn.value} turn, got {role.value}")

        if action.type == ActionType.MOVE:
            return self._apply_move(role, action)
        if action.type == ActionType.PLACE_BARRIER:
            return self._apply_barrier(role)

        raise IllegalMoveError(f"Unsupported action type: {action.type!r}")

    def _apply_move(self, role: Role, action: Action) -> Outcome:
        if (action.d_row, action.d_col) not in MOVE_VECTORS:
            raise IllegalMoveError(
                f"Invalid move vector ({action.d_row}, {action.d_col})"
            )

        state = self.state
        current = state.cop_pos if role == Role.COP else state.thief_pos
        new_pos = (current[0] + action.d_row, current[1] + action.d_col)
        if not self._in_bounds(new_pos):
            raise IllegalMoveError(f"Move out of bounds: {new_pos}")
        if not self.barrier_manager.passable(role, new_pos):
            raise IllegalMoveError(f"{role.value} cannot enter barrier cell: {new_pos}")

        if role == Role.COP:
            state.cop_pos = new_pos
            if state.cop_pos == state.thief_pos:
                state.outcome = Outcome.COP_WIN
        else:
            state.thief_pos = new_pos

        self._advance_turn()
        return state.outcome

    def _apply_barrier(self, role: Role) -> Outcome:
        if role != Role.COP:
            raise IllegalMoveError("Only the cop can place barriers")

        self.barrier_manager.place(self.state.cop_pos)
        self._advance_turn()
        return self.state.outcome

    def _advance_turn(self) -> None:
        state = self.state
        state.move_number += 1
        if state.outcome == Outcome.ONGOING and state.move_number >= self.max_moves:
            state.outcome = Outcome.THIEF_WIN
        state.turn = Role.COP if state.turn == Role.THIEF else Role.THIEF

    def _in_bounds(self, pos: tuple[int, int]) -> bool:
        rows, cols = self.grid_size
        return 0 <= pos[0] < rows and 0 <= pos[1] < cols
