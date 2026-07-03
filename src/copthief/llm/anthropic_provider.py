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
            "messages": [{"role": "user", "content": prompt}],
        }
        # Claude 5-family models reject the deprecated `temperature` parameter;
        # only older model families still accept it.
        if not self._model.startswith(("claude-sonnet-5", "claude-fable-5", "claude-mythos-5")):
            kwargs["temperature"] = self._temperature
        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)
        # Claude 5-family models may emit a ThinkingBlock before the text;
        # return the first text block rather than assuming content[0].
        for block in response.content:
            if getattr(block, "type", "") == "text":
                return block.text
        raise ValueError("Anthropic response contained no text block")
