"""Tests for OpenAIProvider (issue #21)."""

from __future__ import annotations

from unittest.mock import MagicMock

from copthief.llm.openai_provider import OpenAIProvider


def _make_mock_client(response_text: str) -> MagicMock:
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = response_text
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


def test_complete_returns_response_text() -> None:
    client = _make_mock_client("move north")
    provider = OpenAIProvider("gpt-test", client=client)

    result = provider.complete("what is your next move?")

    assert result == "move north"
    client.chat.completions.create.assert_called_once()
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-test"
    assert kwargs["temperature"] == 0.7


def test_complete_passes_tools() -> None:
    client = _make_mock_client("ok")
    provider = OpenAIProvider("gpt-test", client=client)
    tools = [{"name": "move"}]

    provider.complete("prompt", tools=tools)

    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["tools"] is tools


def test_empty_content_returns_empty_string() -> None:
    client = _make_mock_client("")
    provider = OpenAIProvider("gpt-test", client=client)
    assert provider.complete("prompt") == ""
