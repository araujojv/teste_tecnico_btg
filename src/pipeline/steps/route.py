"""Routing step: AGENTS.md precedence policy (no silent retry)."""

from __future__ import annotations

from confidence.models import FieldConfidence
from pipeline.state import DocumentState, PdfKind, RouteDecision, append_audit
from schemas.records import ConfidenceLevel, ValidationStatus

# Critical fields for rule 3 (AGENTS: tipo_evento, valor, data_com).
# "valor" maps to valor_bruto (primary economic amount); absent liquido is not blocking.
_CRITICAL_FIELDS = ("tipo_evento", "valor_bruto", "data_com")


def _result_by_rule(state: DocumentState, rule: str):
    for result in state.validation_results:
        if result.rule == rule:
            return result
    return None


def decide_route(
    state: DocumentState,
) -> tuple[RouteDecision, list[str]]:
    """
    Precedence (AGENTS.md):
    1. fail golden_records -> human_review
    2. fail date_coherence or gross_net_consistency -> human_review
    3. critical field confidence low -> human_review
    4. OCR/scanned with overall_confidence < 0.85 -> human_review
    5. else auto_approve
    """
    reasons: list[str] = []

    golden = _result_by_rule(state, "golden_records")
    if golden is not None and golden.status == ValidationStatus.FAIL:
        reasons.append(
            f"fail golden_records: {golden.message}"
        )
        return "human_review", reasons

    dates = _result_by_rule(state, "date_coherence")
    if dates is not None and dates.status == ValidationStatus.FAIL:
        reasons.append(f"fail date_coherence: {dates.message}")
        return "human_review", reasons

    gross_net = _result_by_rule(state, "gross_net_consistency")
    if gross_net is not None and gross_net.status == ValidationStatus.FAIL:
        reasons.append(f"fail gross_net_consistency: {gross_net.message}")
        return "human_review", reasons

    for field in _CRITICAL_FIELDS:
        fc = state.field_confidences.get(field)
        if fc is None:
            continue
        # Absent optional amounts are not a "low extraction" of a critical value.
        if (
            state.record is not None
            and getattr(state.record, field, None) is None
            and field != "tipo_evento"
        ):
            continue
        level = fc.level if isinstance(fc, FieldConfidence) else None
        if level == ConfidenceLevel.LOW:
            reasons.append(
                f"critical field '{field}' confidence=low "
                f"({fc.justification if isinstance(fc, FieldConfidence) else fc})"
            )
            return "human_review", reasons

    is_ocr = state.pdf_kind == PdfKind.SCANNED
    overall = state.overall_confidence
    if is_ocr and overall is not None and overall < 0.85:
        reasons.append(
            f"OCR/scanned document with overall_confidence={overall:.3f} < 0.85"
        )
        return "human_review", reasons

    warnings = [
        r for r in state.validation_results if r.status == ValidationStatus.WARNING
    ]
    if warnings:
        reasons.append(
            "auto_approve with warnings: "
            + ", ".join(f"{w.rule}" for w in warnings)
        )
    else:
        reasons.append("auto_approve: no blocking fails or low critical confidence")
    return "auto_approve", reasons


def route(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: set route_decision + route_reasons."""
    decision, reasons = decide_route(state)
    updated = state.model_copy(
        update={
            "route_decision": decision,
            "route_reasons": reasons,
        }
    )
    return append_audit(
        updated,
        f"route: decision={decision}; reasons={reasons}",
    )
