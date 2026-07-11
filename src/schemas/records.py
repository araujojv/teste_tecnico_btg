"""Pydantic schemas for corporate event records and validation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

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

    value: T | None
    snippet: str | None = None
    page: int | None = None
    method: ExtractionMethod | None = None
    confidence: ConfidenceLevel | None = None


class CorporateEventRecord(BaseModel):
    """Structured record for a corporate event notice."""

    emissor: str | None = None
    cnpj: str | None = None
    isin: str | None = None
    ticker: str | None = None

    tipo_evento: EventType | None = None
    # Free-text as printed on the title (may diverge from tipo_evento).
    tipo_declarado_no_titulo: str | None = None
    # None = classification not run yet; True/False set by classifier.
    divergencia_titulo_conteudo: bool | None = None
    # Classifier reasoning (for type_consistency WARNING message).
    raciocinio_classificacao: str | None = None

    data_aprovacao: date | None = None
    data_com: date | None = None
    data_ex: date | None = None
    data_pagamento: date | None = None
    data_pagamento_ausente_declarada: bool = False

    valor_bruto: Decimal | None = None
    valor_liquido: Decimal | None = None
    # Fraction, not percentage: 0.175 means 17.5% IRRF (e.g. JCP).
    aliquota_ir: Decimal | None = None
    # Ratio for bonificacao/grupamento (e.g. "1:10", "10%"), not a money amount.
    proporcao: str | None = None
    moeda: str | None = None

    evidencias: dict[str, FieldEvidence[Any]] = Field(default_factory=dict)

    @field_validator("evidencias")
    @classmethod
    def evidencias_keys_must_be_model_fields(
        cls, value: dict[str, FieldEvidence[Any]]
    ) -> dict[str, FieldEvidence[Any]]:
        allowed = set(cls.model_fields)
        invalid = sorted(key for key in value if key not in allowed)
        if invalid:
            raise ValueError(
                "evidencias keys must be CorporateEventRecord field names; "
                f"invalid: {invalid}"
            )
        return value


class ValidationResult(BaseModel):
    """Result of a single validation rule."""

    rule: str
    status: ValidationStatus
    message: str
    details: dict[str, Any] | None = None
