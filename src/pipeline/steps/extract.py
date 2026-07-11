"""Extract step - thin wrapper over extraction factory (native vs OCR)."""

from __future__ import annotations

from config.settings import get_settings
from extraction.factory import extract_fields
from llm.openai_provider import get_llm_provider
from pipeline.state import DocumentState


def extract(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: native or OCR by pdf_kind."""
    settings = get_settings()
    return extract_fields(
        state,
        provider=get_llm_provider(settings),
        settings=settings,
    )
