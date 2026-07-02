"""Tests for Orchestrator turn loop and technical-loss re-run (issue #26)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from copthief.constants import Outcome
from copthief.mcp.client import AgentClient
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import GameEngine
from copthief.services.orchestrator import Orchestrator
from copthief.services.role_assigner import RoleAssigner
from copthief.shared.gatekeeper import ApiGatekeeper

BASE_CFG = {
    "rate_limits": {
        "version": "1.00",
        "services": {
            "default": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "concurrent_max": 5,
                "retry_after_seconds": 0,
                "max_retries": 0,
            }
        },
    }
}


def _orchestrator(
    grid_size: tuple[int, int] = (3, 3),
    responses: list[object] | None = None,
) -> tuple[Orchestrator, MagicMock]:
    engine = GameEngine(grid_size, max_moves=10)
    dialogue = DialogueManager(vision_radius=5)
    gatekeeper = ApiGatekeeper(BASE_CFG)

    provider = MagicMock()
    response_iter = iter(responses or [])

    def _next_response(*_a: object, **_k: object) -> object:
        value = next(response_iter)
        if isinstance(value, BaseException):
            raise value
        return value

    provider.complete.side_effect = _next_response

    client_a = AgentClient("http://a", gatekeeper)
    client_a.set_session(MagicMock())
    client_b = AgentClient("http://b", gatekeeper)
    client_b.set_session(MagicMock())

    orchestrator = Orchestrator(
        engine=engine,
        dialogue=dialogue,
        provider=provider,
        gatekeeper=gatekeeper,
        clients={"A": client_a, "B": client_b},
        role_assigner=RoleAssigner(),
    )
    return orchestrator, provider


def test_sub_game_runs_to_capture() -> None:
    orchestrator, _ = _orchestrator(
        grid_size=(3, 3),
        responses=[
            "move north-west",  # thief at (2,2) -> (1,1)
            "move south-east",  # cop at (0,0) -> (1,1) capture
        ],
    )

    result = orchestrator.run_sub_game(1)

    assert result.outcome == Outcome.COP_WIN
    assert result.cop_agent == "A"
    assert result.thief_agent == "B"


def test_roles_swap_for_second_half() -> None:
    orchestrator, _ = _orchestrator(
        grid_size=(3, 3),
        responses=[
            "move north-west",
            "move south-east",
        ],
    )

    result = orchestrator.run_sub_game(4)

    assert result.cop_agent == "B"
    assert result.thief_agent == "A"


def test_technical_loss_re_runs() -> None:
    responses = [
        "move north-west",
        RuntimeError("llm failure"),
        "move north-west",
        "move south-east",
    ]
    orchestrator, provider = _orchestrator(grid_size=(3, 3), responses=responses)

    result = orchestrator.run_sub_game(1)

    assert result.outcome == Outcome.COP_WIN
    assert result.technical_losses == 1
    assert result.attempts == 2
    assert provider.complete.call_count == 4


def test_exhausted_attempts_raise() -> None:
    orchestrator, _ = _orchestrator(
        grid_size=(3, 3),
        responses=[RuntimeError("fail")],
    )
    orchestrator.max_attempts = 2

    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        orchestrator.run_sub_game(1)


def test_agents_receive_messages() -> None:
    orchestrator, _ = _orchestrator(
        grid_size=(3, 3),
        responses=[
            "move north-west",
            "move south-east",
        ],
    )
    orchestrator.run_sub_game(1)

    client_a = orchestrator.clients["A"]
    client_b = orchestrator.clients["B"]
    assert client_a._session is not None
    assert client_b._session is not None
    a_tools = {call.args[0] for call in client_a._session.call_tool.call_args_list}
    b_tools = {call.args[0] for call in client_b._session.call_tool.call_args_list}
    assert "receive_message" in a_tools
    assert "receive_message" in b_tools


def test_thief_moves_first() -> None:
    orchestrator, provider = _orchestrator(
        grid_size=(3, 3),
        responses=[
            "move north-west",
            "move south-east",
        ],
    )
    orchestrator.run_sub_game(1)

    first_prompt = provider.complete.call_args_list[0].args[0]
    assert "thief" in first_prompt.lower()


def test_illegal_intent_falls_back_to_heuristic() -> None:
    orchestrator, provider = _orchestrator(
        grid_size=(2, 2),
        responses=[
            "I like pizza",  # unparsable -> heuristic moves thief (1,1)->(0,1)
            "move east",  # cop (0,0)->(0,1) capture
        ],
    )

    result = orchestrator.run_sub_game(1)

    assert result.outcome == Outcome.COP_WIN
    assert provider.complete.call_count == 2
