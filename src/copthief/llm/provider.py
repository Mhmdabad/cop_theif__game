"""LLM provider interface (issue #19).

New providers are added by subclassing ``LLMProvider`` and implementing
``complete()``. The orchestrator selects the implementation via config
(PLAN ADR-2, §9.1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract LLM client wrapper used by the orchestrator."""

    @abstractmethod
    def complete(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> str:
        """Send ``prompt`` to the model and return the text response.

        ``tools`` is an optional list of JSON-Schema tool definitions; providers
        that do not support tool-calling may ignore it.
        """


def create_provider(llm_config: dict[str, Any]) -> LLMProvider:
    """Instantiate the provider named in ``llm_config``.

    Raises:
        ValueError: if the provider name is unknown.
    """
    name = llm_config["provider"]
    model = llm_config["model"]
    temperature = float(llm_config.get("temperature", 0.7))

    if name == "anthropic":
        from copthief.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model, temperature)
    if name == "openai":
        from copthief.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(model, temperature)

    raise ValueError(f"Unknown LLM provider: {name}")
