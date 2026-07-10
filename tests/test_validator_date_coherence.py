"""Tests for date_coherence validator."""

from __future__ import annotations

from datetime import date

from schemas.records import CorporateEventRecord, ValidationStatus
from validation.rules.date_coherence import DateCoherenceValidator


def test_pass_coherent_dates(known_issuer_record: CorporateEventRecord) -> None:
    result = DateCoherenceValidator().validate(known_issuer_record)
    assert result.status == ValidationStatus.PASS


def test_warning_pagamento_ausente_declarada() -> None:
    record = CorporateEventRecord(
        data_aprovacao=date(2024, 1, 1),
        data_com=date(2024, 1, 10),
        data_ex=date(2024, 1, 11),
        data_pagamento=None,
        data_pagamento_ausente_declarada=True,
    )
    result = DateCoherenceValidator().validate(record)
    assert result.status == ValidationStatus.WARNING
    assert "absent" in result.message.lower()


def test_fail_incoherent_order() -> None:
    record = CorporateEventRecord(
        data_aprovacao=date(2024, 3, 1),
        data_com=date(2024, 3, 20),
        data_ex=date(2024, 3, 15),  # ex before com
        data_pagamento=date(2024, 4, 1),
    )
    result = DateCoherenceValidator().validate(record)
    assert result.status == ValidationStatus.FAIL


def test_fail_pagamento_before_ex() -> None:
    record = CorporateEventRecord(
        data_com=date(2024, 3, 10),
        data_ex=date(2024, 3, 12),
        data_pagamento=date(2024, 3, 11),
    )
    result = DateCoherenceValidator().validate(record)
    assert result.status == ValidationStatus.FAIL
