"""Sanity-check ladder: 2x2 -> 5x5 with no technical failures (issue #33).

Runs the same deterministic pipeline on increasing board sizes and records the
outcome of every stage. This mirrors PLAN §6.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from copthief.constants import Outcome
from copthief.llm.provider import LLMProvider
from copthief.mcp.client import AgentClient
from copthief.reporting.game_report import build_report
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import GameEngine
from copthief.services.orchestrator import Orchestrator
from copthief.services.role_assigner import RoleAssigner
from copthief.services.scoring import ScoreBook
from copthief.shared.gatekeeper import ApiGatekeeper


class FakeClient:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.role: str | None = None

    def set_role(self, role: str) -> None:
        self.role = role

    def receive_message(self, text: str) -> str:
        self.messages.append(text)
        return "ack"


class StaticProvider(LLMProvider):
    def __init__(self, intent: str) -> None:
        self.intent = intent

    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        return self.intent


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper(
        {
            "rate_limits": {
                "version": "1.00",
                "services": {
                    "default": {
                        "requests_per_minute": 100000,
                        "requests_per_hour": 1000000,
                        "concurrent_max": 100,
                        "retry_after_seconds": 0,
                        "max_retries": 0,
                    }
                },
            }
        }
    )


def _metadata(stage: str, grid: tuple[int, int]) -> dict[str, Any]:
    return {
        "group_name": f"Team-{stage}",
        "students": ["A", "B"],
        "github_repo": "https://github.com/test/cop_theif__game",
        "agent_a_mcp_url": "http://127.0.0.1:8101",
        "agent_b_mcp_url": "http://127.0.0.1:8102",
        "timezone": "Asia/Jerusalem",
    }


def _run_stage(
    stage: str,
    grid: tuple[int, int],
    max_moves: int,
    num_games: int = 6,
) -> dict[str, Any]:
    engine = GameEngine(grid_size=grid, max_moves=max_moves, max_barriers=0)
    dialogue = DialogueManager(vision_radius=2)
    provider = StaticProvider("move north")
    gatekeeper = _gatekeeper()
    clients = cast(dict[str, AgentClient], {"A": FakeClient(), "B": FakeClient()})
    role_assigner = RoleAssigner(swap_at_subgame=4)
    orchestrator = Orchestrator(
        engine=engine,
        dialogue=dialogue,
        provider=provider,
        gatekeeper=gatekeeper,
        clients=clients,
        role_assigner=role_assigner,
    )

    scorebook = ScoreBook({"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5})
    moves_per_game: list[int] = []
    technical_losses = 0

    for index in range(1, num_games + 1):
        result = orchestrator.run_sub_game(index)
        assert result.technical_losses == 0
        assert result.outcome in {Outcome.COP_WIN, Outcome.THIEF_WIN}
        assert result.moves > 0
        scorebook.record(result.cop_agent, result.thief_agent, result.outcome)
        moves_per_game.append(result.moves)
        technical_losses += result.technical_losses

    report = build_report(_metadata(stage, grid), scorebook.sub_games, moves_per_game, scorebook)
    return {
        "stage": stage,
        "grid": grid,
        "max_moves": max_moves,
        "technical_losses": technical_losses,
        "report": report.to_dict(),
    }


def test_sanity_ladder_all_stages_green(tmp_path: Path) -> None:
    stages = [
        ("2x2", (2, 2), 5),
        ("3x3", (3, 3), 10),
        ("4x4", (4, 4), 15),
        ("5x5", (5, 5), 25),
    ]

    results: list[dict[str, Any]] = []
    for stage, grid, max_moves in stages:
        results.append(_run_stage(stage, grid, max_moves))

    output = tmp_path / "sanity_ladder.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")

    for result in results:
        assert result["technical_losses"] == 0
        report = result["report"]
        assert len(report["sub_games"]) == 6
        assert report["totals"]["cop"] >= 0
        assert report["totals"]["thief"] >= 0
