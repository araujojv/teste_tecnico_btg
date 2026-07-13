"""Validator: temporal coherence of event dates (ADR-002)."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, ValidationResult, ValidationStatus
from validation.base import Validator


class DateCoherenceValidator(Validator):
    """aprovacao <= data_com < data_ex <= pagamento; declared absence = warning.

    ADR-002: deterministic rule; doc 05 trap (pagamento before com/ex) -> fail.
    """

    @property
    def name(self) -> str:
        return "date_coherence"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        warnings: list[str] = []

        if record.data_pagamento_ausente_declarada:
            if record.data_pagamento is not None:
                return ValidationResult(
                    rule=self.name,
                    status=ValidationStatus.FAIL,
                    message=(
                        "Declared payment-date absence flag is set, "
                        "but data_pagamento is filled."
                    ),
                )
            warnings.append(
                "Payment date declared absent in the document "
                "(e.g. 'sera oportunamente definida')."
            )

        dates = [
            ("data_aprovacao", record.data_aprovacao),
            ("data_com", record.data_com),
            ("data_ex", record.data_ex),
            ("data_pagamento", record.data_pagamento),
        ]
        present = [(name, value) for name, value in dates if value is not None]

        for i in range(len(present) - 1):
            left_name, left_value = present[i]
            right_name, right_value = present[i + 1]
            # data_com < data_ex (strict); others <=
            if left_name == "data_com" and right_name == "data_ex":
                if not (left_value < right_value):
                    return ValidationResult(
                        rule=self.name,
                        status=ValidationStatus.FAIL,
                        message=(
                            f"Date incoherence: {left_name}={left_value} "
                            f"must be < {right_name}={right_value}."
                        ),
                    )
            elif not (left_value <= right_value):
                return ValidationResult(
                    rule=self.name,
                    status=ValidationStatus.FAIL,
                    message=(
                        f"Date incoherence: {left_name}={left_value} "
                        f"must be <= {right_name}={right_value}."
                    ),
                )

        if warnings:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message="; ".join(warnings),
                details={"warnings": warnings},
            )

        if not present:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message="No dates present to validate coherence.",
            )

        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.PASS,
            message="Dates coherent (aprovacao <= data_com < data_ex <= pagamento).",
        )
