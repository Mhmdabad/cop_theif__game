"""CLI entry-point tests (issue #31).

``main.py`` is omitted from the coverage gate by design, but we still verify
argument parsing and SDK delegation.
"""

from __future__ import annotations

from typing import Any

from copthief import main


class FakeSDK:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.calls: list[tuple[Any, Any, Any]] = []

    def play_game(
        self,
        strategy_a: Any,
        strategy_b: Any,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append((strategy_a, strategy_b, metadata))
        return {
            "group_name": metadata["group_name"],
            "sub_games": [
                {
                    "index": 1,
                    "cop_agent": "A",
                    "thief_agent": "B",
                    "winner": "cop_win",
                    "moves": 5,
                    "cop_score": 20,
                    "thief_score": 5,
                }
            ],
            "totals": {
                "by_role": {"cop": 20, "thief": 5},
                "by_agent": {"agent_a": 20, "agent_b": 5},
            },
        }


def test_main_runs_local_game(capsys: Any, monkeypatch: Any, tmp_path: Any) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"version":"1.00","grid_size":[3,3],"max_moves":10,"num_games":1,"max_barriers":0,"vision_radius":2,"scoring":{"cop_win":20,"thief_win":10,"cop_loss":5,"thief_loss":5},"llm":{"provider":"anthropic","model":"claude","temperature":0.7},"mcp":{"agent_a_port":8101,"agent_b_port":8102,"host":"127.0.0.1"},"roles":{"swap_at_subgame":2},"reporting":{"email_enabled":false}}'
    )
    monkeypatch.setattr(main, "CopThiefSDK", FakeSDK)

    code = main.run(str(config_path))

    assert code == 0
    captured = capsys.readouterr()
    assert "Starting CopThief local run" in captured.out
    assert "Sub-game 1" in captured.out
    assert "cop=A" in captured.out


def test_main_default_config_arg(monkeypatch: Any, tmp_path: Any) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"version":"1.00","grid_size":[2,2],"max_moves":5,"num_games":1,"max_barriers":0,"vision_radius":2,"scoring":{"cop_win":20,"thief_win":10,"cop_loss":5,"thief_loss":5},"llm":{"provider":"anthropic","model":"claude","temperature":0.7},"mcp":{"agent_a_port":8101,"agent_b_port":8102,"host":"127.0.0.1"},"roles":{"swap_at_subgame":2},"reporting":{"email_enabled":false}}'
    )
    monkeypatch.setattr(main, "CopThiefSDK", FakeSDK)

    code = main.main(["--config", str(config_path)])

    assert code == 0
