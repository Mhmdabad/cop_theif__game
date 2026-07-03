"""CLI entry point for a local CopThief run (issue #31).

Usage::

    uv run copthief --config config/config.json            # heuristic mode
    uv run copthief --config config/config.json --mode mcp # real MCP + LLM

Heuristic mode plays in-process (free, no API key). MCP mode spawns the two
agent servers as separate processes and drives the natural-language dialogue
through the configured LLM — this is the assignment's showcase pipeline.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from copthief.agents import Strategy, create_strategy
from copthief.constants import Role
from copthief.reporting.game_report import report_metadata
from copthief.sdk import CopThiefSDK
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import Action, GameEngine
from copthief.shared.config import Config


def _strategy_fn(strategy: Strategy, dialogue: DialogueManager) -> Any:
    """Adapt a ``Strategy`` to the SDK's ``(role, engine) -> Action`` signature.

    Observations go through ``DialogueManager.observe`` so heuristic mode obeys
    the same partial observability (``vision_radius``) as MCP mode.
    """

    def choose(role: Role, engine: GameEngine) -> Action:
        observation = dialogue.observe(role, engine.state)
        return strategy.choose_action(observation, "")

    return choose


def _print_report(report: dict[str, Any]) -> None:
    """Print the per-sub-game turn log and totals."""
    print("\nTurn log / Sub-game results:")
    for sub_game in report["sub_games"]:
        print(
            f"  Sub-game {sub_game['index']}: "
            f"cop={sub_game['cop_agent']} thief={sub_game['thief_agent']} "
            f"winner={sub_game['winner']} moves={sub_game['moves']}"
        )
    print(f"\nTotals: {report['totals']}")
    print("Report written to results/game_report.json")


def run(config_path: str, mode: str = "heuristic") -> int:
    """Play a full local game in the chosen mode and print the turn log."""
    config = Config.from_file(config_path)
    print(
        f"Starting CopThief local run ({mode} mode): {config.num_games} sub-games "
        f"on a {config.grid_size[0]}x{config.grid_size[1]} grid"
    )

    if mode == "mcp":
        from copthief.mcp.launcher import launch

        report = launch(config)
    else:
        sdk = CopThiefSDK(config)
        dialogue = DialogueManager(config.vision_radius)
        strategy_a = create_strategy(config._data, config.grid_size)
        strategy_b = create_strategy(config._data, config.grid_size)
        report = sdk.play_game(
            _strategy_fn(strategy_a, dialogue),
            _strategy_fn(strategy_b, dialogue),
            report_metadata(config),
        )

    _print_report(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and start a local run."""
    parser = argparse.ArgumentParser(description="CopThief local CLI")
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Path to the JSON configuration file",
    )
    parser.add_argument(
        "--mode",
        choices=["heuristic", "mcp"],
        default="heuristic",
        help="heuristic: in-process strategies (free); mcp: real servers + LLM",
    )
    args = parser.parse_args(argv)
    return run(args.config, args.mode)


if __name__ == "__main__":
    sys.exit(main())
