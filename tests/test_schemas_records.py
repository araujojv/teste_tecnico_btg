"""Tests for CorporateEventRecord schema constraints."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.records import (
    CorporateEventRecord,
    EventType,
    ExtractionMethod,
    FieldEvidence,
)
from validation.rules.gross_net_consistency import GrossNetConsistencyValidator
from schemas.records import ValidationStatus


def test_evidencias_accepts_model_field_keys() -> None:
    record = CorporateEventRecord(
        isin="US0378331005",
        evidencias={
            "isin": FieldEvidence[str](
                value="US0378331005",
                snippet="ISIN US0378331005",
                page=1,
                method=ExtractionMethod.NATIVE,
            ),
            "proporcao": FieldEvidence[str](
                value="1:10",
                snippet="grupamento na proporcao de 1:10",
                page=1,
                method=ExtractionMethod.NATIVE,
            ),
        },
    )
    assert "isin" in record.evidencias
    assert record.evidencias["proporcao"].value == "1:10"


def test_evidencias_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CorporateEventRecord(
            evidencias={
                "campo_inventado": FieldEvidence[str](value="x"),
            }
        )
    assert "campo_inventado" in str(exc_info.value)


def test_moeda_defaults_to_none() -> None:
    record = CorporateEventRecord()
    assert record.moeda is None


def test_aliquota_ir_is_decimal_fraction_not_percent() -> None:
    """aliquota_ir uses fraction: 0.175 means 17.5%, not 17.5."""
    record = CorporateEventRecord(
        tipo_evento=EventType.JCP,
        valor_bruto=Decimal("0.09215"),
        valor_liquido=Decimal("0.07602375"),
        aliquota_ir=Decimal("0.175"),
    )
    assert record.aliquota_ir == Decimal("0.175")
    assert record.aliquota_ir < Decimal("1")

    # Using 17.5 (percent) would break bruto/liquido consistency.
    wrong = CorporateEventRecord(
        tipo_evento=EventType.JCP,
        valor_bruto=Decimal("0.09215"),
        valor_liquido=Decimal("0.07602375"),
        aliquota_ir=Decimal("17.5"),
    )
    result = GrossNetConsistencyValidator().validate(wrong)
    assert result.status == ValidationStatus.FAIL

    result_ok = GrossNetConsistencyValidator().validate(record)
    assert result_ok.status == ValidationStatus.PASS
