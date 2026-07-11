"""Confidence scoring step."""

from __future__ import annotations

from confidence.scorer import score_document
from pipeline.state import DocumentState, append_audit


def score(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: fill field_confidences + overall."""
    fields, overall = score_document(state)
    # Store as serializable dict of FieldConfidence models via model_dump later;
    # DocumentState holds FieldConfidence objects.
    updated = state.model_copy(
        update={
            "field_confidences": fields,
            "overall_confidence": overall,
        }
    )
    low = [name for name, fc in fields.items() if fc.level.value == "low"]
    return append_audit(
        updated,
        (
            f"score: overall={overall:.3f}, fields={len(fields)}, "
            f"low={low or 'none'}"
        ),
    )
