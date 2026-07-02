"""Tests for typed config loader and version validation (issue #17)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from copthief.shared.config import Config
from copthief.shared.version import ConfigVersionError


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "version": "1.00",
                "grid_size": [7, 7],
                "max_moves": 30,
                "num_games": 6,
                "max_barriers": 5,
                "vision_radius": 2,
                "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
                "llm": {"provider": "anthropic", "model": "claude", "temperature": 0.7},
                "mcp": {"agent_a_port": 8101, "agent_b_port": 8102, "host": "127.0.0.1"},
                "roles": {"swap_at_subgame": 4},
                "reporting": {"email_enabled": False},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_valid_config(config_path: Path) -> None:
    cfg = Config.from_file(config_path)

    assert cfg.grid_size == (7, 7)
    assert cfg.max_moves == 30
    assert cfg.num_games == 6
    assert cfg.max_barriers == 5
    assert cfg.vision_radius == 2
    assert cfg.scoring == {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}
    assert cfg.llm["provider"] == "anthropic"
    assert cfg.mcp["agent_a_port"] == 8101
    assert cfg.reporting["email_enabled"] is False
    assert cfg.swap_at_subgame == 4


def test_rejects_missing_version(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"grid_size": [5, 5]}), encoding="utf-8")

    with pytest.raises(ConfigVersionError, match="missing"):
        Config.from_file(path)


def test_rejects_mismatched_version(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"version": "2.00"}), encoding="utf-8")

    with pytest.raises(ConfigVersionError, match="2.00"):
        Config.from_file(path)


def test_shipped_config_loads() -> None:
    shipped = Path(__file__).resolve().parents[2] / "config" / "config.json"
    cfg = Config.from_file(shipped)
    assert cfg.grid_size == (5, 5)
