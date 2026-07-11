"""LLM integration tests for event-type classification."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from classification.classifier import LLMEventClassifier
from config.settings import get_settings
from extraction.ingest import ingest_pdf
from llm.openai_provider import get_llm_provider
from schemas.records import EventType

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOC_01 = PROJECT_ROOT / "documents" / "01_energetica_vale_tiete_dividendo.pdf"
DOC_03 = PROJECT_ROOT / "documents" / "03_siderurgica_paranaense_proventos.pdf"


def _classify_doc(path: Path):
    if not path.is_file():
        pytest.skip(f"missing {path.name}")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    settings = get_settings()
    state = ingest_pdf(path, settings)
    classifier = LLMEventClassifier(
        provider=get_llm_provider(settings),
        settings=settings,
    )
    try:
        return classifier.classify(state)
    except Exception as exc:  # noqa: BLE001
        message = str(exc).casefold()
        if "billing_not_active" in message or "insufficient_quota" in message:
            pytest.skip(f"OpenAI account unavailable for LLM test: {exc}")
        raise


@pytest.mark.llm
def test_classify_doc01_dividendo_sem_divergencia() -> None:
    result = _classify_doc(DOC_01)
    assert result.record is not None
    assert result.record.tipo_evento == EventType.DIVIDENDO
    assert result.record.divergencia_titulo_conteudo is False
    assert result.classification_raw is not None
    assert result.classification_raw.get("raciocinio")


@pytest.mark.llm
def test_classify_doc03_jcp_com_divergencia() -> None:
    result = _classify_doc(DOC_03)
    assert result.record is not None
    assert result.record.tipo_evento == EventType.JCP
    assert result.record.divergencia_titulo_conteudo is True
    assert result.classification_raw is not None
    assert result.classification_raw.get("raciocinio")
