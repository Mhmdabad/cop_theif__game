"""Barrier placement and asymmetric passability rules.

Barriers are placed by the Cop on its current cell. They are impassable to the
Thief but remain passable to the Cop, creating the asymmetry required by the
rules (PRD §3.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copthief.constants import Role
from copthief.services.exceptions import IllegalMoveError


@dataclass
class BarrierManager:
    """Owns the mutable barrier set for one sub-game."""

    max_barriers: int
    barriers: set[tuple[int, int]] = field(default_factory=set)

    def place(self, pos: tuple[int, int]) -> None:
        """Place a barrier on ``pos`` if quota allows.

        Raises:
            IllegalMoveError: if the quota is exhausted or a barrier already
                exists at ``pos``.
        """
        if len(self.barriers) >= self.max_barriers:
            raise IllegalMoveError("Barrier quota exhausted")
        if pos in self.barriers:
            raise IllegalMoveError(f"Barrier already exists at {pos}")
        self.barriers.add(pos)

    def passable(self, role: Role, pos: tuple[int, int]) -> bool:
        """Return ``True`` if ``role`` may occupy ``pos``.

        Barriers block the Thief but not the Cop.
        """
        return pos not in self.barriers or role == Role.COP

    def clear(self) -> None:
        """Remove all barriers (used when resetting the sub-game)."""
        self.barriers.clear()
