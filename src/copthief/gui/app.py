"""Real-time GUI board for CopThief (issue #38).

Excluded from coverage by design. Uses tkinter so it has no extra runtime
dependencies and follows Nielsen heuristics: clear status, minimal controls,
and distinct, labelled pieces.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

from copthief.agents.heuristic import HeuristicStrategy
from copthief.constants import Role
from copthief.services.dialogue import Observation
from copthief.services.game_engine import Action, GameEngine


class CopThiefGUI(tk.Tk):
    """Live 2-D grid renderer for a CopThief sub-game."""

    def __init__(
        self,
        grid_size: tuple[int, int] = (5, 5),
        max_moves: int = 25,
        cell_size: int = 60,
        delay_ms: int = 300,
    ) -> None:
        super().__init__()
        self.title("CopThief — Live Board")
        self.grid_dims = grid_size
        self.max_moves = max_moves
        self.cell_size = cell_size
        self.delay_ms = delay_ms

        self.engine = GameEngine(grid_size, max_moves, max_barriers=0)
        self.cop_strategy = HeuristicStrategy(grid_size)
        self.thief_strategy = HeuristicStrategy(grid_size)

        self._build_ui()
        self._draw_board()

    def _build_ui(self) -> None:
        rows, cols = self.grid_dims
        width = cols * self.cell_size
        height = rows * self.cell_size

        self._status = tk.Label(
            self,
            text="Press Start to play",
            font=("Helvetica", 14),
            anchor="w",
        )
        self._status.pack(fill=tk.X, padx=10, pady=5)

        self._canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg="white",
            highlightthickness=1,
            highlightbackground="black",
        )
        self._canvas.pack(padx=10, pady=5)

        control = tk.Frame(self)
        control.pack(fill=tk.X, padx=10, pady=5)

        self._start_btn = tk.Button(control, text="Start", command=self._start)
        self._start_btn.pack(side=tk.LEFT, padx=5)

        self._reset_btn = tk.Button(control, text="Reset", command=self._reset)
        self._reset_btn.pack(side=tk.LEFT, padx=5)

        self._legend = tk.Label(
            control,
            text="Blue = Cop  |  Red = Thief",
            font=("Helvetica", 10),
        )
        self._legend.pack(side=tk.RIGHT, padx=5)

    def _draw_board(self) -> None:
        self._canvas.delete("all")
        rows, cols = self.grid_dims
        size = self.cell_size

        for row in range(rows):
            for col in range(cols):
                x1, y1 = col * size, row * size
                x2, y2 = x1 + size, y1 + size
                self._canvas.create_rectangle(x1, y1, x2, y2, outline="#cccccc")

        for row, col in self.engine.state.barriers:
            x1, y1 = col * size, row * size
            x2, y2 = x1 + size, y1 + size
            self._canvas.create_rectangle(
                x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill="#888888", outline="#888888"
            )

        self._draw_piece(self.engine.state.cop_pos, "#0066cc", "C")
        self._draw_piece(self.engine.state.thief_pos, "#cc0000", "T")

    def _draw_piece(
        self,
        pos: tuple[int, int],
        color: str,
        label: str,
    ) -> None:
        size = self.cell_size
        row, col = pos
        x1, y1 = col * size + 5, row * size + 5
        x2, y2 = x1 + size - 10, y1 + size - 10
        self._canvas.create_oval(x1, y1, x2, y2, fill=color, outline="black", width=2)
        self._canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=label,
            fill="white",
            font=("Helvetica", 12, "bold"),
        )

    def _observation(self, role: Role) -> Observation:
        state = self.engine.state
        if role == Role.COP:
            my_pos, opp_pos = state.cop_pos, state.thief_pos
        else:
            my_pos, opp_pos = state.thief_pos, state.cop_pos
        return Observation(
            role=role,
            my_position=my_pos,
            opponent_position=opp_pos,
            barriers=set(state.barriers),
            last_message="",
            move_number=state.move_number,
        )

    def _choose_action(self, role: Role) -> Action:
        if role == Role.COP:
            return self.cop_strategy.choose_action(self._observation(role), "")
        return self.thief_strategy.choose_action(self._observation(role), "")

    def _start(self) -> None:
        self._reset()
        self._step()

    def _reset(self) -> None:
        self.engine.reset()
        self._status.config(text="Ready — press Start")
        self._draw_board()

    def _step(self) -> None:
        if self.engine.state.outcome.value != "ongoing":
            self._status.config(text=f"Game over: {self.engine.state.outcome.value}")
            return

        role = self.engine.state.turn
        action = self._choose_action(role)
        self.engine.apply_action(role, action)
        self._draw_board()
        self._status.config(
            text=f"Turn {self.engine.state.move_number} — {role.value} moved "
            f"({action.d_row}, {action.d_col})"
        )
        self.after(self.delay_ms, self._step)

    def run(self) -> Any:
        """Start the tkinter main loop."""
        return self.mainloop()


def main() -> None:
    CopThiefGUI().run()


if __name__ == "__main__":
    main()
