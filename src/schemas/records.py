"""Pydantic schemas for corporate event records and validation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ExtractionMethod(str, Enum):
    NATIVE = "native"
    OCR = "ocr"
    LLM = "llm"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventType(str, Enum):
    DIVIDENDO = "dividendo"
    JCP = "jcp"
    BONIFICACAO = "bonificacao"
    GRUPAMENTO = "grupamento"


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


class FieldEvidence(BaseModel, Generic[T]):
    """Extracted value with auditable evidence (snippet + page + method)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: T | None
    snippet: str | None = None
    page: int | None = None
    method: ExtractionMethod | None = None
    confidence: ConfidenceLevel | None = None


class CorporateEventRecord(BaseModel):
    """Structured record for a corporate event notice."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    emissor: str | None = None
    cnpj: str | None = None
    isin: str | None = None
    ticker: str | None = None

    tipo_evento: EventType | None = None
    tipo_declarado_no_titulo: EventType | None = None
    divergencia_titulo_conteudo: bool = False

    data_aprovacao: date | None = None
    data_com: date | None = None
    data_ex: date | None = None
    data_pagamento: date | None = None
    data_pagamento_ausente_declarada: bool = False

    valor_bruto: Decimal | None = None
    valor_liquido: Decimal | None = None
    aliquota_ir: Decimal | None = None
    moeda: str | None = "BRL"

    evidencias: dict[str, FieldEvidence[Any]] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of a single validation rule."""

    rule: str
    status: ValidationStatus
    message: str
    details: dict[str, Any] | None = None
