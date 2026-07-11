"""Confidence models (kept separate to avoid import cycles with DocumentState)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.records import ConfidenceLevel


class FieldConfidence(BaseModel):
    """Per-field confidence with human-readable justification."""

    field: str
    level: ConfidenceLevel
    score: float = Field(ge=0.0, le=1.0)
    justification: str
    signals: list[str] = Field(default_factory=list)
