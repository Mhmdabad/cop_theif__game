"""Tests for randomized starting positions (engine ``random_start``)."""

from __future__ import annotations

from copthief.services.game_engine import GameEngine


def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def test_default_is_fixed_corners() -> None:
    engine = GameEngine((5, 5), max_moves=25)
    assert engine.state.cop_pos == (0, 0)
    assert engine.state.thief_pos == (4, 4)


def test_random_start_respects_min_distance() -> None:
    engine = GameEngine((5, 5), max_moves=25, random_start=True, min_start_distance=3, seed=7)
    for _ in range(20):
        engine.reset()
        state = engine.state
        assert _chebyshev(state.cop_pos, state.thief_pos) >= 3
        for pos in (state.cop_pos, state.thief_pos):
            assert 0 <= pos[0] < 5
            assert 0 <= pos[1] < 5


def test_random_start_is_seed_reproducible() -> None:
    a = GameEngine((5, 5), max_moves=25, random_start=True, seed=42)
    b = GameEngine((5, 5), max_moves=25, random_start=True, seed=42)
    assert a.state == b.state


def test_reset_rerolls_positions() -> None:
    engine = GameEngine((5, 5), max_moves=25, random_start=True, seed=1)
    seen = set()
    for _ in range(10):
        engine.reset()
        seen.add((engine.state.cop_pos, engine.state.thief_pos))
    assert len(seen) > 1  # sub-games are not carbon copies


def test_small_board_clamps_distance_floor() -> None:
    engine = GameEngine((2, 2), max_moves=5, random_start=True, min_start_distance=3, seed=3)
    state = engine.state
    assert state.cop_pos != state.thief_pos  # floor clamps to 1, never overlaps
