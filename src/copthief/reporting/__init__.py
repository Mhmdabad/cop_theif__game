"""copthief.reporting — JSON game report and delivery sinks (file, Gmail)."""

from __future__ import annotations

from copthief import __version__ as __version__
from copthief.reporting.game_report import GameReport, build_report
from copthief.reporting.sinks import FileReportSink, ReportSink

__all__ = ["__version__", "GameReport", "build_report", "FileReportSink", "ReportSink"]
