# PLAN — Architecture & Technical Design

- **Project:** `cop_theif__game` (Exercise 6 — Dual AI Agent Pursuit via MCP)
- **Version:** 1.00
- **Companion docs:** `PRD.md`, `TODO.md`
- **Scope:** Local-only. No cloud, no tunnels, no bonus competition, no Gmail.

---

## 1. Architecture Decision Records (ADRs)

### ADR-1 — Two independent MCP servers + a central orchestrator
**Decision:** Cop and Thief are each a standalone FastMCP server; a separate **orchestrator**
(MCP client + game engine + LLM client) drives the turn loop.
**Rationale:** Matches the Dec-POMDP model — agents are autonomous and cannot inspect each other.
**Alternatives:** single process with two objects (rejected: no real decentralization);
direct agent-to-agent RPC (rejected: bypasses the natural-language requirement).

### ADR-2 — Cloud LLM API, provider-abstracted (default Anthropic Claude)
**Decision:** Agents "think" via a cloud LLM behind an `LLMProvider` interface; provider/model come
from config. Default provider = **Anthropic Claude** (latest model); OpenAI/Gemini pluggable.
**Rationale:** Simplest and most reliable per assignment §7.1; no local model exposure; runs fully
from the local machine with only outbound HTTPS. **Trade-off:** requires an API key + token-cost
tracking. **Alternatives:** local Ollama (more setup, rejected for this build); heuristic-only
(rejected — loses the LLM natural-language reasoning the exercise showcases).

### ADR-3 — LLM lives in the orchestrator, not the MCP server
**Decision:** MCP servers expose **tools/resources only**; the orchestrator performs LLM Tool-Call
reasoning. **Rationale:** Assignment §5.2 — the model is neither run nor stored inside the server.

### ADR-4 — Free natural-language protocol (no rigid schema between agents)
**Decision:** Inter-agent messages are free text; each agent parses the other's message with its own
LLM. **Rationale:** Assignment core requirement; enables ambiguity, inference, and deception.
**Trade-off:** brittle parsing → mitigated by the orchestrator validating all **moves** against the
engine (illegal/garbled intents fall back to the heuristic).

### ADR-5 — SDK-layered architecture with a centralized API gatekeeper
**Decision:** All business logic behind a single `CopThiefSDK`; all external calls (LLM + MCP) pass a
`ApiGatekeeper` with config-driven rate limits, retries, and an overflow queue.
**Rationale:** Assignment guidelines §4–§5. **Trade-off:** more indirection, justified by testability.

### ADR-6 — Optional Tabular Q-Learning as a pluggable strategy
**Decision:** `Strategy` is an interface; `HeuristicStrategy` (default) and `QLearningStrategy`
(optional, config-selected) both implement it. **Rationale:** Assignment §8 is optional/recommended;
keep it isolated so the core run never depends on it.

---

## 2. C4 Model

### 2.1 Context (Level 1)
```
        +-------------------+        natural-language dialogue
        |   Developer /     |        (driven by orchestrator)
        |   Course Staff    |
        +---------+---------+
                  | runs (CLI/GUI)
                  v
        +-------------------+   outbound HTTPS   +----------------+
        |  Cop/Thief Game   |------------------->|  Cloud LLM API  |
        |   (local system)  |                    | (Claude/OpenAI) |
        +-------------------+                    +----------------+
                  | writes
                  v
        results/game_report.json
```

### 2.2 Container (Level 2)
```
+------------------------------------------------------------------+
|                     Local Machine (localhost)                    |
|                                                                  |
|  +------------------+     MCP (HTTP)     +---------------------+  |
|  |  Cop MCP Server  |<------------------>|                     |  |
|  |  (FastMCP, :8101)|                    |    Orchestrator     |  |
|  +------------------+                    |  (MCP client +      |  |
|                                          |   game engine +     |  |
|  +------------------+     MCP (HTTP)     |   LLM client +      |  |
|  | Thief MCP Server |<------------------>|   gatekeeper + SDK) |  |
|  |  (FastMCP, :8102)|                    |                     |  |
|  +------------------+                    +----------+----------+  |
|                                                     | renders     |
|                                          +----------v----------+  |
|                                          |        GUI          |  |
|                                          +---------------------+  |
+------------------------------------------------------------------+
```

### 2.3 Component (Level 3) — inside the orchestrator
- `sdk/sdk.py` — `CopThiefSDK`: single entry point (`play_game`, `play_sub_game`, `report`).
- `services/orchestrator.py` — turn loop, dialogue sequencing, technical-loss/re-run.
- `services/game_engine.py` — grid state machine, movement, capture, win detection.
- `services/barriers.py` — barrier placement + Thief-impassability rules.
- `services/scoring.py` — per-sub-game and totals scoring.
- `services/dialogue.py` — builds prompts, parses NL messages into intended actions.
- `agents/strategy.py` — `Strategy` interface; `heuristic.py`, `qlearning.py`.
- `mcp/cop_server.py`, `mcp/thief_server.py` — FastMCP servers (tools/resources).
- `mcp/client.py` — MCP client wrapper used by the orchestrator.
- `llm/provider.py` — `LLMProvider` interface; `anthropic_provider.py`, `openai_provider.py`.
- `shared/gatekeeper.py`, `shared/config.py`, `shared/version.py`, `constants.py`.
- `reporting/game_report.py` — builds + writes the internal JSON report.
- `gui/app.py` — real-time board renderer (kept out of coverage).

### 2.4 Code (Level 4)
Class sketches (each file ≤150 LOC; split as they grow):
```
CopThiefSDK          -> play_game(cfg) -> GameReport
Orchestrator         -> run_sub_game() : loops turns until capture/timeout/technical_loss
GameEngine(state)    -> apply_move(agent, action) -> new_state ; is_capture()
BarrierManager       -> place(cell) ; passable(agent, cell)
ScoreBook            -> record(outcome) ; totals()
Strategy(ABC)        -> choose_action(observation, message) -> Action
ApiGatekeeper(cfg)   -> execute(call, *a, **k)  # rate limit + queue + retry + log
LLMProvider(ABC)     -> complete(prompt, tools) -> Response
```

---

## 3. UML — Sub-game Turn Sequence
```
Orchestrator      ThiefServer        LLM          CopServer
     |  observe(thief) |              |               |
     |---------------->|              |               |
     |  thief NL msg   |              |               |
     |<----------------|              |               |
     |  interpret + choose action (cop)               |
     |------------------------------->|               |
     |  cop action (move|barrier)     |               |
     |<-------------------------------|               |
     |  apply to GameEngine ; check capture/timeout   |
     |  render GUI ; append turn to sub_game log      |
     |  (repeat, roles alternate, thief-first)        |
```
Termination: capture (Cop win) → score; 25 moves reached (Thief win) → score;
exception/timeout → mark `technical_loss`, discard, re-run to keep 6 valid sub-games.

---

## 4. Data Schemas & Contracts

### 4.1 `config/config.json` (versioned)
```json
{
  "version": "1.00",
  "grid_size": [5, 5],
  "max_moves": 25,
  "num_games": 6,
  "max_barriers": 5,
  "vision_radius": 2,
  "scoring": { "cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5 },
  "llm": { "provider": "anthropic", "model": "claude-sonnet-5", "temperature": 0.7 },
  "mcp": { "cop_port": 8101, "thief_port": 8102, "host": "127.0.0.1" }
}
```

### 4.2 `config/rate_limits.json` (versioned)
```json
{ "rate_limits": { "version": "1.00",
  "services": { "default": {
    "requests_per_minute": 30, "requests_per_hour": 500,
    "concurrent_max": 5, "retry_after_seconds": 30, "max_retries": 3 } } } }
```

### 4.3 Internal game report (`results/game_report.json`)
```json
{
  "group_name": "Team-<name>",
  "students": [],
  "github_repo": "https://github.com/<user>/cop_theif__game",
  "cop_mcp_url": "http://127.0.0.1:8101",
  "thief_mcp_url": "http://127.0.0.1:8102",
  "timezone": "Asia/Jerusalem",
  "sub_games": [
    { "index": 1, "winner": "cop", "moves": 12, "cop_score": 20, "thief_score": 5 }
  ],
  "totals": { "cop": 0, "thief": 0 }
}
```

### 4.4 MCP tool contracts (per server)
- `receive_message(text: str) -> ack` — deliver opponent's NL message.
- `report_observation() -> str` — agent's partial observation as NL.
- `propose_action() -> str` — agent's NL intent for the turn.
- `authenticate_location(token: str) -> bool` — mutual location handshake (local token).

### 4.5 Strategy contract
`choose_action(observation: Observation, last_message: str) -> Action`
where `Action ∈ {Move(dx,dy), PlaceBarrier()}`, validated by `GameEngine`.

---

## 5. Project Structure (target)
```
cop_theif__game/
├── src/copthief/
│   ├── __init__.py            # __version__, public exports
│   ├── main.py                # CLI entry (uv run copthief)
│   ├── constants.py
│   ├── sdk/sdk.py
│   ├── services/{orchestrator,game_engine,barriers,scoring,dialogue}.py
│   ├── agents/{strategy,heuristic,qlearning}.py
│   ├── mcp/{cop_server,thief_server,client}.py
│   ├── llm/{provider,anthropic_provider,openai_provider}.py
│   ├── reporting/game_report.py
│   ├── gui/app.py
│   └── shared/{gatekeeper,config,version}.py
├── tests/{unit,integration}/  # mirror src/, conftest.py
├── docs/{PRD,PLAN,TODO}.md + PRD_<mechanism>.md + prompt_book.md
├── config/{config.json,rate_limits.json,logging_config.json}
├── results/                   # game_report.json, logs
├── assets/                    # screenshots, diagrams
├── notebooks/                 # Q-Learning curves, sensitivity analysis
├── README.md
├── pyproject.toml + uv.lock
├── .env-example + .gitignore
```

---

## 6. Sanity-Check Ladder (assignment §4.5)
| Stage | Grid | Goal |
|---|---|---|
| 1 | 2×2 | Algorithmic sanity: message pipeline + integration wiring |
| 2 | 3×3 / 3×2 | Coordination convergence; hyper-parameter tuning; failure detection |
| 3 | 4×4 / 4×3 | Partial-observability effect (start distance > `vision_radius`) |
| 4 | 5×5 | Final run; produce graphs + full-game analysis |

---

## 7. Quality Gates & Tooling
- **Package manager:** `uv` only (`uv sync`, `uv run`, `uv add`, `uv lock`).
- **Lint:** `ruff check` → 0 violations (`E,F,W,I,N,UP,B,C4,SIM`).
- **Tests:** `pytest` + `pytest-cov`, `fail_under = 85` (omit `main.py`, `gui/*`).
- **Files:** ≤150 LOC each; split per the strategies in guidelines §3.2.
- **Versioning:** `shared/version.py` and every config JSON start at `1.00`; startup validates config version.
- **Security:** provider key via env; `.env` ignored; `.env-example` committed.
- **Parallelism:** MCP servers run as separate processes; LLM/MCP I/O is I/O-bound (threaded), guarded by the gatekeeper.

---

## 8. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| LLM misparses NL intent | Engine validates all moves; heuristic fallback on invalid/garbled action |
| LLM latency/timeouts stall a game | Gatekeeper retries; on exhaustion → `technical_loss` + re-run |
| Non-determinism breaks tests | Mock LLM/MCP in unit tests; seed Q-Learning; deterministic engine tests |
| Two agents deadlock / no progress | 25-move cap guarantees termination (Thief win on timeout) |
| Token cost creep | Short prompts, cost tracking table in README, cap via gatekeeper |
