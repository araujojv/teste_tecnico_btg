"""Pydantic schema for event-type classification (autoregressive field order)."""

from __future__ import annotations

from schemas.records import EventType
from pydantic import BaseModel, Field


class ClassificationLLMOutput(BaseModel):
    """
    Field ORDER is mandatory (AGENTS.md autoregressivity):
    evidencias_do_documento -> raciocinio -> tipo_declarado_no_titulo
    -> tipo_evento -> divergencia_titulo_conteudo.
    """

    evidencias_do_documento: list[str] = Field(
        description="Literal document snippets that support the classification."
    )
    raciocinio: str = Field(
        description="Reasoning BEFORE choosing tipo_evento."
    )
    tipo_declarado_no_titulo: str | None = Field(
        description="Event type as stated in the title/header, or null."
    )
    tipo_evento: EventType = Field(
        description="Event type inferred from document CONTENT."
    )
    divergencia_titulo_conteudo: bool = Field(
        description="True when title and content indicate different event types."
    )
