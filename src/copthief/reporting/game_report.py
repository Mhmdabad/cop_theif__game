"""Internal JSON game report builder (issue #28).

Assembles the report schema from PLAN §4.3. The body is JSON only, with
per-sub-game results and aggregate totals by role and by agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from copthief.services.scoring import ScoreBook, SubGameScore


@dataclass(frozen=True, slots=True)
class GameReport:
    """Internal game report conforming to the assignment schema."""

    group_name: str
    students: list[str]
    github_repo: str
    agent_a_mcp_url: str
    agent_b_mcp_url: str
    timezone: str
    sub_games: list[dict[str, Any]]
    totals: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a JSON-serializable dictionary."""
        return {
            "group_name": self.group_name,
            "students": self.students,
            "github_repo": self.github_repo,
            "agent_a_mcp_url": self.agent_a_mcp_url,
            "agent_b_mcp_url": self.agent_b_mcp_url,
            "timezone": self.timezone,
            "sub_games": self.sub_games,
            "totals": self.totals,
        }


def build_report(
    metadata: dict[str, Any],
    sub_game_entries: list[SubGameScore],
    moves_per_game: list[int],
    scorebook: ScoreBook,
) -> GameReport:
    """Assemble a ``GameReport`` from scoring records and metadata.

    ``metadata`` must contain at least ``group_name``, ``students``,
    ``github_repo``, ``agent_a_mcp_url``, ``agent_b_mcp_url``, and ``timezone``.
    """
    sub_games = [
        {
            "index": i + 1,
            "cop_agent": entry.cop_agent,
            "thief_agent": entry.thief_agent,
            "winner": entry.outcome.value,
            "moves": moves_per_game[i],
            "cop_score": entry.cop_score,
            "thief_score": entry.thief_score,
        }
        for i, entry in enumerate(sub_game_entries)
    ]
    totals = scorebook.totals()
    return GameReport(
        group_name=metadata["group_name"],
        students=list(metadata["students"]),
        github_repo=metadata["github_repo"],
        agent_a_mcp_url=metadata["agent_a_mcp_url"],
        agent_b_mcp_url=metadata["agent_b_mcp_url"],
        timezone=metadata["timezone"],
        sub_games=sub_games,
        totals={"by_role": totals.by_role, "by_agent": totals.by_agent},
    )
