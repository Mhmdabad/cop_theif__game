"""Tests for the config accessors added with MCP mode (report, random start)."""

from __future__ import annotations

from copthief.shared.config import Config


def test_random_start_and_distance_defaults() -> None:
    config = Config({"version": "1.00"})
    assert config.random_start is False
    assert config.min_start_distance == 3
    assert config.report == {}


def test_random_start_and_report_from_data() -> None:
    config = Config(
        {
            "version": "1.00",
            "random_start": True,
            "min_start_distance": 2,
            "report": {"group_name": "Swalha-Abad"},
        }
    )
    assert config.random_start is True
    assert config.min_start_distance == 2
    assert config.report["group_name"] == "Swalha-Abad"
