"""OpenAI implementation of LLMProvider (structured outputs via parse)."""

from __future__ import annotations

from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from config.settings import Settings, get_settings
from llm.provider import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """Uses client.beta.chat.completions.parse with the given model name."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key if api_key is not None else get_settings().openai_api_key
        if not key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")
        self._client = OpenAI(api_key=key)

    def parse(
        self,
        messages: list[dict[str, Any]],
        response_model: type[T],
        *,
        model: str,
    ) -> T:
        completion = self._client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_model,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            refusal = completion.choices[0].message.refusal
            raise RuntimeError(f"OpenAI parse returned no content: {refusal}")
        return parsed


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or get_settings()
    return OpenAIProvider(api_key=cfg.openai_api_key)
