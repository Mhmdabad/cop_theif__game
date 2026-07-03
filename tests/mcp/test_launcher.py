"""Tests for the MCP-mode game runner (fake sessions, no network/API key)."""

from __future__ import annotations

from typing import Any

from copthief.llm.provider import LLMProvider
from copthief.mcp.launcher import run_game
from copthief.shared.config import Config
from copthief.shared.gatekeeper import ApiGatekeeper

CONFIG = {
    "version": "1.00",
    "grid_size": [3, 3],
    "max_moves": 6,
    "num_games": 6,
    "max_barriers": 2,
    "vision_radius": 2,
    "random_start": True,
    "min_start_distance": 2,
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    "llm": {"provider": "anthropic", "model": "claude", "temperature": 0.7},
    "mcp": {"agent_a_port": 8101, "agent_b_port": 8102, "host": "127.0.0.1"},
    "roles": {"swap_at_subgame": 4},
    "report": {
        "group_name": "Swalha-Abad",
        "students": [{"id": "1"}, {"id": "2"}],
        "github_repo": "https://github.com/Mhmdabad/cop_theif__game",
        "timezone": "Asia/Jerusalem",
    },
    "reporting": {"email_enabled": False},
}

FAST_LIMITS = {
    "rate_limits": {
        "services": {
            "default": {
                "requests_per_minute": 100000,
                "requests_per_hour": 1000000,
                "concurrent_max": 5,
                "retry_after_seconds": 0,
                "max_retries": 0,
            }
        }
    }
}


class FakeSession:
    """Records tool calls; authenticates the local token."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.calls.append((name, arguments))
        if name == "authenticate_location":
            return arguments.get("token") == "local-token"
        return "ack"


class StaticProvider(LLMProvider):
    """Always answers with the same parseable natural-language intent."""

    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        return "move north"


def test_run_game_full_report_over_fake_sessions() -> None:
    sessions = {"A": FakeSession(), "B": FakeSession()}
    report = run_game(
        Config(CONFIG),
        sessions,
        provider=StaticProvider(),
        sinks=[],
        gatekeeper=ApiGatekeeper(FAST_LIMITS),
    )

    assert report["group_name"] == "Swalha-Abad"
    assert len(report["sub_games"]) == 6
    # 3/3 role swap: A cops sub-games 1-3, B cops 4-6.
    assert [g["cop_agent"] for g in report["sub_games"]] == ["A", "A", "A", "B", "B", "B"]
    assert set(report["totals"]) == {"cop", "thief"}
    assert set(report["totals_by_agent"]) == {"agent_a", "agent_b"}

    for session in sessions.values():
        names = {name for name, _ in session.calls}
        assert "authenticate_location" in names
        assert "set_role" in names
        assert "receive_message" in names  # natural-language traffic flowed


def test_run_game_rejects_bad_token() -> None:
    class RejectingSession(FakeSession):
        def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
            if name == "authenticate_location":
                return False
            return super().call_tool(name, arguments)

    try:
        run_game(
            Config(CONFIG),
            {"A": RejectingSession(), "B": FakeSession()},
            provider=StaticProvider(),
            sinks=[],
            gatekeeper=ApiGatekeeper(FAST_LIMITS),
        )
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "authentication" in str(exc)
