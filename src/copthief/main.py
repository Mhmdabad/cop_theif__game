"""CLI entry point for a local CopThief run (issue #31).

Usage::

    uv run copthief --config config/config.json

The command loads the config, plays the configured number of sub-games through
``CopThiefSDK``, prints a turn log, and writes ``results/game_report.json``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from copthief.constants import ActionType, Role
from copthief.sdk import CopThiefSDK
from copthief.services.game_engine import Action, GameEngine
from copthief.shared.config import Config


def _heuristic_move(role: Role, engine: GameEngine) -> Action:
    """Simple local strategy: cop closes distance, thief increases it."""
    state = engine.state
    if role == Role.COP:
        my_pos = state.cop_pos
        target = state.thief_pos
        prefer_closer = True
    else:
        my_pos = state.thief_pos
        target = state.cop_pos
        prefer_closer = False

    candidates: list[tuple[int, tuple[int, int]]] = []
    for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_pos = (my_pos[0] + d_row, my_pos[1] + d_col)
        if not engine._in_bounds(new_pos):
            continue
        distance = abs(new_pos[0] - target[0]) + abs(new_pos[1] - target[1])
        candidates.append((distance, (d_row, d_col)))

    if not candidates:
        return Action(ActionType.MOVE, 0, 0)

    _distance, best = min(candidates) if prefer_closer else max(candidates)
    return Action(ActionType.MOVE, *best)


def _metadata_from_config(config: Config) -> dict[str, Any]:
    """Build the assignment-required report metadata from config values."""
    mcp = config.mcp
    return {
        "group_name": "Team-Local",
        "students": [],
        "github_repo": "https://github.com/<user>/cop_theif__game",
        "agent_a_mcp_url": f"http://{mcp['host']}:{mcp['agent_a_port']}",
        "agent_b_mcp_url": f"http://{mcp['host']}:{mcp['agent_b_port']}",
        "timezone": "Asia/Jerusalem",
    }


def run(config_path: str) -> int:
    """Play a full local game and print the turn log."""
    config = Config.from_file(config_path)
    sdk = CopThiefSDK(config)

    print(
        f"Starting CopThief local run: {config.num_games} sub-games "
        f"on a {config.grid_size[0]}x{config.grid_size[1]} grid"
    )

    report = sdk.play_game(_heuristic_move, _heuristic_move, _metadata_from_config(config))

    print("\nTurn log / Sub-game results:")
    for sub_game in report["sub_games"]:
        print(
            f"  Sub-game {sub_game['index']}: "
            f"cop={sub_game['cop_agent']} thief={sub_game['thief_agent']} "
            f"winner={sub_game['winner']} moves={sub_game['moves']}"
        )

    print(f"\nTotals: {report['totals']}")
    print("Report written to results/game_report.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and start a local run."""
    parser = argparse.ArgumentParser(description="CopThief local CLI")
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Path to the JSON configuration file",
    )
    args = parser.parse_args(argv)
    return run(args.config)


if __name__ == "__main__":
    sys.exit(main())
