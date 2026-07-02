"""Tests for the role-capable FastMCP agent server (issue #22)."""

from __future__ import annotations

import pytest

from copthief.constants import Role
from copthief.mcp.agent_server import AgentServer


def test_server_starts_with_role() -> None:
    server = AgentServer(Role.COP, 8101)
    assert server.role == Role.COP
    assert server.port == 8101


def test_receive_message_stores_and_acks() -> None:
    server = AgentServer(Role.THIEF, 8102)
    assert server.receive_message("hello") == "ack"
    assert server._messages == ["hello"]


def test_report_observation_mentions_role_and_actions() -> None:
    server = AgentServer(Role.COP, 8101)
    obs = server.report_observation()
    assert "cop" in obs
    assert "place a barrier" in obs

    server.set_role(Role.THIEF)
    obs = server.report_observation()
    assert "thief" in obs
    assert "place a barrier" not in obs


def test_propose_action_differs_by_role() -> None:
    cop = AgentServer(Role.COP, 8101)
    thief = AgentServer(Role.THIEF, 8102)

    assert "barrier" in cop.propose_action()
    assert "move away" in thief.propose_action()


def test_authenticate_location_validates_token() -> None:
    server = AgentServer(Role.COP, 8101, token="secret")
    assert server.authenticate_location("secret") is True
    assert server.authenticate_location("wrong") is False


@pytest.mark.anyio
async def test_tools_are_registered() -> None:
    server = AgentServer(Role.COP, 8101)
    tools = {tool.name for tool in await server.mcp.list_tools()}
    assert tools == {
        "set_role",
        "receive_message",
        "report_observation",
        "propose_action",
        "authenticate_location",
    }
