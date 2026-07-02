"""Orchestrator-side MCP client wrapper (issue #23).

All calls to the agent server tools are routed through ``ApiGatekeeper`` so
rate limits and retries apply to MCP traffic as well as LLM traffic.
"""

from __future__ import annotations

from typing import Any

from copthief.shared.gatekeeper import ApiGatekeeper


class AgentClient:
    """Synchronous wrapper around one agent server's tool surface."""

    def __init__(self, server_url: str, gatekeeper: ApiGatekeeper):
        self.server_url = server_url
        self.gatekeeper = gatekeeper
        self._session: Any | None = None

    def set_session(self, session: Any) -> None:
        """Inject the active MCP session (sync or sync-wrapped)."""
        self._session = session

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self._session is None:
            raise RuntimeError("AgentClient is not connected")
        return self.gatekeeper.execute(self._session.call_tool, name, arguments)

    def receive_message(self, text: str) -> str:
        """Deliver ``text`` to the agent's ``receive_message`` tool."""
        return self._call_tool("receive_message", {"text": text})

    def report_observation(self) -> str:
        """Fetch the agent's ``report_observation`` result."""
        return self._call_tool("report_observation", {})

    def propose_action(self) -> str:
        """Fetch the agent's ``propose_action`` result."""
        return self._call_tool("propose_action", {})

    def authenticate_location(self, token: str) -> bool:
        """Call ``authenticate_location`` and coerce the result to bool."""
        result = self._call_tool("authenticate_location", {"token": token})
        return bool(result)
