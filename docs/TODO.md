# TODO — Task Breakdown & Milestones

- **Project:** `cop_theif__game` (Exercise 6 — Dual AI Agent Pursuit via MCP)
- **Version:** 1.00
- **Scope:** Local-only. Bonus/cloud/tunnels/Gmail are **out of scope**.
- **Status legend:** ⬜ not started · 🟨 in progress · ✅ done
- **Owner:** solo (developer) unless noted.
- **Definition of Done (global):** file ≤150 LOC · tests written · `ruff` clean · coverage ≥85% for the module · `uv run` verified.

---

## Phase 0 — Project Scaffolding  (Milestone M0)
- [ ] ⬜ **Init `uv` project**: `pyproject.toml`, `uv.lock`, Python 3.10+ target. *DoD:* `uv sync` succeeds.
- [ ] ⬜ **Package skeleton** `src/copthief/` with `__init__.py` (`__version__`) in every subdir.
- [ ] ⬜ **`.gitignore`** (`.env`, `*.key`, `*.pem`, `results/*.log`) + **`.env-example`** (`ANTHROPIC_API_KEY=`).
- [ ] ⬜ **Tooling config** in `pyproject.toml`: ruff (`E,F,W,I,N,UP,B,C4,SIM`), coverage `fail_under=85`.
- [ ] ⬜ **`shared/version.py`** = `1.00`; **`config/config.json`** + **`rate_limits.json`** (version `1.00`).
- [ ] ⬜ **Dedicated sub-PRDs**: `PRD_game_engine.md`, `PRD_mcp_orchestration.md`, `PRD_q_learning.md`.

## Phase 1 — Game Engine & Rules  (Milestone M1) — *no LLM/MCP yet*
- [ ] ⬜ **`constants.py`**: directions (8-way), agent roles, outcomes.
- [ ] ⬜ **`services/game_engine.py`**: grid state machine, 8-dir movement, bounds checks. *DoD:* moves mutate state; illegal moves rejected.
- [ ] ⬜ **`services/barriers.py`**: place barrier (Cop-only, ≤`max_barriers`), Thief-impassable / Cop-passable. *DoD:* unit-tested passability matrix.
- [ ] ⬜ **Capture + timeout detection**: Cop-on-Thief = capture; 25 moves = Thief win.
- [ ] ⬜ **`services/scoring.py`** `ScoreBook`: per-sub-game scores from config + `totals()`.
- [ ] ⬜ **Tests M1**: happy path + edges (edge/corner moves, barrier blocking, exact capture, timeout). *DoD:* engine coverage ≥85%.

## Phase 2 — Config, SDK, Gatekeeper, LLM Abstraction  (Milestone M2)
- [ ] ⬜ **`shared/config.py`**: load JSON, validate version compatibility, typed accessors (no hard-coded values).
- [ ] ⬜ **`shared/gatekeeper.py`** `ApiGatekeeper`: rate limit from `rate_limits.json`, FIFO overflow queue, retry, logging. *DoD:* integration test proves queue-not-crash on overflow.
- [ ] ⬜ **`llm/provider.py`** `LLMProvider` (ABC) + **`anthropic_provider.py`** (default) + **`openai_provider.py`** (optional). *DoD:* mockable `complete()`.
- [ ] ⬜ **`sdk/sdk.py`** `CopThiefSDK`: `play_sub_game`, `play_game`, `build_report` — single entry point; no logic in GUI/CLI.
- [ ] ⬜ **Tests M2**: config version mismatch, gatekeeper overflow/retry, provider selection (mocked).

## Phase 3 — MCP Servers & Orchestration  (Milestone M3)
- [ ] ⬜ **`mcp/cop_server.py`** & **`mcp/thief_server.py`** (FastMCP): tools `receive_message`, `report_observation`, `propose_action`, `authenticate_location`. *DoD:* both start on configured ports.
- [ ] ⬜ **`mcp/client.py`**: orchestrator-side MCP client wrapper (all calls via gatekeeper).
- [ ] ⬜ **`services/dialogue.py`**: build prompts, parse NL message → intended `Action`; enforce partial observation (`vision_radius`).
- [ ] ⬜ **`services/orchestrator.py`**: turn loop (Thief-first), NL exchange, apply action, technical-loss detection + re-run to keep 6 valid sub-games.
- [ ] ⬜ **Tests M3**: mocked servers/LLM — turn ordering, illegal-intent fallback to heuristic, technical-loss re-run.

## Phase 4 — Full Local Run & Reporting  (Milestone M4)
- [ ] ⬜ **`reporting/game_report.py`**: assemble internal JSON (schema in PLAN §4.3), JSON-only body, write to `results/`.
- [ ] ⬜ **`main.py` CLI**: `uv run copthief --config config/config.json` plays a full game locally.
- [ ] ⬜ **End-to-end integration test**: 6 sub-games (mocked LLM) → valid report + correct totals.
- [ ] ⬜ **Sanity-check ladder** (2×2 → 5×5) runs green.

## Phase 5 — Strategy Layer  (Milestone M5)
- [ ] ⬜ **`agents/strategy.py`** `Strategy` (ABC) + **`agents/heuristic.py`** (Manhattan) as default.
- [ ] ⬜ **`agents/qlearning.py`** (optional): `Q-table` (25×4), Bellman update, ε-greedy — config-selectable.
- [ ] ⬜ **Training routine** + **`notebooks/`**: learning curves, sensitivity analysis (α, γ, ε), heatmaps.
- [ ] ⬜ **Tests M5**: heuristic legality; Q-update math (seeded); strategy selection via config.

## Phase 6 — GUI, Docs, Polish  (Milestone M6)
- [ ] ⬜ **`gui/app.py`**: real-time board, agent moves, barriers (excluded from coverage).
- [ ] ⬜ **`README.md`**: install/usage, config guide, **Dec-POMDP formalism** ⟨n,S,{Aᵢ},P,R,{Ωᵢ},O,γ⟩, orchestration-challenge analysis, screenshots.
- [ ] ⬜ **`docs/prompt_book.md`**: significant prompts, context/goal, iterations.
- [ ] ⬜ **Cost analysis** section: token in/out + $ estimate table (cloud LLM).
- [ ] ⬜ **Final gates**: `ruff check` = 0 · `pytest --cov` ≥85% · all files ≤150 LOC · clean `uv run`.

---

## Cross-Cutting Definition of Done (submission-ready)
- [ ] ⬜ `docs/` has PRD, PLAN, TODO + per-mechanism PRDs.
- [ ] ⬜ README is user-manual grade with Dec-POMDP + screenshots.
- [ ] ⬜ SDK architecture; API gatekeeper on all external calls; no code duplication.
- [ ] ⬜ Config-driven (0 hard-coded values); `.env-example`; no secrets in source.
- [ ] ⬜ `uv` only; `pyproject.toml` + `uv.lock` committed.
- [ ] ⬜ Clean git history; license + third-party attribution.

## Explicitly NOT doing (no-bonus scope)
- [ ] 🚫 Cloud deployment (Prefect Cloud) / public hosting.
- [ ] 🚫 Tunnels / reverse proxy (ngrok, localtonet, Nginx) + public OAuth.
- [ ] 🚫 Inter-group competition game + `bonus_game` JSON report.
- [ ] 🚫 Gmail API email report (write report to local file instead).
