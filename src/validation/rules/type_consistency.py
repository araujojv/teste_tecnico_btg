"""Validator: consistency between title-declared type and inferred type."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, ValidationResult, ValidationStatus
from validation.base import Validator


def _normalize_declared(declared: str) -> str:
    return declared.strip().casefold()


class TypeConsistencyValidator(Validator):
    """Title/content divergence -> warning (+ flag to lower confidence)."""

    @property
    def name(self) -> str:
        return "type_consistency"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        declared = record.tipo_declarado_no_titulo
        inferred = record.tipo_evento
        divergencia = record.divergencia_titulo_conteudo

        if declared is None and inferred is None:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message="tipo_evento and tipo_declarado_no_titulo are missing.",
            )

        types_differ = (
            declared is not None
            and inferred is not None
            and _normalize_declared(declared) != inferred.value
        )
        if types_differ or divergencia:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message=(
                    f"Title/content divergence: declared={declared}, "
                    f"inferred={inferred}, flag={divergencia}."
                ),
                details={
                    "rebaixar_confianca": True,
                    "tipo_declarado_no_titulo": declared,
                    "tipo_evento": inferred.value if inferred else None,
                    "divergencia_titulo_conteudo": divergencia,
                },
            )

        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.PASS,
            message=(
                f"Type consistent: declared={declared}, inferred={inferred}."
            ),
        )
