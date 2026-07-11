"""Unit tests for validate/score/route without LLM calls."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from confidence.models import FieldConfidence
from confidence.scorer import score_document
from pipeline.state import DocumentState, PdfKind
from pipeline.steps.route import decide_route, route
from pipeline.steps.score import score
from pipeline.steps.validate import validate
from repositories.golden_records import GoldenRecordsRepository
from schemas.records import (
    ConfidenceLevel,
    CorporateEventRecord,
    EventType,
    ExtractionMethod,
    FieldEvidence,
    ValidationResult,
    ValidationStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_CSV = PROJECT_ROOT / "golden_records" / "golden records.csv"


def _evidence(value, method=ExtractionMethod.NATIVE) -> FieldEvidence:
    return FieldEvidence(value=value, snippet=str(value), page=1, method=method)


def _clean_record() -> CorporateEventRecord:
    return CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        cnpj="12.345.678/0001-90",
        isin="US0378331005",  # valid checksum; also match by ticker/cnpj/name
        ticker="TIET3",
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=False,
        data_aprovacao=date(2024, 3, 1),
        data_com=date(2024, 3, 15),
        data_ex=date(2024, 3, 18),
        data_pagamento=date(2024, 4, 10),
        valor_bruto=Decimal("0.50"),
        valor_liquido=Decimal("0.50"),
        aliquota_ir=Decimal("0"),
        moeda="BRL",
        evidencias={
            "emissor": _evidence("Energetica Vale do Tiete S.A."),
            "isin": _evidence("US0378331005"),
            "ticker": _evidence("TIET3"),
            "tipo_evento": _evidence("dividendo"),
            "data_com": _evidence("15/03/2024"),
            "valor_bruto": _evidence("0.50"),
        },
    )


@pytest.fixture
def repository() -> GoldenRecordsRepository:
    return GoldenRecordsRepository(GOLDEN_CSV)


def test_validate_unknown_issuer_fails_golden(repository: GoldenRecordsRepository) -> None:
    record = CorporateEventRecord(
        emissor="Construtora Horizonte S.A.",
        isin="BRCNHZACNOR5",
        ticker="CNHZ3",
        tipo_evento=EventType.DIVIDENDO,
    )
    state = DocumentState(
        document_id="08",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=record,
    )
    out = validate(state, repository=repository)
    golden = next(r for r in out.validation_results if r.rule == "golden_records")
    assert golden.status == ValidationStatus.FAIL


def test_route_unknown_issuer_human_review(repository: GoldenRecordsRepository) -> None:
    record = CorporateEventRecord(
        emissor="Construtora Horizonte S.A.",
        isin="BRCNHZACNOR5",
        ticker="CNHZ3",
        tipo_evento=EventType.DIVIDENDO,
        evidencias={"tipo_evento": _evidence("dividendo")},
    )
    state = DocumentState(
        document_id="08",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=record,
    )
    state = validate(state, repository=repository)
    state = score(state)
    state = route(state)
    assert state.route_decision == "human_review"
    assert any("golden_records" in reason for reason in state.route_reasons)


def test_route_clean_record_auto_approve(repository: GoldenRecordsRepository) -> None:
    # Use known issuer ISIN from golden (checksum may fail for fictional ISINs 
    # match by ticker/cnpj still passes golden; isin_checksum fail is NOT a routing rule).
    record = CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        cnpj="12.345.678/0001-90",
        isin="BRTIETACNOR3",
        ticker="TIET3",
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=False,
        data_aprovacao=date(2024, 3, 1),
        data_com=date(2024, 3, 15),
        data_ex=date(2024, 3, 18),
        data_pagamento=date(2024, 4, 10),
        valor_bruto=Decimal("1.00"),
        valor_liquido=Decimal("1.00"),
        aliquota_ir=Decimal("0"),
        moeda="BRL",
        evidencias={
            "emissor": _evidence("Energetica"),
            "ticker": _evidence("TIET3"),
            "tipo_evento": _evidence("dividendo"),
            "data_com": _evidence("15/03/2024"),
            "valor_bruto": _evidence("1.00"),
            "valor_liquido": _evidence("1.00"),
        },
    )
    state = DocumentState(
        document_id="01",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=record,
    )
    state = validate(state, repository=repository)
    state = score(state)
    state = route(state)
    assert state.route_decision == "auto_approve"


def test_route_date_fail_human_review() -> None:
    state = DocumentState(
        document_id="x",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=_clean_record(),
        validation_results=[
            ValidationResult(
                rule="golden_records",
                status=ValidationStatus.PASS,
                message="ok",
            ),
            ValidationResult(
                rule="date_coherence",
                status=ValidationStatus.FAIL,
                message="bad dates",
            ),
        ],
        field_confidences={
            "tipo_evento": FieldConfidence(
                field="tipo_evento",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
            "data_com": FieldConfidence(
                field="data_com",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
            "valor_bruto": FieldConfidence(
                field="valor_bruto",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
        },
        overall_confidence=0.9,
    )
    decision, reasons = decide_route(state)
    assert decision == "human_review"
    assert any("date_coherence" in r for r in reasons)


def test_route_gross_net_fail_human_review() -> None:
    state = DocumentState(
        document_id="x",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=_clean_record(),
        validation_results=[
            ValidationResult(
                rule="golden_records", status=ValidationStatus.PASS, message="ok"
            ),
            ValidationResult(
                rule="date_coherence", status=ValidationStatus.PASS, message="ok"
            ),
            ValidationResult(
                rule="gross_net_consistency",
                status=ValidationStatus.FAIL,
                message="math fail",
            ),
        ],
        field_confidences={
            "tipo_evento": FieldConfidence(
                field="tipo_evento",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
        },
        overall_confidence=0.9,
    )
    decision, reasons = decide_route(state)
    assert decision == "human_review"
    assert any("gross_net" in r for r in reasons)


def test_route_critical_low_confidence_human_review() -> None:
    state = DocumentState(
        document_id="x",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=_clean_record(),
        validation_results=[
            ValidationResult(
                rule="golden_records", status=ValidationStatus.PASS, message="ok"
            ),
            ValidationResult(
                rule="date_coherence", status=ValidationStatus.PASS, message="ok"
            ),
            ValidationResult(
                rule="gross_net_consistency",
                status=ValidationStatus.PASS,
                message="ok",
            ),
        ],
        field_confidences={
            "tipo_evento": FieldConfidence(
                field="tipo_evento",
                level=ConfidenceLevel.LOW,
                score=0.3,
                justification="low",
            ),
            "data_com": FieldConfidence(
                field="data_com",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
            "valor_bruto": FieldConfidence(
                field="valor_bruto",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
        },
        overall_confidence=0.5,
    )
    decision, reasons = decide_route(state)
    assert decision == "human_review"
    assert any("tipo_evento" in r and "low" in r for r in reasons)


def test_route_ocr_low_overall_human_review() -> None:
    state = DocumentState(
        document_id="x",
        source_path="synthetic",
        pdf_kind=PdfKind.SCANNED,
        record=_clean_record(),
        validation_results=[
            ValidationResult(
                rule="golden_records", status=ValidationStatus.PASS, message="ok"
            ),
        ],
        field_confidences={
            "tipo_evento": FieldConfidence(
                field="tipo_evento",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
            "data_com": FieldConfidence(
                field="data_com",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
            "valor_bruto": FieldConfidence(
                field="valor_bruto",
                level=ConfidenceLevel.HIGH,
                score=0.9,
                justification="ok",
            ),
        },
        overall_confidence=0.70,
    )
    decision, reasons = decide_route(state)
    assert decision == "human_review"
    assert any("0.85" in r or "OCR" in r or "scanned" in r for r in reasons)


def test_divergencia_rebaixa_tipo_evento(repository: GoldenRecordsRepository) -> None:
    record = CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        cnpj="12.345.678/0001-90",
        isin="BRTIETACNOR3",
        ticker="TIET3",
        tipo_evento=EventType.JCP,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=True,
        data_aprovacao=date(2024, 1, 1),
        data_com=date(2024, 1, 10),
        data_ex=date(2024, 1, 11),
        data_pagamento=date(2024, 2, 1),
        valor_bruto=Decimal("0.09215"),
        valor_liquido=Decimal("0.07602375"),
        aliquota_ir=Decimal("0.175"),
        evidencias={
            "tipo_evento": _evidence("jcp"),
            "data_com": _evidence("10/01/2024"),
            "valor_bruto": _evidence("0.09215"),
        },
    )
    state = DocumentState(
        document_id="03",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=record,
    )
    state = validate(state, repository=repository)
    fields, _ = score_document(state)
    assert "tipo_evento" in fields
    assert any(
        "divergencia_titulo_conteudo" in s for s in fields["tipo_evento"].signals
    )
