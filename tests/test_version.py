"""Tests for version constants and config-version validation (issue #9)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from copthief.shared.version import (
    CODE_VERSION,
    SUPPORTED_CONFIG_VERSION,
    ConfigVersionError,
    validate_config_version,
)

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def test_versions_start_at_one() -> None:
    assert CODE_VERSION == "1.00"
    assert SUPPORTED_CONFIG_VERSION == "1.00"


def test_validate_accepts_top_level_version() -> None:
    assert validate_config_version({"version": "1.00"}) == "1.00"


def test_validate_accepts_nested_rate_limits_version() -> None:
    assert validate_config_version({"rate_limits": {"version": "1.00"}}) == "1.00"


def test_validate_rejects_missing_version() -> None:
    with pytest.raises(ConfigVersionError):
        validate_config_version({})


def test_validate_rejects_mismatched_version() -> None:
    with pytest.raises(ConfigVersionError):
        validate_config_version({"version": "2.00"})


def test_shipped_config_files_load_and_validate() -> None:
    for name in ("config.json", "rate_limits.json"):
        data = json.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))
        assert validate_config_version(data) == SUPPORTED_CONFIG_VERSION
