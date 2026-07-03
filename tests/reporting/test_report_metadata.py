"""Tests for config-driven report metadata and default sinks."""

from __future__ import annotations

from copthief.reporting.game_report import report_metadata
from copthief.reporting.sinks import FileReportSink, GmailReportSink, default_sinks
from copthief.shared.config import Config

FULL = {
    "version": "1.00",
    "mcp": {"agent_a_port": 8101, "agent_b_port": 8102, "host": "127.0.0.1"},
    "report": {
        "group_name": "Swalha-Abad",
        "students": [{"id": "314932211"}, {"id": "323913764"}],
        "github_repo": "https://github.com/Mhmdabad/cop_theif__game",
        "timezone": "Asia/Jerusalem",
    },
}


def test_metadata_from_report_block() -> None:
    meta = report_metadata(Config(FULL))
    assert meta["group_name"] == "Swalha-Abad"
    assert len(meta["students"]) == 2
    assert meta["github_repo"].endswith("cop_theif__game")
    assert meta["agent_a_mcp_url"] == "http://127.0.0.1:8101"
    assert meta["agent_b_mcp_url"] == "http://127.0.0.1:8102"


def test_metadata_defaults_when_report_block_missing() -> None:
    minimal = {"version": "1.00", "mcp": FULL["mcp"]}
    meta = report_metadata(Config(minimal))
    assert meta["group_name"] == "Team-Local"
    assert meta["students"] == []
    assert meta["timezone"] == "Asia/Jerusalem"


def test_default_sinks_file_only_when_email_disabled() -> None:
    sinks = default_sinks({"email_enabled": False})
    assert len(sinks) == 1
    assert isinstance(sinks[0], FileReportSink)


def test_default_sinks_adds_gmail_when_enabled() -> None:
    sinks = default_sinks({"email_enabled": True, "instructor_email": "me@example.com"})
    assert isinstance(sinks[0], FileReportSink)
    assert isinstance(sinks[1], GmailReportSink)
    assert sinks[1].to_email == "me@example.com"
