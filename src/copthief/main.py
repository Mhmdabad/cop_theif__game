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

from copthief.agents import Strategy, create_strategy
from copthief.constants import Role
from copthief.sdk import CopThiefSDK
from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action, GameEngine
from copthief.shared.config import Config


def _strategy_fn(strategy: Strategy, agent_label: str) -> Any:
    """Adapt a ``Strategy`` to the SDK's ``(role, engine) -> Action`` signature."""

    def choose(role: Role, engine: GameEngine) -> Action:
        state = engine.state
        if role.value == "cop":
            my_pos, opp_pos = state.cop_pos, state.thief_pos
        else:
            my_pos, opp_pos = state.thief_pos, state.cop_pos
        observation = Observation(
            role=role,
            my_position=my_pos,
            opponent_position=opp_pos,
            barriers=set(state.barriers),
            last_message="",
            move_number=state.move_number,
        )
        return strategy.choose_action(observation, "")

    return choose


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

    strategy_a = create_strategy(config._data, config.grid_size)
    strategy_b = create_strategy(config._data, config.grid_size)
    report = sdk.play_game(
        _strategy_fn(strategy_a, "A"),
        _strategy_fn(strategy_b, "B"),
        _metadata_from_config(config),
    )

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
