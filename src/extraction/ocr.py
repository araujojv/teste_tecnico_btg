"""OCR/vision extraction for scanned PDFs (multimodal - ADR multimodal cost)."""

from __future__ import annotations

from config.settings import Settings, get_settings
from extraction.extract import (
    filled_field_names,
    to_corporate_event_record,
)
from extraction.prompts import (
    EXTRACTION_OCR_SYSTEM_EXTRA,
    EXTRACTION_SYSTEM,
    build_extraction_vision_user_content,
)
from extraction.schemas import ExtractionLLMOutput
from llm.openai_provider import get_llm_provider
from llm.provider import LLMProvider
from pipeline.state import DocumentState, PdfKind, append_audit
from schemas.records import ExtractionMethod


def extract_ocr(
    state: DocumentState,
    provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> DocumentState:
    """Fill state.record from scanned page images via vision structured output."""
    if state.pdf_kind != PdfKind.SCANNED:
        raise ValueError(
            f"extract_ocr requires pdf_kind=scanned, got {state.pdf_kind}"
        )
    if not state.page_images_base64:
        raise ValueError("extract_ocr requires non-empty page_images_base64")

    cfg = settings or get_settings()
    llm = provider or get_llm_provider(cfg)

    messages = [
        {
            "role": "system",
            "content": EXTRACTION_SYSTEM + "\n" + EXTRACTION_OCR_SYSTEM_EXTRA,
        },
        {
            "role": "user",
            "content": build_extraction_vision_user_content(
                state.page_images_base64
            ),
        },
    ]
    llm_out = llm.parse(
        messages,
        ExtractionLLMOutput,
        model=cfg.vision_model,
    )
    # Scanned docs have empty page_texts; page comes from ExtractedField.page.
    record = to_corporate_event_record(
        llm_out,
        state.page_texts or [],
        method=ExtractionMethod.OCR,
    )
    filled = filled_field_names(record)
    updated = state.model_copy(update={"record": record})
    return append_audit(
        updated,
        (
            f"extract_ocr: model={cfg.vision_model}, "
            f"pages={len(state.page_images_base64)}, "
            f"fields={filled}, evidencias={len(record.evidencias)}"
        ),
    )
