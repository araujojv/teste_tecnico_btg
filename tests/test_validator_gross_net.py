"""Tests for gross_net_consistency validator."""

from __future__ import annotations

from decimal import Decimal

from schemas.records import CorporateEventRecord, EventType, ValidationStatus
from validation.rules.gross_net_consistency import GrossNetConsistencyValidator


def test_pass_doc03_math(jcp_doc03_record: CorporateEventRecord) -> None:
    result = GrossNetConsistencyValidator().validate(jcp_doc03_record)
    assert result.status == ValidationStatus.PASS
    # Sanity check: 0.09215 * (1 - 0.175) = 0.07602375
    expected = Decimal("0.09215") * (Decimal("1") - Decimal("0.175"))
    assert expected == Decimal("0.07602375")


def test_fail_inconsistent_values() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.JCP,
        valor_bruto=Decimal("1.00"),
        valor_liquido=Decimal("0.50"),
        aliquota_ir=Decimal("0.175"),
    )
    result = GrossNetConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.FAIL


def test_not_applicable_grupamento() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.GRUPAMENTO,
        valor_bruto=Decimal("1.00"),
        valor_liquido=Decimal("1.00"),
        aliquota_ir=Decimal("0"),
    )
    result = GrossNetConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.NOT_APPLICABLE


def test_not_applicable_bonificacao() -> None:
    record = CorporateEventRecord(tipo_evento=EventType.BONIFICACAO)
    result = GrossNetConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.NOT_APPLICABLE


def test_warning_missing_fields() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.DIVIDENDO,
        valor_bruto=Decimal("1.00"),
    )
    result = GrossNetConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.WARNING
