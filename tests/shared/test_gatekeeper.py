"""Integration tests for ApiGatekeeper: queue, retries, logging (issue #18)."""

from __future__ import annotations

import threading
import time

import pytest

from copthief.shared.gatekeeper import ApiGatekeeper

BASE_CFG = {
    "rate_limits": {
        "version": "1.00",
        "services": {
            "default": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "concurrent_max": 5,
                "retry_after_seconds": 0,
                "max_retries": 0,
            }
        },
    }
}


def gatekeeper(
    *, rpm: int = 100, rph: int = 1000, retries: int = 0, window: float = 60.0
) -> ApiGatekeeper:
    cfg = {
        "rate_limits": {
            "version": "1.00",
            "services": {
                "default": {
                    "requests_per_minute": rpm,
                    "requests_per_hour": rph,
                    "concurrent_max": 5,
                    "retry_after_seconds": 0,
                    "max_retries": retries,
                }
            },
        }
    }
    return ApiGatekeeper(cfg, _minute_window_seconds=window, _hour_window_seconds=window * 60)


def test_concurrent_overflow_queued_without_crash() -> None:
    keeper = gatekeeper(rpm=1000)
    counter = 0
    lock = threading.Lock()

    def inc() -> int:
        nonlocal counter
        with lock:
            counter += 1
        return counter

    threads = [threading.Thread(target=lambda: keeper.execute(inc)) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter == 20


def test_rate_limit_delays_overflow() -> None:
    keeper = gatekeeper(rpm=1, window=0.15)
    results: list[float] = []

    def mark() -> None:
        results.append(time.monotonic())

    keeper.execute(mark)
    keeper.execute(mark)

    delta = results[1] - results[0]
    assert delta >= 0.1


def test_retries_until_success(caplog: pytest.LogCaptureFixture) -> None:
    keeper = gatekeeper(retries=2)
    attempts = 0

    def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("transient")
        return "ok"

    assert keeper.execute(flaky) == "ok"
    assert attempts == 3
    assert "transient" in caplog.text


def test_retries_exhausted_raises_last_exception() -> None:
    keeper = gatekeeper(retries=1)

    def always_fails() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        keeper.execute(always_fails)
