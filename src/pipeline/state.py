"""DocumentState - shared pipeline state (pure step functions mutate via copy)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.records import CorporateEventRecord, ValidationResult


class PdfKind(str, Enum):
    NATIVE = "native"
    SCANNED = "scanned"


RouteDecision = Literal["auto_approve", "human_review"]


class DocumentState(BaseModel):
    """Full pipeline state. Later steps fill optional fields."""

    # Identity
    document_id: str
    source_path: str

    # Ingest
    pdf_kind: PdfKind | None = None
    page_count: int = 0
    page_texts: list[str] = Field(default_factory=list)
    full_text: str = ""
    char_density_per_page: list[float] = Field(default_factory=list)
    mean_char_density: float = 0.0
    # Populated only for scanned PDFs (native stays empty - ADR multimodal cost).
    page_images_base64: list[str] = Field(default_factory=list)

    # Extraction / classification
    record: CorporateEventRecord | None = None
    classification_raw: dict[str, Any] | None = None

    # Validation
    validation_results: list[ValidationResult] = Field(default_factory=list)

    # Confidence
    overall_confidence: float | None = None
    field_confidences: dict[str, str] = Field(default_factory=dict)

    # Routing
    route_decision: RouteDecision | None = None
    route_reasons: list[str] = Field(default_factory=list)

    # Append-only audit log
    audit_trail: list[str] = Field(default_factory=list)


def append_audit(state: DocumentState, message: str) -> DocumentState:
    """Return a copy with message appended to audit_trail."""
    return state.model_copy(
        update={"audit_trail": [*state.audit_trail, message]}
    )
