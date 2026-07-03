"""Tests for Gmail-API report delivery (issue #30).

All Gmail API interactions are mocked; no real credentials or network calls are
made. credentials.json and token.json are git-ignored as required.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from copthief.reporting.gmail_sender import GmailSender
from copthief.reporting.sinks import GmailReportSink
from copthief.sdk import CopThiefSDK


def _fake_sender(monkeypatch: pytest.MonkeyPatch) -> GmailSender:
    sender = GmailSender("credentials.json", "token.json")
    monkeypatch.setattr(sender, "_load_credentials", lambda: object())
    return sender


def test_send_report_builds_and_sends_message(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = _fake_sender(monkeypatch)
    calls: list[dict[str, Any]] = []

    def fake_build(*_args: object, **_kwargs: object) -> Any:
        class FakeService:
            def users(self) -> FakeService:
                return self

            def messages(self) -> FakeService:
                return self

            def send(self, *, userId: str, body: dict[str, str]) -> FakeService:  # noqa: N803
                calls.append({"userId": userId, "body": body})
                return self

            def execute(self) -> dict[str, Any]:
                return {"id": "msg123"}

        return FakeService()

    monkeypatch.setattr("copthief.reporting.gmail_sender.build", fake_build)

    sender.send_report("instructor@example.com", "Report", json.dumps({"winner": "cop"}))

    assert len(calls) == 1
    assert calls[0]["userId"] == "me"
    raw = calls[0]["body"]["raw"]
    decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
    assert b"instructor@example.com" in decoded
    assert b"Subject: Report" in decoded
    # Assignment §9: the body is ONLY the JSON — no free text, no attachment.
    assert b'{"winner": "cop"}' in decoded
    assert b"attached" not in decoded
    assert b"filename=" not in decoded


def test_send_report_wraps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHttpError(Exception):
        pass

    sender = _fake_sender(monkeypatch)
    monkeypatch.setattr("copthief.reporting.gmail_sender.HttpError", FakeHttpError)

    def failing_service() -> Any:
        raise FakeHttpError("boom")

    monkeypatch.setattr(sender, "_service", failing_service)

    with pytest.raises(RuntimeError, match="Failed to send Gmail report"):
        sender.send_report("instructor@example.com", "Report", "{}")


def test_gmail_report_sink_emails_json(monkeypatch: pytest.MonkeyPatch) -> None:
    sink = GmailReportSink("inst@example.com", "creds.json", "token.json")
    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        sink._sender, "send_report", lambda to, subject, body: calls.append((to, subject, body))
    )

    sink.emit({"group_name": "Team-X"})

    assert len(calls) == 1
    assert calls[0][0] == "inst@example.com"
    assert "CopThief" in calls[0][1]
    assert json.loads(calls[0][2]) == {"group_name": "Team-X"}


def test_sdk_adds_gmail_sink_when_email_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_data = {
        "version": "1.00",
        "grid_size": [2, 2],
        "max_moves": 10,
        "num_games": 2,
        "max_barriers": 0,
        "vision_radius": 2,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        "llm": {"provider": "anthropic", "model": "claude", "temperature": 0.7},
        "mcp": {"agent_a_port": 8101, "agent_b_port": 8102, "host": "127.0.0.1"},
        "roles": {"swap_at_subgame": 2},
        "reporting": {
            "email_enabled": True,
            "instructor_email": "inst@example.com",
            "gmail_credentials_path": "creds.json",
            "gmail_token_path": "token.json",
        },
    }
    from copthief.shared.config import Config

    sdk = CopThiefSDK(Config(config_data))

    assert any(isinstance(s, GmailReportSink) for s in sdk.sinks)
