"""Tests for PDF ingest and native/scanned detection - no LLM calls."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import Settings, get_settings
from extraction.ingest import (
    classify_pdf_kind,
    compute_densities,
    ingest_pdf,
)
from pipeline.state import PdfKind
from pipeline.steps.ingest import ingest as ingest_step
from pipeline.state import DocumentState

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"

DOC_01 = DOCUMENTS_DIR / "01_energetica_vale_tiete_dividendo.pdf"
DOC_07 = DOCUMENTS_DIR / "07_telecom_norte_jcp_SCAN.pdf"


@pytest.fixture
def documents_dir() -> Path:
    if not DOCUMENTS_DIR.is_dir():
        pytest.skip(f"documents/ not found at {DOCUMENTS_DIR}")
    return DOCUMENTS_DIR


@pytest.fixture
def settings() -> Settings:
    return get_settings()


def test_compute_densities_mean() -> None:
    densities, mean = compute_densities(["abc", "", "de"])
    assert densities == [3.0, 0.0, 2.0]
    assert mean == pytest.approx(5.0 / 3.0)


def test_classify_pdf_kind_threshold() -> None:
    assert classify_pdf_kind(1378.0, 50.0) == PdfKind.NATIVE
    assert classify_pdf_kind(0.0, 50.0) == PdfKind.SCANNED
    assert classify_pdf_kind(49.9, 50.0) == PdfKind.SCANNED
    assert classify_pdf_kind(50.0, 50.0) == PdfKind.NATIVE


def test_doc01_classified_as_native(documents_dir: Path, settings: Settings) -> None:
    if not DOC_01.is_file():
        pytest.skip(f"missing {DOC_01.name}")

    state = ingest_pdf(DOC_01, settings)

    assert state.pdf_kind == PdfKind.NATIVE
    assert state.page_images_base64 == []
    assert state.mean_char_density >= settings.text_density_threshold
    assert state.full_text.strip() != ""
    assert state.page_count >= 1
    assert state.audit_trail
    assert "kind=native" in state.audit_trail[-1]


def test_doc07_classified_as_scanned(documents_dir: Path, settings: Settings) -> None:
    if not DOC_07.is_file():
        pytest.skip(f"missing {DOC_07.name}")

    state = ingest_pdf(DOC_07, settings)

    assert state.pdf_kind == PdfKind.SCANNED
    assert state.mean_char_density < settings.text_density_threshold
    assert state.page_count >= 1
    assert len(state.page_images_base64) == state.page_count
    # PNG base64 should be non-empty for each page
    for image_b64 in state.page_images_base64:
        assert len(image_b64) > 100
    assert "kind=scanned" in state.audit_trail[-1]


def test_ingest_step_preserves_document_id(
    documents_dir: Path, settings: Settings
) -> None:
    if not DOC_01.is_file():
        pytest.skip(f"missing {DOC_01.name}")

    initial = DocumentState(
        document_id="custom-id-01",
        source_path=str(DOC_01),
        audit_trail=["pre-ingest"],
    )
    # Ensure settings threshold is loaded (step uses get_settings)
    assert settings.text_density_threshold == get_settings().text_density_threshold

    result = ingest_step(initial)
    assert result.document_id == "custom-id-01"
    assert result.pdf_kind == PdfKind.NATIVE
    assert result.audit_trail[0] == "pre-ingest"
    assert any(entry.startswith("ingest:") for entry in result.audit_trail)
