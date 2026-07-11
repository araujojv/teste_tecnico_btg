"""Pydantic schema for native extraction LLM structured output (strict)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """Single field value + literal snippet from the document (or both null)."""

    value: str | None = None
    snippet: str | None = None
    # 1-based page index (OCR/vision fills this; native may leave null and use find_page).
    page: int | None = None


class ExtractionLLMOutput(BaseModel):
    """
    LLM extraction payload. Dates/money as strings for strict JSON schema;
    mapper converts to date/Decimal. Never invent values - use null.
    """

    emissor: ExtractedField = Field(default_factory=ExtractedField)
    cnpj: ExtractedField = Field(default_factory=ExtractedField)
    isin: ExtractedField = Field(default_factory=ExtractedField)
    ticker: ExtractedField = Field(default_factory=ExtractedField)
    # One of: dividendo | jcp | bonificacao | grupamento (or null).
    tipo_evento: ExtractedField = Field(default_factory=ExtractedField)
    # Literal wording from title/header (not normalized enum).
    tipo_declarado_no_titulo: ExtractedField = Field(default_factory=ExtractedField)

    data_aprovacao: ExtractedField = Field(default_factory=ExtractedField)
    data_com: ExtractedField = Field(default_factory=ExtractedField)
    data_ex: ExtractedField = Field(default_factory=ExtractedField)
    data_pagamento: ExtractedField = Field(default_factory=ExtractedField)
    data_pagamento_ausente_declarada: bool = False

    valor_bruto: ExtractedField = Field(default_factory=ExtractedField)
    valor_liquido: ExtractedField = Field(default_factory=ExtractedField)
    # Fraction string, e.g. "0.10" for 10% - not "10".
    aliquota_ir: ExtractedField = Field(default_factory=ExtractedField)
    proporcao: ExtractedField = Field(default_factory=ExtractedField)
    moeda: ExtractedField = Field(default_factory=ExtractedField)
