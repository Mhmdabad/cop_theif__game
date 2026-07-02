"""Dialogue manager: prompts, partial observations, and intent parsing (issue #25).

The orchestrator uses this module to build role-appropriate natural-language
prompts for the LLM and to parse the model's free-text reply back into a
valid ``Action``. Partial observability is enforced here: the opponent's
position is revealed only when within ``vision_radius`` (PRD §3.4).
"""

from __future__ import annotations

from dataclasses import dataclass

from copthief.constants import ActionType, Role
from copthief.services.exceptions import IllegalMoveError
from copthief.services.game_engine import Action, GridState


@dataclass(frozen=True, slots=True)
class Observation:
    """What an agent is allowed to know on its turn."""

    role: Role
    my_position: tuple[int, int]
    opponent_position: tuple[int, int] | None
    barriers: set[tuple[int, int]]
    last_message: str
    move_number: int


class DialogueManager:
    """Build prompts and parse intents under partial observability."""

    def __init__(self, vision_radius: int):
        self.vision_radius = vision_radius

    def observe(self, role: Role, state: GridState, last_message: str = "") -> Observation:
        """Return the agent's partial observation of ``state``.

        The opponent's exact cell is included only when within Chebyshev
        distance ``vision_radius``; otherwise it is ``None``.
        """
        my_pos, opp_pos = (
            (state.cop_pos, state.thief_pos)
            if role == Role.COP
            else (state.thief_pos, state.cop_pos)
        )
        opponent_visible = self._chebyshev(my_pos, opp_pos) <= self.vision_radius
        return Observation(
            role=role,
            my_position=my_pos,
            opponent_position=opp_pos if opponent_visible else None,
            barriers=set(state.barriers),
            last_message=last_message,
            move_number=state.move_number,
        )

    @staticmethod
    def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def prompt(self, observation: Observation) -> str:
        """Build a natural-language prompt for the LLM."""
        role = observation.role.value
        action_set = (
            "move one cell in any of 8 directions, or place a barrier on your current cell"
            if observation.role == Role.COP
            else "move one cell in any of 8 directions"
        )
        opponent = (
            f"at {observation.opponent_position}"
            if observation.opponent_position
            else "out of sight"
        )
        return (
            f"You are the {role}. You are at {observation.my_position}. "
            f"The opponent is {opponent}. "
            f"Known barriers: {sorted(observation.barriers)}. "
            f"Turn {observation.move_number}. "
            f"You may {action_set}. "
            f"Recent opponent message: {observation.last_message!r}. "
            "Reply with ONLY your intended action, e.g. 'move north-east' or 'place barrier'."
        )

    def parse_intent(self, text: str) -> Action:
        """Parse a free-text intent into an ``Action``.

        Raises:
            IllegalMoveError: if the intent cannot be mapped to a legal action.
        """
        lowered = text.strip().lower()
        if not lowered:
            raise IllegalMoveError("Empty intent")

        if "barrier" in lowered:
            return Action(ActionType.PLACE_BARRIER)

        direction_map = {
            "north-east": (-1, 1),
            "northeast": (-1, 1),
            "north-west": (-1, -1),
            "northwest": (-1, -1),
            "south-east": (1, 1),
            "southeast": (1, 1),
            "south-west": (1, -1),
            "southwest": (1, -1),
            "north": (-1, 0),
            "south": (1, 0),
            "east": (0, 1),
            "west": (0, -1),
        }
        for phrase, delta in direction_map.items():
            if phrase in lowered:
                return Action(ActionType.MOVE, *delta)

        raise IllegalMoveError(f"Unparseable intent: {text!r}")
