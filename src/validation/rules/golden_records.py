"""Validator: match issuer against golden_records."""

from __future__ import annotations

from repositories.golden_records import GoldenRecordsRepository
from schemas.records import CorporateEventRecord, ValidationResult, ValidationStatus
from validation.base import Validator


class GoldenRecordsValidator(Validator):
    def __init__(self, repository: GoldenRecordsRepository) -> None:
        self._repository = repository

    @property
    def name(self) -> str:
        return "golden_records"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        match = self._repository.match(
            isin=record.isin,
            ticker=record.ticker,
            cnpj=record.cnpj,
            emissor=record.emissor,
        )
        if match is None:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.FAIL,
                message=(
                    "Issuer not found in reference base "
                    f"(isin={record.isin}, ticker={record.ticker}, "
                    f"cnpj={record.cnpj}, emissor={record.emissor})."
                ),
            )
        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.PASS,
            message=f"Match by {match.method.value}: {match.record.emissor}.",
            details={
                "method": match.method.value,
                "score": match.score,
                "emissor": match.record.emissor,
                "isin": match.record.isin,
                "ticker": match.record.ticker,
            },
        )
