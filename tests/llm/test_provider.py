"""Tests for LLMProvider interface and factory (issue #19)."""

from __future__ import annotations

import pytest

from copthief.llm.provider import LLMProvider, create_provider


class FakeProvider(LLMProvider):
    def complete(self, prompt, tools=None):  # noqa: ANN001, ANN202
        return "fake"


def test_llm_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_create_provider_returns_anthropic() -> None:
    provider = create_provider({"provider": "anthropic", "model": "claude", "temperature": 0.5})
    assert provider.__class__.__name__ == "AnthropicProvider"


def test_create_provider_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_provider({"provider": "unknown", "model": "x"})


def test_create_provider_openai_returns_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = create_provider({"provider": "openai", "model": "gpt"})
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_subclass_can_complete() -> None:
    assert FakeProvider().complete("hi") == "fake"
