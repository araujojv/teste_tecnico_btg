"""Extract step - thin wrapper over extraction.extract_native."""

from __future__ import annotations

from config.settings import get_settings
from extraction.extract import extract_native
from llm.openai_provider import get_llm_provider
from pipeline.state import DocumentState, PdfKind


def extract(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: native extraction only (step 3)."""
    if state.pdf_kind == PdfKind.SCANNED:
        raise NotImplementedError(
            "Scanned/multimodal extraction is implemented in step 6"
        )
    settings = get_settings()
    return extract_native(
        state,
        provider=get_llm_provider(settings),
        settings=settings,
    )
