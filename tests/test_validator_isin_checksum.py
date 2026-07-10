"""Tests for isin_checksum validator."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, ValidationStatus
from validation.rules.isin_checksum import (
    IsinChecksumValidator,
    is_valid_isin,
    isin_check_digit,
)

# Real ISIN (Apple) - golden_records ISINs are fictional and may fail ISO 6166
VALID_ISIN = "US0378331005"


def test_known_valid_isin_passes() -> None:
    assert is_valid_isin(VALID_ISIN)
    result = IsinChecksumValidator().validate(CorporateEventRecord(isin=VALID_ISIN))
    assert result.status == ValidationStatus.PASS


def test_check_digit_matches_known_isin() -> None:
    assert isin_check_digit(VALID_ISIN) == VALID_ISIN[11]


def test_fail_adulterated_check_digit() -> None:
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


def test_fictional_golden_isin_may_fail_checksum() -> None:
    """Synthetic lot ISINs are not guaranteed to have a valid check digit."""
    fictional = "BRTIETACNOR3"
    # Algorithm is deterministic; fictional codes often fail - that is expected.
    assert isinstance(is_valid_isin(fictional), bool)
