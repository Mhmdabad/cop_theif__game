"""Tests for internal JSON game report builder (issue #28)."""

from __future__ import annotations

from copthief.constants import Outcome
from copthief.reporting.game_report import GameReport, build_report
from copthief.services.scoring import ScoreBook


def _metadata() -> dict[str, object]:
    return {
        "group_name": "s82kma9e",
        "team_name": "Team-X",
        "students": ["A", "B"],
        "github_repo": "https://github.com/test/repo",
        "agent_a_mcp_url": "http://127.0.0.1:8101",
        "agent_b_mcp_url": "http://127.0.0.1:8102",
        "timezone": "UTC",
    }


def test_build_report_matches_assignment_schema() -> None:
    scorebook = ScoreBook({"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5})
    scorebook.record("A", "B", Outcome.COP_WIN)

    report = build_report(_metadata(), scorebook.sub_games, [12], scorebook)
    data = report.to_dict()

    # Spec-exact keys (assignment §9.1) — parsed by the grading system.
    assert data["group_name"] == "s82kma9e"
    assert data["cop_mcp_url"] == "http://127.0.0.1:8101"
    assert data["thief_mcp_url"] == "http://127.0.0.1:8102"
    assert data["totals"] == {"cop": 20, "thief": 5}
    assert data["sub_games"] == [
        {
            "index": 1,
            "cop_agent": "A",
            "thief_agent": "B",
            "winner": "cop_win",
            "moves": 12,
            "cop_score": 20,
            "thief_score": 5,
        }
    ]

    # Extras preserved for the role-swap detail.
    assert data["team_name"] == "Team-X"
    assert data["agent_a_mcp_url"] == "http://127.0.0.1:8101"
    assert data["totals_by_agent"] == {"agent_a": 20, "agent_b": 5}


def test_spec_keys_order_first() -> None:
    scorebook = ScoreBook({"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5})
    scorebook.record("A", "B", Outcome.THIEF_WIN)
    data = build_report(_metadata(), scorebook.sub_games, [25], scorebook).to_dict()

    spec_keys = [
        "group_name",
        "students",
        "github_repo",
        "cop_mcp_url",
        "thief_mcp_url",
        "timezone",
        "sub_games",
        "totals",
    ]
    assert list(data)[: len(spec_keys)] == spec_keys


def test_game_report_is_json_serializable() -> None:
    import json

    report = GameReport(
        group_name="G",
        students=["S"],
        github_repo="https://example.com",
        agent_a_mcp_url="http://a",
        agent_b_mcp_url="http://b",
        timezone="UTC",
        sub_games=[],
        totals={"cop": 0, "thief": 0},
        totals_by_agent={"agent_a": 0, "agent_b": 0},
        team_name="T",
    )
    json.dumps(report.to_dict())
