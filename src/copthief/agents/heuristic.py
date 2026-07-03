"""Default heuristic strategy: 8-directional pursuit/evasion (issue #34).

The cop minimises Chebyshev distance to the thief (diagonals included, so an
equal-speed pursuit can actually corner an evader); the thief maximises it and
never steps onto a barrier. While the thief is out of sight the cop seals its
patrol route by placing barriers on alternating turns, exercising the barrier
mechanic without stalling the chase.
"""

from __future__ import annotations

from copthief.agents.strategy import Strategy
from copthief.constants import MOVE_VECTORS, ActionType, Role
from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action


class HeuristicStrategy(Strategy):
    """Deterministic distance-based strategy over all 8 move directions."""

    def __init__(self, grid_size: tuple[int, int], max_barriers: int = 5) -> None:
        self.grid_size = grid_size
        self.max_barriers = max_barriers

    def choose_action(self, observation: Observation, last_message: str) -> Action:
        """Pick a legal action that improves the agent's objective."""
        role = observation.role
        my_pos = observation.my_position
        target = observation.opponent_position

        if role == Role.COP and target is None and self._should_place_barrier(observation):
            return Action(ActionType.PLACE_BARRIER)

        if target is None:
            target = self._default_target(role)

        candidates = self._legal_moves(role, my_pos, observation.barriers)
        if not candidates:
            if role == Role.COP:
                return Action(ActionType.PLACE_BARRIER)
            # A barrier-locked thief has no legal action; surface the least-bad
            # move and let the engine adjudicate.
            return Action(ActionType.MOVE, *MOVE_VECTORS[0])

        if role == Role.COP:
            chase = self._intercept_point(my_pos, target)
            _score, move = min(
                (self._chebyshev((my_pos[0] + d_row, my_pos[1] + d_col), chase), (d_row, d_col))
                for d_row, d_col in candidates
            )
        else:
            _score, move = max(
                (self._flee_score((my_pos[0] + d_row, my_pos[1] + d_col), target), (d_row, d_col))
                for d_row, d_col in candidates
            )

        return Action(ActionType.MOVE, *move)

    def _flee_score(self, pos: tuple[int, int], cop: tuple[int, int]) -> int:
        """Distance-maximising score with an edge penalty.

        Pure distance-greedy flight runs the thief into a corner where the cop
        traps it. The edge penalty (at most 2) is smaller than one distance
        step (3), so it only breaks ties between equally-distant cells — the
        thief still flees at full speed but prefers open board over corners.
        """
        rows, cols = self.grid_size
        edge_penalty = int(pos[0] in (0, rows - 1)) + int(pos[1] in (0, cols - 1))
        return 3 * self._chebyshev(pos, cop) - edge_penalty

    def _intercept_point(self, my_pos: tuple[int, int], thief: tuple[int, int]) -> tuple[int, int]:
        """Aim one cell ahead of the thief's flee direction (cut the circle).

        A pure distance-minimising chase never catches an equal-speed evader
        that circles the open board; leading the target closes the loop. When
        already adjacent, aim at the thief itself to take the capture.
        """
        if self._chebyshev(my_pos, thief) <= 1:
            return thief
        rows, cols = self.grid_size
        flee_row = (thief[0] > my_pos[0]) - (thief[0] < my_pos[0])
        flee_col = (thief[1] > my_pos[1]) - (thief[1] < my_pos[1])
        return (
            min(max(thief[0] + flee_row, 0), rows - 1),
            min(max(thief[1] + flee_col, 0), cols - 1),
        )

    def _should_place_barrier(self, observation: Observation) -> bool:
        """Seal the current cell on alternating blind turns while quota lasts."""
        return (
            len(observation.barriers) < self.max_barriers
            and observation.my_position not in observation.barriers
            and observation.move_number % 4 == 1
        )

    def _legal_moves(
        self,
        role: Role,
        pos: tuple[int, int],
        barriers: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """In-bounds one-step vectors; the thief additionally avoids barriers."""
        rows, cols = self.grid_size
        moves = []
        for d_row, d_col in MOVE_VECTORS:
            new_pos = (pos[0] + d_row, pos[1] + d_col)
            if not (0 <= new_pos[0] < rows and 0 <= new_pos[1] < cols):
                continue
            if role == Role.THIEF and new_pos in barriers:
                continue
            moves.append((d_row, d_col))
        return moves

    @staticmethod
    def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def _default_target(self, role: Role) -> tuple[int, int]:
        """Search/safety target when the opponent is not visible."""
        rows, cols = self.grid_size
        centre = (rows // 2, cols // 2)
        if role == Role.COP:
            return centre
        # Thief: head to the corner farthest from the centre.
        corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
        return max(corners, key=lambda corner: self._chebyshev(corner, centre))
