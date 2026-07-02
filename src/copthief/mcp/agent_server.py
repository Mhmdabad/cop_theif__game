"""Role-capable FastMCP agent server (issue #22).

A single implementation is launched twice (Agent-A and Agent-B) on separate
ports. Each instance accepts a role per sub-game and exposes the tool contract
from PLAN §4.4.
"""

from __future__ import annotations

from fastmcp import FastMCP

from copthief.constants import Role


class AgentServer:
    """One MCP server instance: stateful, role-capable."""

    def __init__(self, role: Role, port: int, token: str = "local-token"):
        self.role = role
        self.port = port
        self._token = token
        self._messages: list[str] = []
        self._last_observation = ""
        self.mcp = FastMCP(f"agent-{port}")
        self._register_tools()

    def set_role(self, role: Role) -> None:
        """Switch role for the next sub-game (3/3 swap support)."""
        self.role = role

    def _register_tools(self) -> None:
        self.mcp.add_tool(self.set_role)
        self.mcp.add_tool(self.receive_message)
        self.mcp.add_tool(self.report_observation)
        self.mcp.add_tool(self.propose_action)
        self.mcp.add_tool(self.authenticate_location)

    def receive_message(self, text: str) -> str:
        """Deliver a natural-language message from the opponent."""
        self._messages.append(text)
        return "ack"

    def report_observation(self) -> str:
        """Return the agent's current partial observation as natural language."""
        action_set = "move or place a barrier" if self.role == Role.COP else "move"
        obs = (
            f"I am the {self.role.value}. "
            f"Available actions: {action_set}. "
            f"Recent messages: {self._messages[-3:]}."
        )
        self._last_observation = obs
        return obs

    def propose_action(self) -> str:
        """Return the agent's natural-language intent for the current turn."""
        if self.role == Role.COP:
            return "I will move toward the thief or place a barrier if needed."
        return "I will move away from the cop to avoid capture."

    def authenticate_location(self, token: str) -> bool:
        """Verify the shared local token."""
        return token == self._token

    def run(self) -> None:
        """Start the server on the configured port."""
        self.mcp.run(transport="sse", port=self.port)
