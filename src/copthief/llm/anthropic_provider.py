"""Anthropic Claude provider (default)."""

from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic

from copthief.llm.provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """LLMProvider backed by Anthropic's Messages API."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        *,
        api_key: str | None = None,
        client: Anthropic | None = None,
    ):
        if client is None:
            key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            client = Anthropic(api_key=key)
        self._client = client
        self._model = model
        self._temperature = temperature

    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 1024,
            "temperature": self._temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)
        return response.content[0].text
