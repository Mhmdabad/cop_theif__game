"""Generate UI state screenshots for documentation (issue #39).

This script draws the same board states the tkinter GUI would show, but uses
matplotlib so it can run headless and produce committed assets.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
GRID_SIZE = (5, 5)
CELL_SIZE = 1.0


def _draw_state(
    cop_pos: tuple[int, int],
    thief_pos: tuple[int, int],
    barriers: set[tuple[int, int]],
    status: str,
    output: Path,
) -> None:
    rows, cols = GRID_SIZE
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(0, cols * CELL_SIZE)
    ax.set_ylim(0, rows * CELL_SIZE)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")

    for row in range(rows):
        for col in range(cols):
            rect = patches.Rectangle(
                (col * CELL_SIZE, row * CELL_SIZE),
                CELL_SIZE,
                CELL_SIZE,
                linewidth=1,
                edgecolor="#cccccc",
                facecolor="white",
            )
            ax.add_patch(rect)

    for row, col in barriers:
        barrier = patches.Rectangle(
            (col * CELL_SIZE + 0.05, row * CELL_SIZE + 0.05),
            CELL_SIZE - 0.1,
            CELL_SIZE - 0.1,
            facecolor="#888888",
            edgecolor="#888888",
        )
        ax.add_patch(barrier)

    def _piece(pos: tuple[int, int], color: str, label: str) -> None:
        row, col = pos
        circle = patches.Circle(
            (col * CELL_SIZE + CELL_SIZE / 2, row * CELL_SIZE + CELL_SIZE / 2),
            0.35,
            facecolor=color,
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(circle)
        ax.text(
            col * CELL_SIZE + CELL_SIZE / 2,
            row * CELL_SIZE + CELL_SIZE / 2,
            label,
            ha="center",
            va="center",
            color="white",
            fontsize=12,
            weight="bold",
        )

    _piece(cop_pos, "#0066cc", "C")
    _piece(thief_pos, "#cc0000", "T")

    ax.set_title(status, fontsize=12, pad=10)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)

    states = [
        ("start", (0, 0), (4, 4), set(), "Start of sub-game"),
        ("mid_pursuit", (2, 2), (3, 4), set(), "Mid-pursuit"),
        ("barrier_placed", (2, 2), (3, 4), {(2, 2)}, "Cop placed a barrier"),
        ("capture", (3, 4), (3, 4), set(), "Cop captures Thief"),
        ("timeout", (1, 1), (4, 4), set(), "Timeout — Thief wins"),
    ]

    for name, cop, thief, barriers, status in states:
        _draw_state(cop, thief, barriers, status, ASSETS_DIR / f"{name}.png")
        print(f"Wrote {ASSETS_DIR / f'{name}.png'}")


if __name__ == "__main__":
    main()
