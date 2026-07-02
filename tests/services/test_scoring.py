"""Tests for ScoreBook per-sub-game and totals scoring (issue #15)."""

from __future__ import annotations

import pytest

from copthief.constants import Outcome
from copthief.services.scoring import ScoreBook

SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def test_cop_win_scores() -> None:
    book = ScoreBook(SCORING)
    entry = book.record("A", "B", Outcome.COP_WIN)

    assert entry.cop_score == 20
    assert entry.thief_score == 5


def test_thief_win_scores() -> None:
    book = ScoreBook(SCORING)
    entry = book.record("A", "B", Outcome.THIEF_WIN)

    assert entry.cop_score == 5
    assert entry.thief_score == 10


def test_ongoing_outcome_rejected() -> None:
    book = ScoreBook(SCORING)
    with pytest.raises(ValueError, match="non-terminal"):
        book.record("A", "B", Outcome.ONGOING)


def test_totals_accumulate_by_role_and_agent() -> None:
    book = ScoreBook(SCORING)
    book.record("A", "B", Outcome.COP_WIN)
    book.record("B", "A", Outcome.THIEF_WIN)

    totals = book.totals()

    assert totals.by_role == {"cop": 25, "thief": 15}
    assert totals.by_agent == {"agent_a": 30, "agent_b": 10}


def test_totals_snapshot_is_independent() -> None:
    book = ScoreBook(SCORING)
    totals1 = book.totals()
    book.record("A", "B", Outcome.COP_WIN)
    totals2 = book.totals()

    assert totals1.by_role == {"cop": 0, "thief": 0}
    assert totals2.by_role == {"cop": 20, "thief": 5}
