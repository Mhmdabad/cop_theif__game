"""Report delivery sinks (issue #29).

``ReportSink`` is the abstract delivery contract. ``FileReportSink`` always
writes ``results/game_report.json`` so the assignment artifact exists on every
run, independent of email settings (PLAN ADR-7).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from copthief.reporting.gmail_sender import GmailSender


class ReportSink(ABC):
    """Abstract destination for a completed game report."""

    @abstractmethod
    def emit(self, report: dict[str, Any]) -> None:
        """Deliver ``report`` to the sink's destination."""


class FileReportSink(ReportSink):
    """Persist the report as formatted JSON to disk."""

    def __init__(self, output_path: Path | str | None = None) -> None:
        self.output_path = Path(output_path or "results/game_report.json")

    def emit(self, report: dict[str, Any]) -> None:
        """Write ``report`` to ``output_path``, creating parent dirs if needed."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class GmailReportSink(ReportSink):
    """Email the report to the instructor via the Gmail API."""

    def __init__(
        self,
        to_email: str,
        credentials_path: Path | str = "credentials.json",
        token_path: Path | str = "token.json",
    ) -> None:
        self.to_email = to_email
        self._sender = GmailSender(credentials_path, token_path)

    def emit(self, report: dict[str, Any]) -> None:
        """Send ``report`` as a JSON attachment to the configured instructor."""
        self._sender.send_report(
            self.to_email,
            "CopThief Game Report",
            json.dumps(report, indent=2, ensure_ascii=False),
        )
