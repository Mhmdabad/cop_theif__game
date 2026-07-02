"""Tests for AnthropicProvider (issue #19)."""

from __future__ import annotations

from unittest.mock import MagicMock

from copthief.llm.anthropic_provider import AnthropicProvider


def _make_mock_client(response_text: str) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    content_block = MagicMock()
    content_block.text = response_text
    message.content = [content_block]
    client.messages.create.return_value = message
    return client


def test_complete_returns_response_text() -> None:
    client = _make_mock_client("move north")
    provider = AnthropicProvider("claude-test", client=client)

    result = provider.complete("what is your next move?")

    assert result == "move north"
    client.messages.create.assert_called_once()
    _, kwargs = client.messages.create.call_args
    assert kwargs["model"] == "claude-test"
    assert kwargs["temperature"] == 0.7


def test_complete_passes_tools() -> None:
    client = _make_mock_client("ok")
    provider = AnthropicProvider("claude-test", client=client)
    tools = [{"name": "move"}]

    provider.complete("prompt", tools=tools)

    _, kwargs = client.messages.create.call_args
    assert kwargs["tools"] is tools


def test_custom_temperature() -> None:
    client = _make_mock_client("ok")
    provider = AnthropicProvider("claude-test", temperature=0.0, client=client)
    provider.complete("prompt")

    _, kwargs = client.messages.create.call_args
    assert kwargs["temperature"] == 0.0
