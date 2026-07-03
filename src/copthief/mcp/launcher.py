"""MCP-mode launcher: real servers, real dialogue, full game (PRD §3.3).

Spawns the two agent servers as **separate processes** (true decentralization,
PLAN §7), connects sync MCP sessions, and drives the orchestrator — LLM
reasoning, natural-language exchange, role swap, technical-loss re-run — for a
full reported game. Sessions/provider are injectable so tests run without
network or API keys.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from typing import Any

from copthief.llm.provider import LLMProvider, create_provider
from copthief.mcp.client import AgentClient
from copthief.mcp.sync_session import SyncMCPSession
from copthief.reporting.game_report import build_report, report_metadata
from copthief.reporting.sinks import ReportSink, default_sinks
from copthief.services.dialogue import DialogueManager
from copthief.services.game_engine import GameEngine
from copthief.services.orchestrator import Orchestrator
from copthief.services.role_assigner import RoleAssigner
from copthief.services.scoring import ScoreBook
from copthief.shared.config import Config
from copthief.shared.gatekeeper import ApiGatekeeper, default_gatekeeper


def _spawn_server(port: int, role: str) -> subprocess.Popen[bytes]:  # pragma: no cover
    """Start one agent server as a child process."""
    return subprocess.Popen(
        [sys.executable, "-m", "copthief.mcp.agent_server", "--port", str(port), "--role", role]
    )


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:  # pragma: no cover
    """Block until ``host:port`` accepts connections (server is up)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"Agent server on {host}:{port} did not start within {timeout}s")


def run_game(
    config: Config,
    sessions: dict[str, Any],
    provider: LLMProvider | None = None,
    sinks: list[ReportSink] | None = None,
    gatekeeper: ApiGatekeeper | None = None,
) -> dict[str, Any]:
    """Play a full MCP-mode game over already-connected sessions."""
    gatekeeper = gatekeeper or default_gatekeeper()
    mcp_cfg = config.mcp
    urls = {
        "A": f"http://{mcp_cfg['host']}:{mcp_cfg['agent_a_port']}",
        "B": f"http://{mcp_cfg['host']}:{mcp_cfg['agent_b_port']}",
    }
    clients: dict[str, AgentClient] = {}
    for agent in ("A", "B"):
        client = AgentClient(urls[agent], gatekeeper)
        client.set_session(sessions[agent])
        if not client.authenticate_location("local-token"):
            raise RuntimeError(f"Agent {agent} failed location authentication")
        clients[agent] = client

    engine = GameEngine(
        config.grid_size,
        config.max_moves,
        config.max_barriers,
        random_start=config.random_start,
        min_start_distance=config.min_start_distance,
    )
    orchestrator = Orchestrator(
        engine=engine,
        dialogue=DialogueManager(config.vision_radius),
        provider=provider or create_provider(config.llm),
        gatekeeper=gatekeeper,
        clients=clients,
        role_assigner=RoleAssigner(config.swap_at_subgame),
    )

    scorebook = ScoreBook(config.scoring)
    moves_per_game: list[int] = []
    for index in range(1, config.num_games + 1):
        result = orchestrator.run_sub_game(index)
        scorebook.record(result.cop_agent, result.thief_agent, result.outcome)
        moves_per_game.append(result.moves)

    report = build_report(report_metadata(config), scorebook.sub_games, moves_per_game, scorebook)
    data = report.to_dict()
    for sink in sinks if sinks is not None else default_sinks(config.reporting):
        sink.emit(data)
    return data


def launch(config: Config) -> dict[str, Any]:  # pragma: no cover - needs live servers/LLM
    """Spawn both servers, connect real SSE sessions, play, and clean up."""
    mcp_cfg = config.mcp
    host = mcp_cfg["host"]
    ports = {"A": int(mcp_cfg["agent_a_port"]), "B": int(mcp_cfg["agent_b_port"])}
    processes = [_spawn_server(ports["A"], "cop"), _spawn_server(ports["B"], "thief")]
    sessions: dict[str, Any] = {}
    try:
        for agent, port in ports.items():
            _wait_for_port(host, port)
            sessions[agent] = SyncMCPSession(f"http://{host}:{port}/sse").connect()
        return run_game(config, sessions)
    finally:
        for session in sessions.values():
            session.close()
        for process in processes:
            process.terminate()
