"""Validator: title/content type consistency via classifier flag only."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, ValidationResult, ValidationStatus
from validation.base import Validator


class TypeConsistencyValidator(Validator):
    """
    Relies on divergencia_titulo_conteudo from the classifier (which read the doc).
    Does not compare tipo_declarado_no_titulo vs tipo_evento strings.
    """

    @property
    def name(self) -> str:
        return "type_consistency"

    def validate(self, record: CorporateEventRecord) -> ValidationResult:
        divergencia = record.divergencia_titulo_conteudo

        # Classification has not run yet.
        if divergencia is None:
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.NOT_APPLICABLE,
                message="Classification not run; divergencia_titulo_conteudo is unset.",
            )

        if divergencia:
            raciocinio = record.raciocinio_classificacao or "(raciocinio ausente)"
            return ValidationResult(
                rule=self.name,
                status=ValidationStatus.WARNING,
                message=(
                    "Title/content divergence flagged by classifier. "
                    f"Raciocinio: {raciocinio}"
                ),
                details={
                    "rebaixar_confianca": True,
                    "tipo_declarado_no_titulo": record.tipo_declarado_no_titulo,
                    "tipo_evento": (
                        record.tipo_evento.value if record.tipo_evento else None
                    ),
                    "divergencia_titulo_conteudo": True,
                    "raciocinio": raciocinio,
                },
            )

        return ValidationResult(
            rule=self.name,
            status=ValidationStatus.PASS,
            message=(
                "No title/content divergence "
                f"(tipo_declarado_no_titulo={record.tipo_declarado_no_titulo}, "
                f"tipo_evento={record.tipo_evento})."
            ),
        )
