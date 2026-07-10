"""Tests for type_consistency validator."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, EventType, ValidationStatus
from validation.rules.type_consistency import TypeConsistencyValidator


def test_warning_titulo_dividendo_conteudo_jcp(
    jcp_doc03_record: CorporateEventRecord,
) -> None:
    result = TypeConsistencyValidator().validate(jcp_doc03_record)
    assert result.status == ValidationStatus.WARNING
    assert result.details is not None
    assert result.details["rebaixar_confianca"] is True


def test_pass_aligned_types() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo=EventType.DIVIDENDO,
        divergencia_titulo_conteudo=False,
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.PASS


def test_warning_flag_even_if_types_match() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.JCP,
        tipo_declarado_no_titulo=EventType.JCP,
        divergencia_titulo_conteudo=True,
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.WARNING
