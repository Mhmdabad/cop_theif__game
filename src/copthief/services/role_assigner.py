"""Role assignment for the local 3/3 swap (issue #24).

The orchestrator owns role assignment so the two agent server instances can
remain symmetric (PLAN ADR-8).
"""

from __future__ import annotations


class RoleAssigner:
    """Maps sub-game index to the cop/thief role held by each agent."""

    def __init__(self, swap_at_subgame: int = 4):
        self.swap_at_subgame = swap_at_subgame

    def roles_for(self, sub_game_index: int) -> dict[str, str]:
        """Return ``{"A": role, "B": role}`` for the given 1-based index."""
        if sub_game_index < self.swap_at_subgame:
            return {"A": "cop", "B": "thief"}
        return {"A": "thief", "B": "cop"}
