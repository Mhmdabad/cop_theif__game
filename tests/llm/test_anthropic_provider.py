"""Tests for AnthropicProvider (issue #19)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from copthief.llm.anthropic_provider import AnthropicProvider


def _block(block_type: str, text: str | None = None) -> MagicMock:
    block = MagicMock()
    block.type = block_type
    if text is not None:
        block.text = text
    return block


def _make_mock_client(*blocks: MagicMock) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.content = list(blocks)
    client.messages.create.return_value = message
    return client


def test_complete_returns_response_text() -> None:
    client = _make_mock_client(_block("text", "move north"))
    provider = AnthropicProvider("claude-test", client=client)

    result = provider.complete("what is your next move?")

    assert result == "move north"
    client.messages.create.assert_called_once()
    _, kwargs = client.messages.create.call_args
    assert kwargs["model"] == "claude-test"
    assert kwargs["temperature"] == 0.7


def test_complete_skips_thinking_block() -> None:
    # Claude 5-family models emit a ThinkingBlock before the text block.
    client = _make_mock_client(_block("thinking"), _block("text", "move south-east"))
    provider = AnthropicProvider("claude-test", client=client)

    assert provider.complete("your move?") == "move south-east"


def test_complete_raises_when_no_text_block() -> None:
    client = _make_mock_client(_block("thinking"))
    provider = AnthropicProvider("claude-test", client=client)

    with pytest.raises(ValueError, match="no text block"):
        provider.complete("your move?")


def test_claude5_models_omit_deprecated_temperature() -> None:
    client = _make_mock_client(_block("text", "ok"))
    provider = AnthropicProvider("claude-sonnet-5", client=client)
    provider.complete("prompt")

    _, kwargs = client.messages.create.call_args
    assert "temperature" not in kwargs


def test_complete_passes_tools() -> None:
    client = _make_mock_client(_block("text", "ok"))
    provider = AnthropicProvider("claude-test", client=client)
    tools = [{"name": "move"}]

    provider.complete("prompt", tools=tools)

    _, kwargs = client.messages.create.call_args
    assert kwargs["tools"] is tools


def test_custom_temperature() -> None:
    client = _make_mock_client(_block("text", "ok"))
    provider = AnthropicProvider("claude-test", temperature=0.0, client=client)
    provider.complete("prompt")

    _, kwargs = client.messages.create.call_args
    assert kwargs["temperature"] == 0.0
