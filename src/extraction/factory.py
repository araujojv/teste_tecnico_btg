"""Extraction strategy factory: native vs OCR by pdf_kind."""

from __future__ import annotations

from config.settings import Settings
from extraction.extract import extract_native
from extraction.ocr import extract_ocr
from llm.provider import LLMProvider
from pipeline.state import DocumentState, PdfKind


def extract_fields(
    state: DocumentState,
    provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> DocumentState:
    """
    Choose extraction strategy from pdf_kind.
    Native PDFs never go through multimodal (ADR multimodal cost).
    """
    if state.pdf_kind == PdfKind.NATIVE:
        return extract_native(state, provider=provider, settings=settings)
    if state.pdf_kind == PdfKind.SCANNED:
        return extract_ocr(state, provider=provider, settings=settings)
    raise ValueError(f"extract_fields: unknown pdf_kind={state.pdf_kind}")
