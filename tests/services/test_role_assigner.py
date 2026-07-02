"""Tests for RoleAssigner 3/3 swap logic (issue #24)."""

from __future__ import annotations

from copthief.services.role_assigner import RoleAssigner


def test_first_half_a_cop_b_thief() -> None:
    assigner = RoleAssigner()
    assert assigner.roles_for(1) == {"A": "cop", "B": "thief"}
    assert assigner.roles_for(2) == {"A": "cop", "B": "thief"}
    assert assigner.roles_for(3) == {"A": "cop", "B": "thief"}


def test_second_half_swapped() -> None:
    assigner = RoleAssigner()
    assert assigner.roles_for(4) == {"A": "thief", "B": "cop"}
    assert assigner.roles_for(5) == {"A": "thief", "B": "cop"}
    assert assigner.roles_for(6) == {"A": "thief", "B": "cop"}


def test_full_game_each_agent_plays_three_of_each_role() -> None:
    assigner = RoleAssigner()
    counts = {"A": {"cop": 0, "thief": 0}, "B": {"cop": 0, "thief": 0}}
    for i in range(1, 7):
        roles = assigner.roles_for(i)
        counts["A"][roles["A"]] += 1
        counts["B"][roles["B"]] += 1

    assert counts["A"] == {"cop": 3, "thief": 3}
    assert counts["B"] == {"cop": 3, "thief": 3}


def test_custom_swap_point() -> None:
    assigner = RoleAssigner(swap_at_subgame=3)
    assert assigner.roles_for(1) == {"A": "cop", "B": "thief"}
    assert assigner.roles_for(2) == {"A": "cop", "B": "thief"}
    assert assigner.roles_for(3) == {"A": "thief", "B": "cop"}
