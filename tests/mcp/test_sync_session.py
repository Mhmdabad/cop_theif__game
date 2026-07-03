"""Tests for the sync bridge over the async FastMCP client.

Uses fastmcp's in-memory transport (a ``FastMCP`` instance as the target), so
the real tool-call path is exercised without any network.
"""

from __future__ import annotations

from copthief.constants import Role
from copthief.mcp.agent_server import AgentServer
from copthief.mcp.sync_session import SyncMCPSession


def test_call_tools_over_in_memory_transport() -> None:
    server = AgentServer(Role.COP, port=8101)
    with SyncMCPSession(server.mcp) as session:
        assert session.call_tool("authenticate_location", {"token": "local-token"}) is True
        assert session.call_tool("authenticate_location", {"token": "wrong"}) is False
        assert session.call_tool("receive_message", {"text": "I am near the wall"}) == "ack"
        observation = session.call_tool("report_observation", {})
        assert "cop" in observation


def test_set_role_switches_action_set() -> None:
    server = AgentServer(Role.COP, port=8101)
    with SyncMCPSession(server.mcp) as session:
        session.call_tool("set_role", {"role": "thief"})
        observation = session.call_tool("report_observation", {})
        assert "thief" in observation
        assert "barrier" not in observation


def test_disconnected_session_raises() -> None:
    session = SyncMCPSession("http://127.0.0.1:1/sse")
    try:
        session.call_tool("receive_message", {"text": "x"})
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass
