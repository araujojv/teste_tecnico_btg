"""Unit tests for OCR extraction helpers and factory (no LLM)."""

from __future__ import annotations

from extraction.extract import _evidence_for, to_corporate_event_record
from extraction.factory import extract_fields
from extraction.prompts import build_extraction_vision_user_content
from extraction.schemas import ExtractedField, ExtractionLLMOutput
from pipeline.state import DocumentState, PdfKind
from schemas.records import ExtractionMethod


def test_vision_user_content_has_one_image_per_page() -> None:
    images = ["aaa", "bbb", "ccc"]
    content = build_extraction_vision_user_content(images)
    image_parts = [p for p in content if p.get("type") == "image_url"]
    assert len(image_parts) == 3
    assert "base64,aaa" in image_parts[0]["image_url"]["url"]
    text_labels = [p["text"] for p in content if p.get("type") == "text"]
    assert any("PAGE 1" in t for t in text_labels)
    assert any("PAGE 3" in t for t in text_labels)


def test_evidence_for_ocr_uses_field_page() -> None:
    field = ExtractedField(value="0.10", snippet="R$ 0,10 por acao", page=2)
    ev = _evidence_for(
        field,
        typed_value=field.value,
        page_texts=[],
        method=ExtractionMethod.OCR,
    )
    assert ev is not None
    assert ev.method == ExtractionMethod.OCR
    assert ev.page == 2
    assert ev.snippet == "R$ 0,10 por acao"


def test_to_record_ocr_method_on_evidencias() -> None:
    llm_out = ExtractionLLMOutput(
        emissor=ExtractedField(value="Telecom Norte", snippet="Telecom Norte", page=1),
        valor_bruto=ExtractedField(value="0.25", snippet="0,25", page=1),
        data_com=ExtractedField(value="10/01/2026", snippet="10/01/2026", page=1),
    )
    record = to_corporate_event_record(
        llm_out,
        [],
        method=ExtractionMethod.OCR,
    )
    assert record.evidencias["emissor"].method == ExtractionMethod.OCR
    assert record.evidencias["valor_bruto"].method == ExtractionMethod.OCR
    assert record.evidencias["data_com"].page == 1


def test_factory_rejects_missing_pdf_kind() -> None:
    state = DocumentState(
        document_id="x",
        source_path="synthetic",
        pdf_kind=None,
    )
    try:
        extract_fields(state)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "pdf_kind" in str(exc)


def test_factory_ocr_requires_images() -> None:
    state = DocumentState(
        document_id="07",
        source_path="synthetic",
        pdf_kind=PdfKind.SCANNED,
        page_images_base64=[],
    )
    try:
        extract_fields(state)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "page_images_base64" in str(exc)


def test_classification_vision_content_image_count() -> None:
    from classification.prompts import build_classification_vision_user_content

    content = build_classification_vision_user_content(["img1", "img2"])
    assert sum(1 for p in content if p.get("type") == "image_url") == 2


def test_use_vision_classification_when_scanned_no_text() -> None:
    from classification.classifier import _use_vision_classification

    scanned = DocumentState(
        document_id="07",
        source_path="synthetic",
        pdf_kind=PdfKind.SCANNED,
        page_images_base64=["x"],
        page_texts=[""],
        full_text="",
    )
    assert _use_vision_classification(scanned) is True

    native = DocumentState(
        document_id="01",
        source_path="synthetic",
        pdf_kind=PdfKind.NATIVE,
        page_texts=["texto"],
        full_text="texto",
    )
    assert _use_vision_classification(native) is False
