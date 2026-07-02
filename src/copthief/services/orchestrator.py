"""Orchestrator: turn loop, role assignment, and technical-loss re-run (issue #26).

The orchestrator drives one sub-game at a time. It asks the current agent for
a natural-language intent via the LLM, delivers that message to the opponent,
and applies the parsed action to the engine. LLM/MCP failures become
``technical_loss`` with a re-run so the full game always reports 6 valid
sub-games (PRD §2.2/§3.7).
"""

from __future__ import annotations

from dataclasses import dataclass

from copthief.constants import Outcome
from copthief.llm.provider import LLMProvider
from copthief.mcp.client import AgentClient
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import GameEngine
from copthief.services.role_assigner import RoleAssigner
from copthief.shared.gatekeeper import ApiGatekeeper


@dataclass
class SubGameResult:
    """Outcome of one sub-game, including any technical-loss re-runs."""

    outcome: Outcome
    moves: int
    attempts: int
    technical_losses: int = 0
    cop_agent: str = ""
    thief_agent: str = ""


class Orchestrator:
    """Turn loop for a single sub-game."""

    def __init__(
        self,
        engine: GameEngine,
        dialogue: DialogueManager,
        provider: LLMProvider,
        gatekeeper: ApiGatekeeper,
        clients: dict[str, AgentClient],
        role_assigner: RoleAssigner,
        max_attempts: int = 3,
    ):
        self.engine = engine
        self.dialogue = dialogue
        self.provider = provider
        self.gatekeeper = gatekeeper
        self.clients = clients
        self.role_assigner = role_assigner
        self.max_attempts = max_attempts

    def run_sub_game(self, sub_game_index: int) -> SubGameResult:
        """Run a sub-game, re-running on technical failures."""
        technical_losses = 0
        roles = self.role_assigner.roles_for(sub_game_index)
        cop_agent = "A" if roles["A"] == "cop" else "B"
        thief_agent = "B" if cop_agent == "A" else "A"

        for attempt in range(1, self.max_attempts + 1):
            try:
                self._configure_agents(roles)
                outcome = self._play(cop_agent, thief_agent)
                return SubGameResult(
                    outcome=outcome,
                    moves=self.engine.state.move_number,
                    attempts=attempt,
                    technical_losses=technical_losses,
                    cop_agent=cop_agent,
                    thief_agent=thief_agent,
                )
            except Exception as exc:  # noqa: BLE001 - technical loss catches all
                technical_losses += 1
                if attempt == self.max_attempts:
                    raise RuntimeError(
                        f"Sub-game {sub_game_index} failed after {self.max_attempts} attempts"
                    ) from exc

        raise RuntimeError("Unreachable")  # pragma: no cover

    def _configure_agents(self, roles: dict[str, str]) -> None:
        for agent, role in roles.items():
            self.clients[agent].set_role(role)

    def _play(self, cop_agent: str, thief_agent: str) -> Outcome:
        self.engine.reset()
        received: dict[str, str] = {"A": "", "B": ""}
        role_to_agent = {"cop": cop_agent, "thief": thief_agent}

        while self.engine.state.outcome == Outcome.ONGOING:
            role = self.engine.state.turn
            agent = role_to_agent[role.value]
            opponent = "B" if agent == "A" else "A"

            observation = self.dialogue.observe(role, self.engine.state, received[agent])
            prompt = self.dialogue.prompt(observation)
            intent_text = self.gatekeeper.execute(self.provider.complete, prompt)
            action = self.dialogue.parse_intent(intent_text)

            self.clients[opponent].receive_message(intent_text)
            self.engine.apply_action(role, action)
            received[opponent] = intent_text

        return self.engine.state.outcome
