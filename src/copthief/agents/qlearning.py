"""Optional tabular Q-Learning strategy (issue #35).

The state space is the agent's own cell (``rows * cols``), and the action space
is the four orthogonal moves. ``QLearningStrategy`` can be selected from config
but the default run never depends on it (PRD §3.5; guidelines §8).
"""

from __future__ import annotations

import random

from copthief.agents.strategy import Strategy
from copthief.constants import ActionType
from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action

# Up, down, left, right.
_ACTION_DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class QLearningStrategy(Strategy):
    """Tabular Q-Learning policy with epsilon-greedy action selection."""

    def __init__(
        self,
        grid_size: tuple[int, int],
        *,
        alpha: float = 0.1,
        gamma: float = 0.9,
        epsilon: float = 0.1,
        seed: int | None = None,
        q_table: list[list[float]] | None = None,
    ) -> None:
        self.grid_size = grid_size
        self.rows, self.cols = grid_size
        self.n_states = self.rows * self.cols
        self.n_actions = 4
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        if q_table is not None:
            self.q = [list(row) for row in q_table]
        else:
            self.q = [[0.0 for _ in range(self.n_actions)] for _ in range(self.n_states)]

    def _state_index(self, pos: tuple[int, int]) -> int:
        return pos[0] * self.cols + pos[1]

    def _legal_actions(self, pos: tuple[int, int]) -> list[int]:
        return [
            i
            for i, (d_row, d_col) in enumerate(_ACTION_DELTAS)
            if 0 <= pos[0] + d_row < self.rows and 0 <= pos[1] + d_col < self.cols
        ]

    def select_action(self, observation: Observation) -> int:
        """Epsilon-greedy selection returning the action index."""
        pos = observation.my_position
        legal = self._legal_actions(pos)
        state = self._state_index(pos)

        if self.rng.random() < self.epsilon:
            return self.rng.choice(legal)

        best_value = max(self.q[state][i] for i in legal)
        best_actions = [i for i in legal if self.q[state][i] == best_value]
        return self.rng.choice(best_actions)

    def choose_action(self, observation: Observation, last_message: str) -> Action:
        """Epsilon-greedy selection over the four orthogonal moves."""
        action_index = self.select_action(observation)
        d_row, d_col = _ACTION_DELTAS[action_index]
        return Action(ActionType.MOVE, d_row, d_col)

    def update(
        self,
        position: tuple[int, int],
        action_index: int,
        reward: float,
        next_position: tuple[int, int],
    ) -> None:
        """Apply one Bellman update to ``Q[position, action_index]``."""
        state = self._state_index(position)
        next_state = self._state_index(next_position)
        max_next = max(self.q[next_state]) if self.q[next_state] else 0.0
        td_target = reward + self.gamma * max_next
        self.q[state][action_index] += self.alpha * (td_target - self.q[state][action_index])
