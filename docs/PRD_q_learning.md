# PRD — Optional Tabular Q-Learning Strategy

- **Mechanism:** Optional reinforcement-learning move strategy (assignment §8).
- **Version:** 1.00 · **Parent:** `PRD.md` §3.5 · **Plan:** `PLAN.md` ADR-6, §9.1
- **Status:** **Optional / recommended** — the core run must never depend on it.
- **Related:** [[PRD_game_engine]], [[PRD_mcp_orchestration]]

## 1. Background & Theory
Reinforcement learning lets an agent improve its policy through interaction, without heavy compute or
deep-learning libraries. **Tabular Q-Learning** stores an action-value table `Q(s, a)` and updates it via
the **Bellman equation**:

```
Q(s, a) ← Q(s, a) + α · [ r + γ · max_a' Q(s', a') − Q(s, a) ]
```

- **State `s`** — the agent's grid cell (25 states for 5×5). **Action `a`** — one of 4/8 moves.
- **Reward `r`** — outcome-shaped (e.g. capture/evasion payoff, small step penalty).
- **α** learning rate (≈0.01–0.5); **γ** discount (0–1); **ε-greedy** explore/exploit.

## 2. Requirements
- `QLearningStrategy` implements the shared `Strategy` interface (`choose_action`).
- Q-table sized from `grid_size` (states) × action count; hyper-parameters (`α`, `γ`, `ε`) from config.
- Selectable via config; when unselected, the heuristic strategy is used and this module is never imported
  by the core game path.
- A training routine runs episodes and persists/loads the learned table.

## 3. Interface (I/O)
- **Input:** `Observation` (state) + last NL message. **Output:** a legal `Action` (engine-validated).
- **Training I/O:** episodes → updated Q-table; artifacts for the analysis notebook.
- **Setup:** `learning_rate`, `discount_factor`, `epsilon`, `episodes`, seed.

## 4. Performance
- Update is O(1) per step; table is small (e.g. 25×4). No neural nets, no GPU, negligible memory.

## 5. Constraints, Alternatives & Rationale
- Strategy quality is **not graded** (assignment §14) — this exists for research/visualization depth.
  **Alternatives:** heuristics / Manhattan distance / decision trees / direct LLM prompting are all
  acceptable; deep RL rejected as unnecessary and heavyweight for a 5×5 grid.

## 6. Success Criteria & Test Scenarios
- Bellman update matches a hand-computed value on a seeded example.
- ε-greedy selection is legal and reproducible under a fixed seed.
- Strategy selection via config routes to Q-learning vs heuristic correctly.
- Learning curves show non-decreasing performance across episodes (notebook).
- Module coverage ≥ 85%.
