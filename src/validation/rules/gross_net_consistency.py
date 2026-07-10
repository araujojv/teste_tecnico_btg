"""Validator: bruto * (1 - aliquota) ~= liquido consistency."""

from __future__ import annotations

from decimal import Decimal

from schemas.records import (
    CorporateEventRecord,
    EventType,
    ValidationResult,
    ValidationStatus,
)
from validation.base import Validator

# Rounding tolerance (ADR: Decimal, never float)
_TOLERANCE = Decimal("0.00000001")

_NA_TYPES = {EventType.GRUPAMENTO, EventType.BONIFICACAO}


class GrossNetConsistencyValidator(Validator):
    @property
    def name(self) -> str:
        return "gross_net_consistency"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        if record.tipo_evento in _NA_TYPES:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.NOT_APPLICABLE,
                message=(
                    f"Rule not applicable for tipo_evento={record.tipo_evento}."
                ),
            )

        missing = [
            name
            for name, value in (
                ("valor_bruto", record.valor_bruto),
                ("valor_liquido", record.valor_liquido),
                ("aliquota_ir", record.aliquota_ir),
            )
            if value is None
        ]
        if missing:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message=(
                    "Missing fields for gross/net check: "
                    + ", ".join(missing)
                    + "."
                ),
                details={"missing_fields": missing},
            )

        assert record.valor_bruto is not None
        assert record.valor_liquido is not None
        assert record.aliquota_ir is not None

        expected = record.valor_bruto * (Decimal("1") - record.aliquota_ir)
        diff = abs(expected - record.valor_liquido)
        if diff > _TOLERANCE:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.FAIL,
                message=(
                    f"Gross/net inconsistency: expected {expected}, "
                    f"got {record.valor_liquido} (diff={diff})."
                ),
                details={
                    "valor_bruto": str(record.valor_bruto),
                    "aliquota_ir": str(record.aliquota_ir),
                    "valor_liquido": str(record.valor_liquido),
                    "esperado": str(expected),
                    "diff": str(diff),
                },
            )

        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.PASS,
            message=f"bruto * (1 - aliquota) ~= liquido (esperado={expected}).",
            details={"esperado": str(expected), "diff": str(diff)},
        )
