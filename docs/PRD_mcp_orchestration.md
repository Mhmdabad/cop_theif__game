# PRD — MCP Orchestration & Natural-Language Dialogue

- **Mechanism:** Two role-capable MCP agent servers + orchestrator dialogue loop.
- **Version:** 1.00 · **Parent:** `PRD.md` §3.3–§3.4 · **Plan:** `PLAN.md` ADR-1/3/4/8, §2–§4
- **Related:** [[PRD_game_engine]], [[PRD_reporting]], [[scope-decisions]]

## 1. Background & Theory
The graded core (assignment §14) is **orchestration**: two autonomous agents that never share memory
coordinate a legal game by exchanging **free natural language**, under **partial observability**
(Dec-POMDP). Each agent is a FastMCP **server** exposing tools/resources; the **LLM is not hosted in the
server** — the orchestrator (MCP client) reads an agent's message, calls the LLM (Tool Call), and applies
the resulting action to the engine.

## 2. Requirements
- **Two servers, one implementation:** a single role-capable `agent_server.py` launched twice
  (Agent-A `:8101`, Agent-B `:8102`), each accepting an assigned role per sub-game.
- **Tools:** `receive_message`, `report_observation`, `propose_action`, `authenticate_location`.
- **Free-text protocol:** messages are prose (intent / partial observation / possible deception); no raw
  coordinates cross the wire; the receiver's LLM interprets them.
- **Partial observability:** an agent sees the opponent only within `vision_radius` (Chebyshev); else it
  infers from dialogue. Observations never expose full ground-truth state.
- **Role swap:** orchestrator's `RoleAssigner` assigns roles per sub-game (1–3 A=cop; 4–6 swap).
- **Gatekeeper:** every LLM/MCP call passes the centralized `ApiGatekeeper`.

## 3. Interface (I/O)
- **Orchestrator input:** engine `GridState` + config. **Per turn:** partial `Observation` + opponent's
  last NL message → LLM → intended `Action` → engine validation.
- **Output:** completed sub-game turn log + outcome, fed to [[PRD_reporting]].
- **Termination handling:** on LLM/MCP failure mark `technical_loss`, discard, re-run to keep 6 valid
  sub-games.

## 4. Performance & Cost
- I/O-bound (network to cloud LLM); threaded, gatekeeper-rate-limited. Prompts kept short to bound token
  cost; token usage tracked for the cost analysis.

## 5. Constraints, Alternatives & Rationale
- **NL parsing is brittle** → mitigated: the engine validates every move; illegal/garbled intent falls
  back to the heuristic. **Alternative** (rigid JSON schema between agents) rejected — violates the free
  natural-language requirement. **Alternative** (single process, two objects) rejected — no real
  decentralization. **Local-only:** servers bind `127.0.0.1`; no tunnels/cloud/OAuth (bonus, out of scope).

## 6. Success Criteria & Test Scenarios
- Both servers start; tools reachable via the client (mocked in unit tests).
- Role assignment + 3/3 swap correct; Thief-first ordering.
- Partial observation respected (no leak beyond `vision_radius`).
- Illegal-intent → heuristic fallback; technical-loss → re-run.
- Orchestration module coverage ≥ 85% with mocked LLM/MCP (no real services).
