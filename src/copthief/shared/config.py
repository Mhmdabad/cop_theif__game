"""Typed config loader with version validation (issue #17).

All tunables are read from ``config/config.json``; no game constants are
hard-coded outside this module's accessors (guidelines §7.2).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from copthief.shared.version import validate_config_version


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable view over the validated JSON configuration."""

    _data: dict[str, Any]

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        """Load ``path`` as JSON and validate its schema version."""
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        validate_config_version(data)
        return cls(data)

    @property
    def grid_size(self) -> tuple[int, int]:
        return tuple(self._data["grid_size"])  # type: ignore[return-value]

    @property
    def max_moves(self) -> int:
        return int(self._data["max_moves"])

    @property
    def num_games(self) -> int:
        return int(self._data["num_games"])

    @property
    def max_barriers(self) -> int:
        return int(self._data["max_barriers"])

    @property
    def vision_radius(self) -> int:
        return int(self._data["vision_radius"])

    @property
    def scoring(self) -> dict[str, int]:
        return {k: int(v) for k, v in self._data["scoring"].items()}

    @property
    def llm(self) -> dict[str, Any]:
        return dict(self._data["llm"])

    @property
    def mcp(self) -> dict[str, Any]:
        return dict(self._data["mcp"])

    @property
    def reporting(self) -> dict[str, Any]:
        return dict(self._data["reporting"])

    @property
    def swap_at_subgame(self) -> int:
        return int(self._data["roles"]["swap_at_subgame"])
