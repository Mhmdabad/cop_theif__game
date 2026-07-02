"""Tests for dialogue prompts, observations, and intent parsing (issue #25)."""

from __future__ import annotations

import pytest

from copthief.constants import ActionType, Role
from copthief.services.dialogue import DialogueManager, Observation
from copthief.services.exceptions import IllegalMoveError
from copthief.services.game_engine import Action, GridState


def _state(cop_pos: tuple[int, int], thief_pos: tuple[int, int]) -> GridState:
    return GridState(cop_pos=cop_pos, thief_pos=thief_pos)


def test_opponent_visible_within_vision_radius() -> None:
    dialogue = DialogueManager(vision_radius=2)
    state = _state((0, 0), (1, 1))
    obs = dialogue.observe(Role.COP, state)

    assert obs.opponent_position == (1, 1)


def test_opponent_hidden_beyond_vision_radius() -> None:
    dialogue = DialogueManager(vision_radius=1)
    state = _state((0, 0), (3, 3))
    obs = dialogue.observe(Role.THIEF, state)

    assert obs.opponent_position is None


def test_observation_never_includes_full_state() -> None:
    dialogue = DialogueManager(vision_radius=5)
    state = _state((0, 0), (4, 4))
    obs = dialogue.observe(Role.COP, state, last_message="hi")

    assert obs.my_position == (0, 0)
    assert obs.role == Role.COP
    assert isinstance(obs, Observation)


def test_prompt_mentions_role_and_action_set() -> None:
    dialogue = DialogueManager(vision_radius=5)
    state = _state((0, 0), (1, 0))
    obs = dialogue.observe(Role.COP, state)
    prompt = dialogue.prompt(obs)

    assert "cop" in prompt
    assert "place a barrier" in prompt
    assert "(1, 0)" in prompt

    obs = dialogue.observe(Role.THIEF, state)
    prompt = dialogue.prompt(obs)
    assert "thief" in prompt
    assert "place a barrier" not in prompt


def test_parse_intent_move_directions() -> None:
    dialogue = DialogueManager(1)
    assert dialogue.parse_intent("move north") == Action(ActionType.MOVE, -1, 0)
    assert dialogue.parse_intent("go south-east") == Action(ActionType.MOVE, 1, 1)
    assert dialogue.parse_intent("northwest") == Action(ActionType.MOVE, -1, -1)


def test_parse_intent_place_barrier() -> None:
    dialogue = DialogueManager(1)
    assert dialogue.parse_intent("place a barrier") == Action(ActionType.PLACE_BARRIER)


def test_parse_intent_empty_raises() -> None:
    dialogue = DialogueManager(1)
    with pytest.raises(IllegalMoveError, match="Empty"):
        dialogue.parse_intent("")


def test_parse_intent_garbled_raises() -> None:
    dialogue = DialogueManager(1)
    with pytest.raises(IllegalMoveError, match="Unparseable"):
        dialogue.parse_intent("I like pizza")
