"""Integration test: native extraction on doc 01 (calls OpenAI)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.settings import get_settings
from extraction.extract import extract_native, find_page, parse_brazilian_date, parse_decimal
from extraction.ingest import ingest_pdf
from llm.openai_provider import get_llm_provider
from pipeline.state import PdfKind
from schemas.records import EventType, ExtractionMethod

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOC_01 = PROJECT_ROOT / "documents" / "01_energetica_vale_tiete_dividendo.pdf"


def test_find_page_assigns_1based_index() -> None:
    pages = ["alpha beta", "ISIN BRTIETACNOR3 ticker TIET3"]
    assert find_page("BRTIETACNOR3", pages) == 2
    assert find_page("missing", pages) is None


def test_parse_helpers() -> None:
    assert parse_brazilian_date("28/05/2026") is not None
    assert parse_decimal("0,4275") == parse_decimal("0.4275")


@pytest.mark.llm
def test_extract_doc01_emissor_isin_tipo() -> None:
    if not DOC_01.is_file():
        pytest.skip(f"missing {DOC_01.name}")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    settings = get_settings()
    state = ingest_pdf(DOC_01, settings)
    assert state.pdf_kind == PdfKind.NATIVE

    provider = get_llm_provider(settings)
    try:
        extracted = extract_native(state, provider=provider, settings=settings)
    except Exception as exc:  # noqa: BLE001 - surface billing/auth as skip
        message = str(exc).casefold()
        if "billing_not_active" in message or "insufficient_quota" in message:
            pytest.skip(f"OpenAI account unavailable for LLM test: {exc}")
        raise

    assert extracted.record is not None
    record = extracted.record
    assert record.emissor is not None
    assert "vale" in record.emissor.casefold() or "energ" in record.emissor.casefold()
    assert record.isin == "BRTIETACNOR3"
    assert record.tipo_evento == EventType.DIVIDENDO

    assert "isin" in record.evidencias
    isin_ev = record.evidencias["isin"]
    assert isin_ev.method == ExtractionMethod.NATIVE
    assert isin_ev.page == 1
    assert isin_ev.snippet
