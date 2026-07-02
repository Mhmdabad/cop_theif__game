"""Tests for report delivery sinks (issue #29)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from copthief.reporting.sinks import FileReportSink, ReportSink


def test_file_report_sink_creates_parent_directory(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "game_report.json"
    sink = FileReportSink(output)

    sink.emit({"group_name": "X"})

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == {"group_name": "X"}


def test_file_report_sink_default_path_is_results_game_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    sink = FileReportSink()

    sink.emit({"winner": "cop"})

    assert (tmp_path / "results" / "game_report.json").exists()


def test_report_sink_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        ReportSink()  # type: ignore[abstract]
