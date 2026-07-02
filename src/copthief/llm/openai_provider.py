"""OpenAI provider (optional)."""

from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "OpenAI provider requires the 'openai' package. "
        "Install it with: uv add openai"
    ) from exc

from copthief.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """LLMProvider backed by the OpenAI Chat Completions API."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        *,
        api_key: str | None = None,
        client: OpenAI | None = None,
    ):
        if client is None:
            key = api_key or os.environ.get("OPENAI_API_KEY")
            client = OpenAI(api_key=key)
        self._client = client
        self._model = model
        self._temperature = temperature

    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            kwargs["tools"] = tools

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
