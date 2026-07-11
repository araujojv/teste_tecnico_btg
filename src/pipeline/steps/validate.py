"""Validate step: run deterministic validator chain on CorporateEventRecord."""

from __future__ import annotations

from config.settings import get_settings
from pipeline.state import DocumentState, append_audit
from repositories.golden_records import GoldenRecordsRepository
from validation.base import run_validators
from validation.rules.date_coherence import DateCoherenceValidator
from validation.rules.golden_records import GoldenRecordsValidator
from validation.rules.gross_net_consistency import GrossNetConsistencyValidator
from validation.rules.isin_checksum import IsinChecksumValidator
from validation.rules.type_consistency import TypeConsistencyValidator


def build_default_validators(
    repository: GoldenRecordsRepository | None = None,
) -> list:
    settings = get_settings()
    repo = repository or GoldenRecordsRepository(settings.golden_records_path)
    return [
        GoldenRecordsValidator(repo),
        DateCoherenceValidator(),
        GrossNetConsistencyValidator(),
        IsinChecksumValidator(),
        TypeConsistencyValidator(),
    ]


def validate(
    state: DocumentState,
    *,
    repository: GoldenRecordsRepository | None = None,
) -> DocumentState:
    """(DocumentState) -> DocumentState: attach ValidationResult list."""
    if state.record is None:
        raise ValueError("validate requires state.record")

    validators = build_default_validators(repository)
    results = run_validators(state.record, validators)
    summary = ", ".join(f"{r.rule}={r.status.value}" for r in results)
    updated = state.model_copy(update={"validation_results": results})
    return append_audit(updated, f"validate: {summary}")
