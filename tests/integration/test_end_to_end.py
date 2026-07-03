"""End-to-end integration test: 6 sub-games with a mocked LLM (issue #32).

This test exercises the orchestrator, dialogue manager, engine, scoring, and
report builder together. The LLM is replaced by a deterministic provider, and
the MCP agent clients are no-op fakes, so the run is fully local and
reproducible.
"""

from __future__ import annotations

from typing import Any, cast

from copthief.constants import Outcome
from copthief.llm.provider import LLMProvider
from copthief.mcp.client import AgentClient
from copthief.reporting.game_report import build_report
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import GameEngine
from copthief.services.orchestrator import Orchestrator
from copthief.services.role_assigner import RoleAssigner
from copthief.services.scoring import ScoreBook
from copthief.shared.gatekeeper import ApiGatekeeper


class FakeClient:
    """No-op MCP client that records messages but never touches the network."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.role: str | None = None

    def set_role(self, role: str) -> None:
        self.role = role

    def receive_message(self, text: str) -> str:
        self.messages.append(text)
        return "ack"


class StaticProvider(LLMProvider):
    """Mock LLM that always returns the same parseable intent."""

    def __init__(self, intent: str) -> None:
        self.intent = intent

    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        return self.intent


def _metadata() -> dict[str, Any]:
    return {
        "group_name": "Team-Integration",
        "students": ["A", "B"],
        "github_repo": "https://github.com/test/cop_theif__game",
        "agent_a_mcp_url": "http://127.0.0.1:8101",
        "agent_b_mcp_url": "http://127.0.0.1:8102",
        "timezone": "Asia/Jerusalem",
    }


def _gatekeeper() -> ApiGatekeeper:
    """Permissive gatekeeper so the test is not delayed by rate limits."""
    return ApiGatekeeper(
        {
            "rate_limits": {
                "version": "1.00",
                "services": {
                    "default": {
                        "requests_per_minute": 100000,
                        "requests_per_hour": 1000000,
                        "concurrent_max": 100,
                        "retry_after_seconds": 0,
                        "max_retries": 0,
                    }
                },
            }
        }
    )


def test_six_sub_games_produce_valid_report() -> None:
    engine = GameEngine(grid_size=(5, 5), max_moves=25, max_barriers=0)
    dialogue = DialogueManager(vision_radius=2)
    provider = StaticProvider("move north")
    gatekeeper = _gatekeeper()
    clients = cast(dict[str, AgentClient], {"A": FakeClient(), "B": FakeClient()})
    role_assigner = RoleAssigner(swap_at_subgame=4)
    orchestrator = Orchestrator(
        engine=engine,
        dialogue=dialogue,
        provider=provider,
        gatekeeper=gatekeeper,
        clients=clients,
        role_assigner=role_assigner,
    )

    scorebook = ScoreBook({"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5})
    moves_per_game: list[int] = []

    for index in range(1, 7):
        result = orchestrator.run_sub_game(index)
        assert result.outcome in {Outcome.COP_WIN, Outcome.THIEF_WIN}
        assert result.moves > 0
        assert result.attempts >= 1
        scorebook.record(result.cop_agent, result.thief_agent, result.outcome)
        moves_per_game.append(result.moves)

    report = build_report(_metadata(), scorebook.sub_games, moves_per_game, scorebook).to_dict()

    assert report["group_name"] == "Team-Integration"
    assert report["students"] == ["A", "B"]
    assert len(report["sub_games"]) == 6

    expected_role = {"cop": 0, "thief": 0}
    expected_agent = {"agent_a": 0, "agent_b": 0}
    for i, sub in enumerate(report["sub_games"], start=1):
        assert sub["index"] == i
        assert sub["cop_agent"] in {"A", "B"}
        assert sub["thief_agent"] in {"A", "B"}
        assert sub["thief_agent"] != sub["cop_agent"]
        assert sub["winner"] in {"cop_win", "thief_win"}
        assert isinstance(sub["moves"], int)
        assert isinstance(sub["cop_score"], int)
        assert isinstance(sub["thief_score"], int)

        expected_role["cop"] += sub["cop_score"]
        expected_role["thief"] += sub["thief_score"]
        if sub["cop_agent"] == "A":
            expected_agent["agent_a"] += sub["cop_score"]
            expected_agent["agent_b"] += sub["thief_score"]
        else:
            expected_agent["agent_b"] += sub["cop_score"]
            expected_agent["agent_a"] += sub["thief_score"]

    assert report["totals"] == expected_role
    assert report["totals_by_agent"] == expected_agent
