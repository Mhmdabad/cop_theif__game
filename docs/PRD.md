# PRD — Dual AI Agent Pursuit (Cop vs. Thief) via MCP Servers

- **Document:** Product Requirements Document
- **Project:** `cop_theif__game` — Exercise 6 (Course: Orchestration of AI Agents)
- **Version:** 1.00
- **Status:** Draft for approval
- **Scope decision:** **Local-only build. No bonus, no inter-group competition, no cloud deployment.**

---

## 1. Overview and Context

### 1.1 Purpose
Design, build, and run an **end-to-end game pipeline** in which **two autonomous AI agents** — the
**Cop** and the **Thief** — play a pursuit game against each other on a 2-D grid. The agents do **not**
share memory or call each other directly. Each agent is a separate **MCP server**; a central
**orchestrator** (MCP client + game engine) drives a turn-based dialogue between them.

The graded value of this project is the **orchestration capability** — standing up two independent
MCP-based agents that communicate in **free natural language** and coordinate a legal game in real
time under **partial observability**. The winning strategy itself is explicitly **not** the deliverable.

### 1.2 The User Problem
Multi-agent systems in the real world are decentralized: each agent is autonomous, sees only part of
the world, and must act in real time while coordinating with (or competing against) other agents
whose internals it cannot inspect. This project is a controlled sandbox for that problem, framed
formally as a **Dec-POMDP** (Decentralized Partially Observable Markov Decision Process).

### 1.3 Target Audience
- **Primary:** Course staff evaluating the submission (and automated grading agents that parse the JSON report).
- **Secondary:** The student/developer, and any future developer reusing the MCP-agent skeleton.

### 1.4 Out of Scope (explicit — this is the "no bonus" boundary)
- Cloud deployment (Prefect Cloud, public cloud hosting).
- Public tunnels / reverse proxies (ngrok, localtonet, Nginx).
- OAuth / public authentication for **exposed MCP endpoints**.
- The **inter-group bonus competition** game and its `bonus_game` JSON report.

> **Note on Gmail:** The **Gmail API email report is *in scope*** — assignment §9 requires the Cop
> agent to email the JSON report to the instructor at the end of a game. It is a **core** requirement,
> independent of the bonus. See §3.7.

---

## 2. Goals, KPIs, and Acceptance Criteria

### 2.1 Measurable Goals
| # | Goal | Success Metric |
|---|------|----------------|
| G1 | Two role-capable MCP agent servers (A, B) run locally | Both start on separate `localhost` ports, expose tools, accept either role |
| G2 | Agents communicate only in natural language | No raw coordinates cross the wire; messages are free text |
| G3 | A full **game** (6 sub-games) runs end-to-end | Orchestrator completes 6 legal sub-games and produces a report |
| G4 | Partial observability enforced | Agents receive observations limited by `vision_radius`, not full state |
| G5 | Deterministic, correct scoring | Totals match the scoring table for every sub-game |
| G6 | Real-time GUI | Board, agent moves, and barriers render live during play |
| G7 | Professional quality bar met | ≥85% coverage, 0 ruff violations, files ≤150 LOC, `uv`-managed |

### 2.2 Acceptance Criteria
- `uv run copthief --config config/config.json` plays a full game locally and writes
  `results/game_report.json` conforming to the internal report schema.
- The report contains per-sub-game results and correct `totals` for `cop` and `thief`.
- A **sanity-check ladder** (grids 2×2 → 5×5) passes without technical failures.
- Any sub-game that ends by **technical failure** (LLM/MCP error) is flagged `technical_loss` and
  re-run so that exactly **6 valid sub-games** are counted.
- README documents the Dec-POMDP formalism and a reproducible local run.

---

## 3. Functional Requirements

### 3.1 Game Rules (authoritative)
- **Board:** 2-D grid, default **5×5**, size read from config. Movement is 8-directional
  (orthogonal **and** diagonal). The board is a **state machine**: every move mutates board state.
- **Sub-game:** one pursuit round, **≤ 25 moves**. Turn-based; the **Thief moves first**, then the
  Cop, repeating. Each turn an agent either **moves one cell** or performs its **special action**.
- **Game:** a sequence of **6 sub-games**; results accumulate and are reported together.
- **Role assignment (local 3/3 swap):** the two agents are **role-capable**, not role-fixed. The
  orchestrator assigns roles per sub-game — **sub-games 1–3: Agent-A = Cop, Agent-B = Thief;
  sub-games 4–6: roles swap** (Agent-B = Cop, Agent-A = Thief). Each agent therefore plays **3 as Cop
  and 3 as Thief**, mirroring the competition's per-team aggregate.
- **Cop win (capture):** the Cop lands on the **exact cell** occupied by the Thief.
- **Thief win (evasion):** the Thief survives all **25 moves** without being caught.
- **Barriers (Cop-only special action):** instead of moving, the Cop places a **barrier** on its
  current cell. That cell becomes **impassable to the Thief** for the rest of the sub-game, but the
  **Cop may still pass through it** (like a wall/edge for the Thief only). Max **5 barriers per
  sub-game**. The Thief cannot place barriers.

### 3.2 Scoring (per sub-game)
| Outcome | Cop score | Thief score |
|---|---|---|
| Cop wins | `scoring.cop_win` (20) | `scoring.thief_loss` (5) |
| Thief wins | `scoring.cop_loss` (5) | `scoring.thief_win` (10) |

With the 3/3 swap, **each agent** plays 3 as Cop + 3 as Thief, so **each agent's aggregate** ranges
max **90** / min **30** points. The report tracks totals **per role** (`cop`/`thief`) *and* **per
agent** (`agent_a`/`agent_b`).

### 3.3 Agents & Communication
- There are **two role-capable agents**, each a standalone **MCP server** built with **FastMCP**
  (same implementation, two instances on separate ports). Each exposes tools for mutual authentication
  of location, sending messages, and receiving them, and accepts a **role** (cop/thief) per sub-game.
- The cop-role agent may place barriers; the thief-role agent may not — the server enables the correct
  action set for the assigned role.
- On each turn an agent produces a **natural-language message** describing its intent, its (partial)
  observation, or a possible **deception** attempt. The receiving agent uses its **LLM** to interpret
  the message, assess the situation, and choose its next action.
- The **LLM is not hosted inside the MCP server**. The orchestrator holds the LLM client, reads the
  agent's message, calls the LLM, and drives the Tool Call → MCP → result loop.

### 3.4 Partial Observability
- Each agent always knows its **own** position.
- It observes the opponent's position **only** when within `vision_radius` (Chebyshev distance);
  otherwise it must **infer** location from the natural-language dialogue.
- This realizes the Dec-POMDP observation function `O`.

### 3.5 Decision Strategy
- **Default:** LLM reasoning over the dialogue, backed by a **Manhattan-distance heuristic** for legal
  move selection.
- **Optional module:** **Tabular Q-Learning** (§8 of the assignment) selectable via config, with a
  training routine and a results-analysis notebook. Strategy quality is **not graded**; this module
  exists for research/visualization depth.

### 3.6 Configuration
All tunable values come from `config/config.json` (no hard-coding): `grid_size`, `max_moves`,
`num_games`, `max_barriers`, `vision_radius`, `scoring.*`, LLM provider/model, and MCP ports.

### 3.7 Reporting
- Emit the **internal game JSON report** (`results/game_report.json`) with: `group_name`, `students`,
  `github_repo`, `agent_a_mcp_url`, `agent_b_mcp_url` (local URLs), `timezone`, `sub_games[]` (each
  recording which agent held the cop/thief role), and `totals` (per role **and** per agent).
- The report body is **JSON only** (no free text) to allow automated grading.
- **Gmail send (assignment §9, required):** at the end of a full game the **agent holding the Cop role
  in the final sub-game** triggers (via the orchestrator) an automatic summary that emails the JSON
  report to the instructor address
  (`rmisegal+uoh26b@gmail.com`) via the **Gmail API**, using **token-based auth** (OAuth client secret
  + stored token) rather than a password.
- The email send is **config-toggleable** (`reporting.email_enabled`): the JSON report is always
  written to `results/` regardless; the email fires only when enabled. This keeps day-to-day local dev
  friction-free (no Google setup needed) while remaining fully §9-compliant when turned on.
- **Technical-loss rule (§9):** any sub-game ended by a technical failure is marked `technical_loss`
  and re-run, so exactly **6 valid** sub-games are reported.

### 3.8 User Interface
- A **GUI** renders the grid, live agent movement, and barriers in real time.
- A **CLI** entry point runs a game/sub-game and prints a turn log.

### 3.9 Non-Functional Requirements
- **Quality:** ≥85% test coverage; 0 `ruff` violations; every file ≤150 LOC; `uv` as the only package
  manager; SDK-layered OOP with no duplication; centralized **API gatekeeper** with config-driven rate
  limits for all LLM/MCP calls.
- **Security:** no secrets in source; `ANTHROPIC_API_KEY` (or provider key) via environment only;
  `.env` git-ignored; `.env-example` committed. Gmail OAuth `credentials.json` and the generated
  `token.json` are git-ignored (never committed).
- **Reliability:** graceful handling of LLM/MCP timeouts; technical-loss detection and re-run.
- **Portability:** runs on Windows (primary dev OS) and Linux via `uv`.
- **Maintainability & Extensibility (§12):** documented extension points — `LLMProvider`, `Strategy`,
  and `ReportSink` are plugin interfaces; new providers/strategies/sinks are added without touching
  core. Building-block modules follow Single Responsibility + Separation of Concerns.
- **Documentation (§3.3):** every module/class/function has a docstring; comments explain the *why*;
  imports are relative / package-qualified (no absolute paths, §14.3); `__init__.py` exposes `__all__`.
- **Usability / UX (§10, Nielsen heuristics):** the GUI targets visibility of system status,
  match to the real world, error prevention, recognition over recall, and aesthetic-minimalist design;
  accessible color palette, clear labels, and screenshots of every state in the README.
- **Standards (§13):** the project is designed against **ISO/IEC 25010** — functional suitability,
  performance efficiency, reliability, security, maintainability, and portability.
- **Concurrency safety (§15):** MCP servers are separate processes; shared orchestrator/gatekeeper
  state is protected with locks and `queue.Queue`; no race conditions or deadlocks.

### 3.10 User Stories
- *As course staff*, I run one command and get a valid JSON report I can grade automatically.
- *As the developer*, I flip a config flag to switch LLM provider or enable Q-Learning without code changes.
- *As a reviewer*, I watch the GUI and see the pursuit unfold move-by-move with barriers.

---

## 4. Assumptions, Dependencies, Constraints

- **Assumptions:** a valid cloud LLM API key is available; the local machine can run two servers +
  orchestrator concurrently.
- **Dependencies:** `fastmcp`, an LLM SDK (`anthropic` default; `openai`/`google-genai` optional),
  a GUI toolkit, `numpy` (Q-Learning), `pytest`/`pytest-cov`, `ruff`, `uv`.
- **Constraints:** Python 3.10+; free-text protocol (no rigid schema between agents); Dec-POMDP partial
  observability must be preserved (agents never receive full ground-truth state).

---

## 5. Timeline & Milestones (see `PLAN.md` / `TODO.md`)
| Milestone | Deliverable |
|---|---|
| M1 | Game engine: rules, movement, barriers, capture, scoring + tests |
| M2 | Config + SDK + gatekeeper + version + LLM provider abstraction |
| M3 | Two FastMCP servers + orchestrator dialogue loop (local) |
| M4 | Full local run of 6 sub-games + JSON report |
| M5 | Strategy layer (heuristic + optional Q-Learning) + notebook |
| M6 | GUI, README (Dec-POMDP), sanity-check ladder, coverage/lint gates |

---

## 6. Dedicated Sub-PRDs (per assignment §2.3)
The following mechanisms each get a dedicated PRD before their implementation:
- `docs/PRD_mcp_orchestration.md` — MCP servers, client, and the natural-language dialogue protocol.
- `docs/PRD_game_engine.md` — grid state machine, movement, barriers, win/scoring logic.
- `docs/PRD_q_learning.md` — optional Tabular Q-Learning (state/action/reward, Bellman update).
- `docs/PRD_reporting.md` — JSON report schema + Gmail-API delivery with token-based auth.
