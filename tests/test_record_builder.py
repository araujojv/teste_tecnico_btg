"""Unit tests for record_builder (no LLM)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from confidence.models import FieldConfidence
from output.record_builder import (
    PIPELINE_VERSION,
    build_document_output,
    serialize_value,
    write_document_json,
)
from pipeline.state import DocumentState, PdfKind
from schemas.records import (
    ConfidenceLevel,
    CorporateEventRecord,
    EventType,
    ExtractionMethod,
    FieldEvidence,
    ValidationResult,
    ValidationStatus,
)


def _synthetic_state() -> DocumentState:
    record = CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        isin="BRTIETACNOR3",
        ticker="TIET3",
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="Pagamento de Dividendos",
        divergencia_titulo_conteudo=False,
        data_com=date(2024, 3, 15),
        valor_bruto=Decimal("0.4275"),
        valor_liquido=Decimal("0.4275"),
        moeda="BRL",
        evidencias={
            "emissor": FieldEvidence(
                value="Energetica Vale do Tiete S.A.",
                snippet="Energetica Vale do Tiete",
                page=1,
                method=ExtractionMethod.NATIVE,
            ),
            "valor_bruto": FieldEvidence(
                value=Decimal("0.4275"),
                snippet="R$ 0,4275",
                page=1,
                method=ExtractionMethod.NATIVE,
            ),
        },
    )
    return DocumentState(
        document_id="01_energetica_vale_tiete_dividendo",
        source_path="documents/01_energetica_vale_tiete_dividendo.pdf",
        pdf_kind=PdfKind.NATIVE,
        record=record,
        validation_results=[
            ValidationResult(
                rule="golden_records",
                status=ValidationStatus.PASS,
                message="ok",
            ),
            ValidationResult(
                rule="type_consistency",
                status=ValidationStatus.WARNING,
                message="flag",
                details={"rebaixar_confianca": True},
            ),
        ],
        field_confidences={
            "valor_bruto": FieldConfidence(
                field="valor_bruto",
                level=ConfidenceLevel.HIGH,
                score=0.95,
                justification="native high",
                signals=["extraction_method=native"],
            ),
        },
        overall_confidence=0.9,
        route_decision="auto_approve",
        route_reasons=[],
        audit_trail=["ingest: kind=native", "extract_native: ok"],
    )


def test_serialize_decimal_and_date() -> None:
    assert serialize_value(Decimal("0.4275")) == "0.4275"
    assert serialize_value(date(2024, 3, 15)) == "2024-03-15"
    assert serialize_value(EventType.JCP) == "jcp"


def test_build_document_output_structure() -> None:
    state = _synthetic_state()
    fixed_ts = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_document_output(state, processed_at=fixed_ts)

    assert payload["doc_id"] == "01_energetica_vale_tiete_dividendo"
    assert set(payload.keys()) == {
        "doc_id",
        "processing",
        "record",
        "validation",
        "routing",
        "audit_trail",
    }

    processing = payload["processing"]
    assert processing["pipeline_version"] == PIPELINE_VERSION
    assert processing["timestamp"] == fixed_ts.isoformat()
    assert processing["extraction_method"] == "native"
    assert "extraction" in processing["models"]
    assert processing["overall_confidence"] == 0.9

    valor = payload["record"]["valor_bruto"]
    assert valor["value"] == "0.4275"
    assert isinstance(valor["value"], str)
    assert valor["confidence"]["level"] == "high"
    assert valor["evidence"]["method"] == "native"
    assert valor["evidence"]["snippet"] == "R$ 0,4275"

    assert payload["record"]["data_com"]["value"] == "2024-03-15"
    assert payload["routing"]["decision"] == "auto_approve"
    assert len(payload["validation"]) == 2
    assert payload["validation"][1]["status"] == "warning"
    assert payload["audit_trail"][0].startswith("ingest:")


def test_write_document_json_utf8(tmp_path: Path) -> None:
    state = _synthetic_state()
    # "Siderurgica" with accent via unicode escape (Windows-safe source).
    accented = "Companhia Sider\u00fargica Paranaense S.A."
    state.record = state.record.model_copy(update={"emissor": accented})
    payload = build_document_output(state)
    path = write_document_json(payload, tmp_path / "doc.json")

    raw = path.read_bytes()
    assert "Sider\u00fargica".encode("utf-8") in raw

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["record"]["emissor"]["value"] == accented
    assert loaded["record"]["valor_bruto"]["value"] == "0.4275"
    assert isinstance(loaded["record"]["valor_bruto"]["value"], str)
