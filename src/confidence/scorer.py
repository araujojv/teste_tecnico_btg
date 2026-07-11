"""Confidence scoring for extracted fields."""

from __future__ import annotations

from confidence.models import FieldConfidence
from pipeline.state import DocumentState, PdfKind
from schemas.records import (
    ConfidenceLevel,
    ExtractionMethod,
    ValidationResult,
    ValidationStatus,
)

# Validators that touch each field (for signal aggregation).
_FIELD_VALIDATORS: dict[str, set[str]] = {
    "emissor": {"golden_records"},
    "cnpj": {"golden_records"},
    "isin": {"golden_records", "isin_checksum"},
    "ticker": {"golden_records"},
    "tipo_evento": {"type_consistency"},
    "tipo_declarado_no_titulo": {"type_consistency"},
    "data_aprovacao": {"date_coherence"},
    "data_com": {"date_coherence"},
    "data_ex": {"date_coherence"},
    "data_pagamento": {"date_coherence"},
    "valor_bruto": {"gross_net_consistency"},
    "valor_liquido": {"gross_net_consistency"},
    "aliquota_ir": {"gross_net_consistency"},
}

_SCORED_FIELDS = (
    "emissor",
    "cnpj",
    "isin",
    "ticker",
    "tipo_evento",
    "data_aprovacao",
    "data_com",
    "data_ex",
    "data_pagamento",
    "valor_bruto",
    "valor_liquido",
    "aliquota_ir",
    "moeda",
    "proporcao",
)


def _level_from_score(score: float) -> ConfidenceLevel:
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    if score >= 0.55:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _method_base(method: ExtractionMethod | None, pdf_kind: PdfKind | None) -> tuple[float, str]:
    if method == ExtractionMethod.NATIVE or (
        method is None and pdf_kind == PdfKind.NATIVE
    ):
        return 0.9, "extraction_method=native (+0.90 base)"
    if method == ExtractionMethod.OCR or pdf_kind == PdfKind.SCANNED:
        return 0.7, "extraction_method=ocr (+0.70 base)"
    if method == ExtractionMethod.LLM:
        return 0.75, "extraction_method=llm (+0.75 base)"
    return 0.6, "extraction_method=unknown (+0.60 base)"


def _validator_adjustments(
    field: str,
    results: list[ValidationResult],
) -> tuple[float, list[str]]:
    delta = 0.0
    signals: list[str] = []
    relevant = _FIELD_VALIDATORS.get(field, set())
    golden_pass = any(
        r.rule == "golden_records" and r.status == ValidationStatus.PASS
        for r in results
    )
    for result in results:
        if result.rule not in relevant:
            continue
        if result.status == ValidationStatus.PASS:
            delta += 0.05
            signals.append(f"validator:{result.rule}=pass (+0.05)")
        elif result.status == ValidationStatus.WARNING:
            # Fictional ISINs in golden: checksum warning must not drag isin to low.
            confirmed = bool(
                result.details and result.details.get("confirmed_in_golden_records")
            )
            if (
                field == "isin"
                and result.rule == "isin_checksum"
                and (confirmed or golden_pass)
            ):
                signals.append(
                    f"validator:{result.rule}=warning "
                    "(golden confirmed, no penalty)"
                )
            else:
                delta -= 0.2
                signals.append(f"validator:{result.rule}=warning (-0.20)")
        elif result.status == ValidationStatus.FAIL:
            delta -= 0.45
            signals.append(f"validator:{result.rule}=fail (-0.45)")
        elif result.status == ValidationStatus.NOT_APPLICABLE:
            signals.append(f"validator:{result.rule}=n/a (0)")
    return delta, signals


def score_field(
    field: str,
    state: DocumentState,
) -> FieldConfidence:
    record = state.record
    evidence = None
    if record is not None:
        evidence = record.evidencias.get(field)

    method = evidence.method if evidence is not None else None
    score, method_signal = _method_base(method, state.pdf_kind)
    signals = [method_signal]

    if record is not None and getattr(record, field, None) is None:
        # Absent fields are not "low confidence extractions"  mark medium/neutral.
        if field in ("valor_liquido", "aliquota_ir", "proporcao", "cnpj"):
            score = min(score, 0.7)
            signals.append("field_absent (cap 0.70)")

    delta, val_signals = _validator_adjustments(field, state.validation_results)
    score += delta
    signals.extend(val_signals)

    if field == "tipo_evento" and record is not None and record.divergencia_titulo_conteudo:
        score -= 0.25
        signals.append("divergencia_titulo_conteudo=true (-0.25)")

    score = max(0.0, min(1.0, score))
    level = _level_from_score(score)
    justification = (
        f"{field}: level={level.value}, score={score:.2f}. Signals: "
        + "; ".join(signals)
    )
    return FieldConfidence(
        field=field,
        level=level,
        score=score,
        justification=justification,
        signals=signals,
    )


def score_document(state: DocumentState) -> tuple[dict[str, FieldConfidence], float]:
    """Return per-field confidences and overall mean score."""
    fields: dict[str, FieldConfidence] = {}
    for name in _SCORED_FIELDS:
        if state.record is None:
            continue
        # Score fields that exist on the model (value may still be None).
        fields[name] = score_field(name, state)

    if not fields:
        return {}, 0.0
    overall = sum(fc.score for fc in fields.values()) / len(fields)
    return fields, overall
