"""Training routine for the optional Q-Learning strategy (issue #36).

Trains a cop against a stationary thief on a small grid. The reward is the
negative Manhattan distance to the thief, with a bonus for capture. This keeps
the routine deterministic and reproducible without requiring a full game engine
run per episode.
"""

from __future__ import annotations

from copthief.agents.qlearning import _ACTION_DELTAS, QLearningStrategy
from copthief.constants import Role
from copthief.services.dialogue import Observation


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def train_cop_q_learning(
    grid_size: tuple[int, int],
    thief_pos: tuple[int, int],
    *,
    episodes: int = 500,
    max_steps: int = 50,
    alpha: float = 0.1,
    gamma: float = 0.9,
    epsilon: float = 0.1,
    seed: int = 0,
    capture_bonus: float = 10.0,
) -> tuple[QLearningStrategy, list[float]]:
    """Train a cop ``QLearningStrategy`` to reach a stationary thief.

    Returns the trained strategy and the per-episode total reward history.
    """
    rows, cols = grid_size
    strategy = QLearningStrategy(
        grid_size=grid_size,
        alpha=alpha,
        gamma=gamma,
        epsilon=epsilon,
        seed=seed,
    )
    history: list[float] = []

    for _episode in range(episodes):
        pos: tuple[int, int] = (0, 0)
        total_reward = 0.0

        for step in range(max_steps):
            observation = Observation(
                role=Role.COP,
                my_position=pos,
                opponent_position=thief_pos,
                barriers=set(),
                last_message="",
                move_number=step,
            )
            action_index = strategy.select_action(observation)
            d_row, d_col = _ACTION_DELTAS[action_index]
            next_pos = (pos[0] + d_row, pos[1] + d_col)

            if not (0 <= next_pos[0] < rows and 0 <= next_pos[1] < cols):
                next_pos = pos

            reward = -float(_manhattan(next_pos, thief_pos))
            done = next_pos == thief_pos
            if done:
                reward += capture_bonus

            strategy.update(pos, action_index, reward, next_pos)
            total_reward += reward
            pos = next_pos

            if done:
                break

        history.append(total_reward)

    return strategy, history
