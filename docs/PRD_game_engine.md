# PRD — Game Engine (Grid, Movement, Barriers, Win/Scoring)

- **Mechanism:** Core game engine — the authoritative rules state machine.
- **Version:** 1.00 · **Parent:** `PRD.md` §3.1–§3.2 · **Plan:** `PLAN.md` §2.3, §9.2
- **Related:** [[PRD_mcp_orchestration]] (drives the engine), [[PRD_q_learning]], [[PRD_reporting]]

## 1. Background & Theory
The pursuit is modeled as a **Dec-POMDP** grid world. The engine owns the ground-truth state and is the
single source of legality: every proposed action is validated and either applied (mutating state) or
rejected. It is deliberately free of any LLM/MCP/network concern so it is fully deterministic and unit
-testable. State: agent positions + barrier set + move counter. It is a **state machine** — each move
transitions the board to a new state.

## 2. Requirements
- **Board:** 2-D grid, default 5×5, dimensions read from config (`grid_size`).
- **Movement:** 8-directional (orthogonal + diagonal), one cell per turn; bounds-checked.
- **Turn order:** Thief first, then Cop, alternating within a sub-game.
- **Barriers (Cop-only):** in lieu of a move, place a barrier on the Cop's current cell; ≤ `max_barriers`
  (5) per sub-game; **impassable to the Thief, passable to the Cop**.
- **Termination:** capture (Cop on Thief's exact cell → Cop win); timeout (`max_moves`=25 reached → Thief
  win).
- **Scoring:** from config — cop_win 20 / thief_loss 5; thief_win 10 / cop_loss 5.

## 3. Interface (I/O)
- **Input:** `Action` = `Move(dx, dy)` (dx,dy ∈ {-1,0,1}, not both 0) or `PlaceBarrier()`; current `GridState`.
- **Output:** new `GridState` + outcome flag ∈ {`ongoing`, `cop_win`, `thief_win`}.
- **Setup:** `grid_size`, `max_moves`, `max_barriers`, `scoring.*` (config).
- **Validation:** in-bounds, single-cell step, legal diagonal, barrier quota, correct agent's turn, Thief
  cannot cross a barrier.

## 4. Performance
- O(1) per move; whole sub-game ≤ 25 moves. No I/O. Pure-Python, no external deps.

## 5. Constraints, Alternatives & Rationale
- **Barrier asymmetry** (Cop passes, Thief blocked) is the subtle rule — must be explicit in the
  passability check. **Alternative** (barrier blocks both) rejected: contradicts the spec. **Alternative**
  (barriers as separate objects with lifetimes) rejected: over-engineered for a per-sub-game wall set.

## 6. Success Criteria & Test Scenarios
- Legal/illegal move acceptance; edge and corner clamping; diagonal legality.
- Barrier: Thief blocked, Cop passes; quota exhausted → placement rejected.
- Capture on exact cell; timeout at move 25 → Thief win.
- Scoring totals match the table for both outcomes.
- Engine module coverage ≥ 85%; happy path **and** error cases (guidelines §6).
