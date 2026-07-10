"""Shared fixtures - no LLM calls."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from repositories.golden_records import GoldenRecordsRepository
from schemas.records import CorporateEventRecord, EventType

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_CSV = PROJECT_ROOT / "golden_records" / "golden records.csv"


@pytest.fixture
def golden_csv_path() -> Path:
    return GOLDEN_CSV


@pytest.fixture
def repository(golden_csv_path: Path) -> GoldenRecordsRepository:
    return GoldenRecordsRepository(golden_csv_path)


@pytest.fixture
def known_issuer_record() -> CorporateEventRecord:
    """Issuer present in golden_records (Energetica Vale do Tiete)."""
    return CorporateEventRecord(
        emissor="Energetica Vale do Tiete S.A.",
        cnpj="12.345.678/0001-90",
        isin="BRTIETACNOR3",
        ticker="TIET3",
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=False,
        data_aprovacao=date(2024, 3, 1),
        data_com=date(2024, 3, 15),
        data_ex=date(2024, 3, 18),
        data_pagamento=date(2024, 4, 10),
        valor_bruto=Decimal("0.50"),
        valor_liquido=Decimal("0.50"),
        aliquota_ir=Decimal("0"),
        moeda="BRL",
    )


@pytest.fixture
def unknown_issuer_record() -> CorporateEventRecord:
    """Doc 08 - Construtora Horizonte, absent from golden_records."""
    return CorporateEventRecord(
        emissor="Construtora Horizonte S.A.",
        cnpj="00.000.000/0001-00",
        isin="BRCNHZACNOR5",
        ticker="CNHZ3",
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="dividendo",
    )


@pytest.fixture
def jcp_doc03_record() -> CorporateEventRecord:
    """Doc 03 - title dividend, content JCP; gross/net sanity check."""
    return CorporateEventRecord(
        emissor="Companhia Siderurgica Paranaense S.A.",
        cnpj="76.543.210/0001-12",
        isin="BRCSPRACNOR1",
        ticker="CSPR3",
        tipo_evento=EventType.JCP,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=True,
        data_aprovacao=date(2024, 1, 10),
        data_com=date(2024, 1, 20),
        data_ex=date(2024, 1, 21),
        data_pagamento=date(2024, 2, 15),
        valor_bruto=Decimal("0.09215"),
        valor_liquido=Decimal("0.07602375"),
        # Fraction: 0.175 = 17.5% IRRF
        aliquota_ir=Decimal("0.175"),
        moeda="BRL",
    )
