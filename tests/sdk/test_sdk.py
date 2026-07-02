"""Tests for CopThiefSDK single entry point (issue #20)."""

from __future__ import annotations

from typing import Any

from copthief.constants import ActionType, Outcome, Role
from copthief.sdk import CopThiefSDK
from copthief.services.game_engine import Action, GameEngine
from copthief.shared.config import Config


def _config(**overrides: Any) -> Config:
    data = {
        "version": "1.00",
        "grid_size": [5, 5],
        "max_moves": 25,
        "num_games": 2,
        "max_barriers": 5,
        "vision_radius": 2,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        "llm": {"provider": "anthropic", "model": "claude", "temperature": 0.7},
        "mcp": {"agent_a_port": 8101, "agent_b_port": 8102, "host": "127.0.0.1"},
        "roles": {"swap_at_subgame": 2},
        "reporting": {"email_enabled": False},
    }
    data.update(overrides)
    return Config(data)


def _scripted(cop_moves: list[tuple[int, int]], thief_moves: list[tuple[int, int]]) -> Any:
    cop_index = 0
    thief_index = 0

    def strategy(role: Role, engine: GameEngine) -> Action:  # noqa: ARG001
        nonlocal cop_index, thief_index
        if role == Role.COP:
            move = cop_moves[cop_index % len(cop_moves)]
            cop_index += 1
        else:
            move = thief_moves[thief_index % len(thief_moves)]
            thief_index += 1
        return Action(ActionType.MOVE, *move)

    return strategy


def test_play_sub_game_records_outcome_and_score() -> None:
    sdk = CopThiefSDK(_config(grid_size=[2, 2]))
    # On a 2x2 board thief moves (1,1)->(0,1); cop then moves (0,0)->(0,1) for capture.
    strategy_a = _scripted(cop_moves=[(0, 1)], thief_moves=[(-1, 0)])
    strategy_b = _scripted(cop_moves=[(0, 1)], thief_moves=[(-1, 0)])

    outcome = sdk.play_sub_game(strategy_a, strategy_b, "A", "B")

    assert outcome == Outcome.COP_WIN
    assert sdk.scorebook.totals().by_agent == {"agent_a": 20, "agent_b": 5}


def test_play_game_swaps_roles_and_builds_report() -> None:
    sdk = CopThiefSDK(_config(grid_size=[2, 2], num_games=2, swap_at_subgame=2))
    strategy_a = _scripted(cop_moves=[(0, 1), (0, 1)], thief_moves=[(-1, 0), (-1, 0)])
    strategy_b = _scripted(cop_moves=[(0, 1), (0, 1)], thief_moves=[(-1, 0), (-1, 0)])

    report = sdk.play_game(strategy_a, strategy_b, {"group_name": "Test"})

    assert report["group_name"] == "Test"
    assert len(report["sub_games"]) == 2
    assert report["sub_games"][0]["cop_agent"] == "A"
    assert report["sub_games"][1]["cop_agent"] == "B"
    assert report["totals"]["by_role"] == {"cop": 40, "thief": 10}
    assert report["totals"]["by_agent"] == {"agent_a": 25, "agent_b": 25}


def test_build_report_without_playing_is_empty_totals() -> None:
    sdk = CopThiefSDK(_config())
    report = sdk.build_report({"group_name": "Empty"})

    assert report["sub_games"] == []
    assert report["totals"]["by_role"] == {"cop": 0, "thief": 0}
