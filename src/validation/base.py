"""Validation chain base (Chain of Responsibility)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.records import CorporateEventRecord, ValidationResult


class Validator(ABC):
    """Common interface: each rule returns a ValidationResult."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        ...


def run_validators(
    record: CorporateEventRecord,
    validators: list[Validator],
) -> list[ValidationResult]:
    """Runs the chain in the given order - no short-circuit."""
    return [validator.validate(record) for validator in validators]
