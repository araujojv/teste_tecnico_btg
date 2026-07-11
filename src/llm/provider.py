"""LLM provider adapter interface (swap providers without touching the pipeline)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Adapter: structured parse against a Pydantic response model."""

    @abstractmethod
    def parse(
        self,
        messages: list[dict[str, Any]],
        response_model: type[T],
        *,
        model: str,
    ) -> T:
        """Return a parsed instance of response_model. Model name is caller-supplied."""
        ...
