"""Tests for the orchestrator MCP client wrapper (issue #23)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from copthief.mcp.client import AgentClient
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


def _client() -> AgentClient:
    return AgentClient("http://127.0.0.1:8101", ApiGatekeeper(BASE_CFG))


def test_receive_message_routes_through_gatekeeper() -> None:
    client = _client()
    session = MagicMock()
    session.call_tool.return_value = "ack"
    client.set_session(session)

    assert client.receive_message("hi") == "ack"
    session.call_tool.assert_called_once_with("receive_message", {"text": "hi"})


def test_report_observation_routes_through_gatekeeper() -> None:
    client = _client()
    session = MagicMock()
    session.call_tool.return_value = "obs"
    client.set_session(session)

    assert client.report_observation() == "obs"
    session.call_tool.assert_called_once_with("report_observation", {})


def test_propose_action_routes_through_gatekeeper() -> None:
    client = _client()
    session = MagicMock()
    session.call_tool.return_value = "move"
    client.set_session(session)

    assert client.propose_action() == "move"
    session.call_tool.assert_called_once_with("propose_action", {})


def test_authenticate_location_coerces_to_bool() -> None:
    client = _client()
    session = MagicMock()
    session.call_tool.return_value = 1
    client.set_session(session)

    assert client.authenticate_location("secret") is True


def test_call_before_connected_raises() -> None:
    client = _client()
    with pytest.raises(RuntimeError, match="not connected"):
        client.receive_message("hi")
