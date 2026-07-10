"""Tests for golden_records validator."""

from __future__ import annotations

from repositories.golden_records import GoldenRecordsRepository
from schemas.records import CorporateEventRecord, ValidationStatus
from validation.rules.golden_records import GoldenRecordsValidator


def test_pass_known_issuer(
    repository: GoldenRecordsRepository,
    known_issuer_record: CorporateEventRecord,
) -> None:
    result = GoldenRecordsValidator(repository).validate(known_issuer_record)
    assert result.status == ValidationStatus.PASS
    assert result.rule == "golden_records"
    assert result.details is not None
    assert result.details["ticker"] == "TIET3"


def test_fail_unknown_issuer(
    repository: GoldenRecordsRepository,
    unknown_issuer_record: CorporateEventRecord,
) -> None:
    result = GoldenRecordsValidator(repository).validate(unknown_issuer_record)
    assert result.status == ValidationStatus.FAIL
    assert "not found" in result.message.lower()
