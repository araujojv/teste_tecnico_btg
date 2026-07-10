"""Validator: ISIN check digit (ISO 6166 / Luhn)."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, ValidationResult, ValidationStatus
from validation.base import Validator


def isin_check_digit(isin12: str) -> str:
    """Compute check digit for the first 11 characters of an ISIN."""
    body = isin12[:11].upper()
    digits: list[int] = []
    for char in body:
        if char.isdigit():
            digits.append(int(char))
        elif char.isalpha():
            # A=10 ... Z=35
            value = ord(char) - ord("A") + 10
            digits.extend(int(d) for d in str(value))
        else:
            raise ValueError(f"Invalid character in ISIN: {char!r}")

    # Luhn: from the right, double every other position
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:
            doubled = digit * 2
            total += doubled // 10 + doubled % 10
        else:
            total += digit
    return str((10 - (total % 10)) % 10)


def is_valid_isin(isin: str) -> bool:
    cleaned = isin.strip().upper()
    if len(cleaned) != 12:
        return False
    if not cleaned[:2].isalpha():
        return False
    if not cleaned[2:].isalnum():
        return False
    try:
        return cleaned[11] == isin_check_digit(cleaned)
    except ValueError:
        return False


class IsinChecksumValidator(Validator):
    @property
    def name(self) -> str:
        return "isin_checksum"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        if not record.isin:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message="ISIN missing - checksum not verified.",
            )

        isin = record.isin.strip().upper()
        if len(isin) != 12:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.FAIL,
                message=f"ISIN with invalid length ({len(isin)}): {isin}.",
            )

        if is_valid_isin(isin):
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.PASS,
                message=f"Valid ISIN checksum: {isin}.",
            )

        expected = isin_check_digit(isin)
        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.FAIL,
            message=(
                f"Invalid ISIN checksum: {isin} "
                f"(digit={isin[11]}, expected={expected})."
            ),
            details={"isin": isin, "expected_check_digit": expected},
        )
