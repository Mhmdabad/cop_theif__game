"""Default heuristic strategy based on Manhattan distance (issue #34).

The cop tries to minimise distance to the thief; the thief tries to maximise
it. The strategy is role-aware: only the cop may place a barrier, and only
when no legal move is available.
"""

from __future__ import annotations

from copthief.agents.strategy import Strategy
from copthief.constants import ORTHOGONAL_MOVES, ActionType, Role
from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action


class HeuristicStrategy(Strategy):
    """Deterministic Manhattan-distance strategy."""

    def __init__(self, grid_size: tuple[int, int]) -> None:
        self.grid_size = grid_size

    def choose_action(self, observation: Observation, last_message: str) -> Action:
        """Pick a legal move that improves the agent's objective."""
        role = observation.role
        my_pos = observation.my_position
        target = observation.opponent_position

        if target is None:
            target = self._default_target(role)

        candidates = self._legal_moves(my_pos)
        if not candidates:
            if role == Role.COP:
                return Action(ActionType.PLACE_BARRIER)
            # On any real board there is always at least one orthogonal move.
            return Action(ActionType.MOVE, *ORTHOGONAL_MOVES[0])

        if role == Role.COP:
            _score, move = min(
                (self._manhattan((my_pos[0] + d_row, my_pos[1] + d_col), target), (d_row, d_col))
                for d_row, d_col in candidates
            )
        else:
            _score, move = max(
                (self._manhattan((my_pos[0] + d_row, my_pos[1] + d_col), target), (d_row, d_col))
                for d_row, d_col in candidates
            )

        return Action(ActionType.MOVE, *move)

    def _legal_moves(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        rows, cols = self.grid_size
        return [
            (d_row, d_col)
            for d_row, d_col in ORTHOGONAL_MOVES
            if 0 <= pos[0] + d_row < rows and 0 <= pos[1] + d_col < cols
        ]

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _default_target(self, role: Role) -> tuple[int, int]:
        """Search/safety target when the opponent is not visible."""
        rows, cols = self.grid_size
        centre = (rows // 2, cols // 2)
        if role == Role.COP:
            return centre
        # Thief: head to the nearest corner, away from the centre.
        corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
        return max(corners, key=lambda corner: self._manhattan(corner, centre))
