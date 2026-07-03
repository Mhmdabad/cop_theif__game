"""Synchronous bridge over the async FastMCP client.

The orchestrator and ``AgentClient`` are synchronous by design (simple, easy to
test), while ``fastmcp.Client`` is async-only. This adapter runs a private
event loop on a background thread and exposes a blocking ``call_tool``.
``target`` may be an SSE URL (real servers) or a ``FastMCP`` instance
(in-memory, used by the tests).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from fastmcp import Client


class SyncMCPSession:
    """Blocking ``call_tool`` facade over one async MCP client connection."""

    def __init__(self, target: Any, timeout_seconds: float = 60.0):
        self._target = target
        self._timeout = timeout_seconds
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._client: Client | None = None

    def connect(self) -> SyncMCPSession:
        """Start the loop thread and open the MCP connection."""
        self._thread.start()
        self._client = self._run(self._open())
        return self

    async def _open(self) -> Client:
        client = Client(self._target)
        await client.__aenter__()
        return client

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke a server tool and return its deserialized result."""
        if self._client is None:
            raise RuntimeError("SyncMCPSession is not connected")
        result = self._run(self._client.call_tool(name, arguments or {}))
        data = getattr(result, "data", None)
        return data if data is not None else result

    def close(self) -> None:
        """Close the connection and stop the background loop."""
        if self._client is not None:
            self._run(self._client.__aexit__(None, None, None))
            self._client = None
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    def _run(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(self._timeout)

    def __enter__(self) -> SyncMCPSession:
        return self.connect()

    def __exit__(self, *exc_info: Any) -> None:
        self.close()
