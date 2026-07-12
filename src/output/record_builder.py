"""Build final per-document JSON from DocumentState."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from config.settings import Settings, get_settings
from pipeline.state import DocumentState, PdfKind
from schemas.records import CorporateEventRecord, ExtractionMethod

PIPELINE_VERSION = "0.1.0"

# Business fields exposed in the output record (value + confidence + evidence).
_OUTPUT_FIELDS: tuple[str, ...] = (
    "emissor",
    "cnpj",
    "isin",
    "ticker",
    "tipo_evento",
    "tipo_declarado_no_titulo",
    "divergencia_titulo_conteudo",
    "raciocinio_classificacao",
    "data_aprovacao",
    "data_com",
    "data_ex",
    "data_pagamento",
    "data_pagamento_ausente_declarada",
    "valor_bruto",
    "valor_liquido",
    "aliquota_ir",
    "proporcao",
    "moeda",
)


def serialize_value(value: Any) -> Any:
    """JSON-safe value: Decimal as string, dates ISO, enums as value."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def _extraction_method(state: DocumentState) -> str:
    if state.pdf_kind == PdfKind.SCANNED:
        return ExtractionMethod.OCR.value
    if state.pdf_kind == PdfKind.NATIVE:
        return ExtractionMethod.NATIVE.value
    record = state.record
    if record is not None:
        for evidence in record.evidencias.values():
            if evidence.method is not None:
                return evidence.method.value
    return "unknown"


def _field_block(
    name: str,
    record: CorporateEventRecord,
    state: DocumentState,
) -> dict[str, Any]:
    raw = getattr(record, name)
    evidence = record.evidencias.get(name)
    confidence = state.field_confidences.get(name)
    return {
        "value": serialize_value(raw),
        "confidence": (
            {
                "level": confidence.level.value,
                "score": confidence.score,
                "justification": confidence.justification,
                "signals": list(confidence.signals),
            }
            if confidence is not None
            else None
        ),
        "evidence": (
            {
                "snippet": evidence.snippet,
                "page": evidence.page,
                "method": (
                    evidence.method.value if evidence.method is not None else None
                ),
            }
            if evidence is not None
            else None
        ),
    }


def build_document_output(
    state: DocumentState,
    settings: Settings | None = None,
    *,
    processed_at: datetime | None = None,
) -> dict[str, Any]:
    """
    Assemble the final JSON payload for one document.

    Shape: doc_id, processing, record, validation, routing, audit_trail.
    """
    cfg = settings or get_settings()
    ts = processed_at or datetime.now(timezone.utc)
    record = state.record

    record_payload: dict[str, Any] = {}
    if record is not None:
        for name in _OUTPUT_FIELDS:
            record_payload[name] = _field_block(name, record, state)

    validation = [
        {
            "rule": result.rule,
            "status": result.status.value,
            "message": result.message,
            "details": result.details,
        }
        for result in state.validation_results
    ]

    return {
        "doc_id": state.document_id,
        "processing": {
            "timestamp": ts.isoformat(),
            "pipeline_version": PIPELINE_VERSION,
            "source_path": state.source_path,
            "pdf_kind": state.pdf_kind.value if state.pdf_kind else None,
            "extraction_method": _extraction_method(state),
            "models": {
                "extraction": cfg.extraction_model,
                "classification": cfg.classification_model,
                "vision": cfg.vision_model,
            },
            "overall_confidence": state.overall_confidence,
        },
        "record": record_payload,
        "validation": validation,
        "routing": {
            "decision": state.route_decision,
            "reasons": list(state.route_reasons),
        },
        "audit_trail": list(state.audit_trail),
    }


def write_document_json(
    payload: dict[str, Any],
    path: Path | str,
) -> Path:
    """Write payload as UTF-8 JSON (Decimal already stringified)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    return out
