"""Tests for barrier placement and asymmetric passability (issue #13)."""

from __future__ import annotations

import pytest

from copthief.constants import Role
from copthief.services.barriers import BarrierManager
from copthief.services.exceptions import IllegalMoveError


def test_barrier_blocks_thief_but_not_cop() -> None:
    manager = BarrierManager(max_barriers=5)
    manager.place((2, 2))

    assert manager.passable(Role.COP, (2, 2)) is True
    assert manager.passable(Role.THIEF, (2, 2)) is False
    assert manager.passable(Role.THIEF, (2, 3)) is True


def test_quota_enforced() -> None:
    manager = BarrierManager(max_barriers=2)
    manager.place((0, 0))
    manager.place((0, 1))

    with pytest.raises(IllegalMoveError, match="quota"):
        manager.place((0, 2))


def test_duplicate_barrier_rejected() -> None:
    manager = BarrierManager(max_barriers=5)
    manager.place((1, 1))

    with pytest.raises(IllegalMoveError, match="already exists"):
        manager.place((1, 1))


def test_clear_removes_all_barriers() -> None:
    manager = BarrierManager(max_barriers=5)
    manager.place((1, 1))
    manager.place((2, 2))

    manager.clear()

    assert manager.barriers == set()
    assert manager.passable(Role.THIEF, (1, 1)) is True
