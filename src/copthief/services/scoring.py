"""Score book: per-sub-game points and running totals.

Points are read from the ``scoring`` config block so the same engine supports
any valid scoring table (PRD §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from copthief.constants import Outcome


@dataclass(frozen=True, slots=True)
class SubGameScore:
    """Points awarded for one finished sub-game."""

    cop_agent: str
    thief_agent: str
    outcome: Outcome
    cop_score: int
    thief_score: int


@dataclass(frozen=True, slots=True)
class Totals:
    """Aggregate points by role and by agent."""

    by_role: dict[str, int]
    by_agent: dict[str, int]


class ScoreBook:
    """Records outcomes and accumulates totals.

    ``cop_agent`` and ``thief_agent`` are expected to be ``"A"`` or ``"B"``.
    """

    def __init__(self, scoring_config: dict[str, int]):
        self._cfg = scoring_config
        self.sub_games: list[SubGameScore] = []
        self._by_role: dict[str, int] = {"cop": 0, "thief": 0}
        self._by_agent: dict[str, int] = {"agent_a": 0, "agent_b": 0}

    def record(self, cop_agent: str, thief_agent: str, outcome: Outcome) -> SubGameScore:
        """Award points for ``outcome`` and update running totals.

        Raises:
            ValueError: if ``outcome`` is not terminal.
        """
        if outcome == Outcome.COP_WIN:
            cop_score = self._cfg["cop_win"]
            thief_score = self._cfg["thief_loss"]
        elif outcome == Outcome.THIEF_WIN:
            cop_score = self._cfg["cop_loss"]
            thief_score = self._cfg["thief_win"]
        else:
            raise ValueError(f"Cannot score non-terminal outcome: {outcome.value}")

        entry = SubGameScore(cop_agent, thief_agent, outcome, cop_score, thief_score)
        self.sub_games.append(entry)

        self._by_role["cop"] += cop_score
        self._by_role["thief"] += thief_score
        self._by_agent[f"agent_{cop_agent.lower()}"] += cop_score
        self._by_agent[f"agent_{thief_agent.lower()}"] += thief_score

        return entry

    def totals(self) -> Totals:
        """Return a snapshot of current aggregate scores."""
        return Totals(self._by_role.copy(), self._by_agent.copy())
