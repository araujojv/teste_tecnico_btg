"""Tests for isin_checksum validator."""

from __future__ import annotations

from pathlib import Path

from confidence.scorer import score_document
from pipeline.state import DocumentState, PdfKind
from pipeline.steps.score import score
from pipeline.steps.validate import validate
from repositories.golden_records import GoldenRecordsRepository
from schemas.records import (
    ConfidenceLevel,
    CorporateEventRecord,
    ExtractionMethod,
    FieldEvidence,
    ValidationStatus,
)
from validation.rules.isin_checksum import (
    IsinChecksumValidator,
    is_valid_isin,
    isin_check_digit,
)

# Real ISIN (Apple) - golden_records ISINs are fictional and may fail ISO 6166
VALID_ISIN = "US0378331005"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_CSV = PROJECT_ROOT / "golden_records" / "golden records.csv"


def test_known_valid_isin_passes() -> None:
    assert is_valid_isin(VALID_ISIN)
    result = IsinChecksumValidator().validate(CorporateEventRecord(isin=VALID_ISIN))
    assert result.status == ValidationStatus.PASS


def test_check_digit_matches_known_isin() -> None:
    assert isin_check_digit(VALID_ISIN) == VALID_ISIN[11]


def test_fail_adulterated_check_digit_without_golden() -> None:
    bad = VALID_ISIN[:11] + ("0" if VALID_ISIN[11] != "0" else "1")
    assert not is_valid_isin(bad)
    result = IsinChecksumValidator().validate(CorporateEventRecord(isin=bad))
    assert result.status == ValidationStatus.FAIL
    assert result.details is not None
    assert result.details["expected_check_digit"] == isin_check_digit(bad)


def test_warning_missing_isin() -> None:
    result = IsinChecksumValidator().validate(CorporateEventRecord(isin=None))
    assert result.status == ValidationStatus.WARNING


def test_fail_wrong_length() -> None:
    result = IsinChecksumValidator().validate(
        CorporateEventRecord(isin="BRTIETACNOR")
    )
    assert result.status == ValidationStatus.FAIL


def test_fictional_isin_in_golden_is_warning() -> None:
    """Fictional ISIN present in golden_records -> WARNING, not FAIL."""
    repo = GoldenRecordsRepository(GOLDEN_CSV)
    fictional = "BRTIETACNOR3"
    assert not is_valid_isin(fictional)
    assert repo.find_by_isin(fictional) is not None

    result = IsinChecksumValidator(repo).validate(
        CorporateEventRecord(isin=fictional)
    )
    assert result.status == ValidationStatus.WARNING
    assert result.details is not None
    assert result.details.get("confirmed_in_golden_records") is True
    assert "golden_records" in result.message.casefold()


def test_invalid_isin_absent_from_golden_is_fail() -> None:
    repo = GoldenRecordsRepository(GOLDEN_CSV)
    # Valid length, bad check digit, not in golden
    unknown = "BRXXXXACNOR0"
    assert not is_valid_isin(unknown)
    assert repo.find_by_isin(unknown) is None

    result = IsinChecksumValidator(repo).validate(
        CorporateEventRecord(isin=unknown)
    )
    assert result.status == ValidationStatus.FAIL


def test_golden_confirmed_checksum_warning_keeps_isin_confidence_not_low() -> None:
    repo = GoldenRecordsRepository(GOLDEN_CSV)
    record = CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        cnpj="12.345.678/0001-90",
        isin="BRTIETACNOR3",
        ticker="TIET3",
        evidencias={
            "isin": FieldEvidence(
                value="BRTIETACNOR3",
                snippet="ISIN BRTIETACNOR3",
                page=1,
                method=ExtractionMethod.NATIVE,
            ),
        },
    )
    state = DocumentState(
        document_id="01",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        record=record,
    )
    state = validate(state, repository=repo)
    checksum = next(r for r in state.validation_results if r.rule == "isin_checksum")
    assert checksum.status == ValidationStatus.WARNING

    fields, _ = score_document(state)
    assert fields["isin"].level != ConfidenceLevel.LOW
    assert fields["isin"].score >= 0.8
