"""Centralized API gatekeeper: rate limits, FIFO overflow queue, retries.

All external calls (LLM + MCP) pass through ``ApiGatekeeper.execute`` so the
whole submission shares one policy (PLAN §2.3, ADR-5).
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any


class ApiGatekeeper:
    """Thread-safe gatekeeper with a background worker and FIFO overflow queue.

    ``execute`` enqueues ``call(*a, **k)`` and blocks until the worker reaches
    it, applies rate-limit waits, retries on transient failures, and returns
    the result (or raises the final exception).
    """

    def __init__(
        self,
        rate_limits_config: dict[str, Any],
        *,
        _minute_window_seconds: float = 60.0,
        _hour_window_seconds: float = 3600.0,
    ):
        cfg = rate_limits_config["rate_limits"]["services"]["default"]
        self._rpm = int(cfg["requests_per_minute"])
        self._rph = int(cfg["requests_per_hour"])
        self._retry_after = float(cfg["retry_after_seconds"])
        self._max_retries = int(cfg["max_retries"])
        self._minute_window_seconds = _minute_window_seconds
        self._hour_window_seconds = _hour_window_seconds

        self._lock = threading.Lock()
        self._minute_window: deque[float] = deque()
        self._hour_window: deque[float] = deque()
        self._task_queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any], queue.Queue[Any]]] = queue.Queue()  # noqa: E501
        self._logger = logging.getLogger(__name__)

        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def execute(self, call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Enqueue ``call`` and block until it completes."""
        result_queue: queue.Queue[Any] = queue.Queue(maxsize=1)
        self._task_queue.put((call, args, kwargs, result_queue))
        result = result_queue.get()
        if isinstance(result, BaseException):
            raise result
        return result

    def _run(self) -> None:
        while True:
            call, args, kwargs, result_queue = self._task_queue.get()
            try:
                result = self._execute_guarded(call, args, kwargs)
            except BaseException as exc:  # pragma: no cover - defensive
                result = exc
            result_queue.put(result)

    def _execute_guarded(
        self, call: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        self._wait_for_capacity()
        self._record_call()
        return self._call_with_retries(call, args, kwargs)

    def _wait_for_capacity(self) -> None:
        with self._lock:
            while True:
                now = time.monotonic()
                self._prune_windows(now)
                if len(self._minute_window) < self._rpm and len(self._hour_window) < self._rph:
                    return
                time.sleep(0.05)

    def _prune_windows(self, now: float) -> None:
        while self._minute_window and now - self._minute_window[0] >= self._minute_window_seconds:
            self._minute_window.popleft()
        while self._hour_window and now - self._hour_window[0] >= self._hour_window_seconds:
            self._hour_window.popleft()

    def _record_call(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._minute_window.append(now)
            self._hour_window.append(now)

    def _call_with_retries(
        self, call: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        last_exc: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return call(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                self._logger.warning("Gatekeeper call failed (attempt %d): %s", attempt, exc)
                if attempt < self._max_retries:
                    time.sleep(self._retry_after)
        assert last_exc is not None
        raise last_exc
