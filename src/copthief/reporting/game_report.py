"""Internal JSON game report builder (issue #28).

The emitted JSON follows the assignment's §9.1 example **exactly** — the
grading system parses it automatically, so the spec keys (``group_name``,
``cop_mcp_url``, ``thief_mcp_url``, flat ``totals``) come first. Our richer
data (per-agent URLs and totals, human-readable team name) is appended as
*extra* keys, which JSON parsers ignore.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from copthief.services.scoring import ScoreBook, SubGameScore
from copthief.shared.config import Config


def report_metadata(config: Config) -> dict[str, Any]:
    """Build the report metadata block from the config's ``report`` section.

    Falls back to neutral placeholders when the section is absent (e.g. in
    minimal test configs) so the report schema stays complete.
    """
    report = config.report
    mcp = config.mcp
    return {
        "group_name": report.get("group_name", "Team-Local"),
        "team_name": report.get("team_name", ""),
        "students": list(report.get("students", [])),
        "github_repo": report.get("github_repo", ""),
        "agent_a_mcp_url": f"http://{mcp['host']}:{mcp['agent_a_port']}",
        "agent_b_mcp_url": f"http://{mcp['host']}:{mcp['agent_b_port']}",
        "timezone": report.get("timezone", "Asia/Jerusalem"),
    }


@dataclass(frozen=True, slots=True)
class GameReport:
    """Internal game report conforming to the assignment schema."""

    group_name: str
    students: list[Any]
    github_repo: str
    agent_a_mcp_url: str
    agent_b_mcp_url: str
    timezone: str
    sub_games: list[dict[str, Any]]
    totals: dict[str, int]
    totals_by_agent: dict[str, int]
    team_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a JSON-serializable dictionary.

        Agent-A opens as the cop (sub-games 1-3) and Agent-B as the thief, so
        the spec's role-fixed URL keys map to those agents' servers.
        """
        return {
            # --- assignment §9.1 schema (parsed by the grading system) ---
            "group_name": self.group_name,
            "students": self.students,
            "github_repo": self.github_repo,
            "cop_mcp_url": self.agent_a_mcp_url,
            "thief_mcp_url": self.agent_b_mcp_url,
            "timezone": self.timezone,
            "sub_games": self.sub_games,
            "totals": self.totals,
            # --- extras (role-swap detail; ignored by the parser) ---
            "team_name": self.team_name,
            "agent_a_mcp_url": self.agent_a_mcp_url,
            "agent_b_mcp_url": self.agent_b_mcp_url,
            "totals_by_agent": self.totals_by_agent,
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
        totals=dict(totals.by_role),
        totals_by_agent=dict(totals.by_agent),
        team_name=str(metadata.get("team_name", "")),
    )
