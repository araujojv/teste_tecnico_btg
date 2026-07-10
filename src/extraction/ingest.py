"""PDF ingest: text extraction, native/scanned detection, optional page images."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from config.settings import Settings, get_settings
from pipeline.state import DocumentState, PdfKind, append_audit


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-based
    text: str


def extract_pages(path: Path | str) -> list[PageText]:
    """Extract plain text per page via pdfplumber (no LLM)."""
    pdf_path = Path(path)
    pages: list[PageText] = []
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=index, text=text))
    return pages


def compute_densities(page_texts: list[str]) -> tuple[list[float], float]:
    """Return per-page char counts and their mean (0.0 if no pages)."""
    densities = [float(len(text)) for text in page_texts]
    if not densities:
        return [], 0.0
    mean = sum(densities) / len(densities)
    return densities, mean


def classify_pdf_kind(mean_density: float, threshold: float) -> PdfKind:
    """Below threshold => scanned; otherwise native."""
    if mean_density < threshold:
        return PdfKind.SCANNED
    return PdfKind.NATIVE


def pages_to_base64(path: Path | str, resolution: int) -> list[str]:
    """Rasterize each page to PNG base64 via pdfplumber.to_image (scanned only)."""
    pdf_path = Path(path)
    images: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            rendered = page.to_image(resolution=resolution)
            buffer = io.BytesIO()
            rendered.original.save(buffer, format="PNG")
            images.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
    return images


def _document_id_from_path(path: Path) -> str:
    return path.stem


def ingest_pdf(
    path: Path | str,
    settings: Settings | None = None,
    *,
    document_id: str | None = None,
) -> DocumentState:
    """Ingest a PDF into DocumentState (text + kind; images only if scanned)."""
    cfg = settings or get_settings()
    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = extract_pages(pdf_path)
    page_texts = [page.text for page in pages]
    densities, mean_density = compute_densities(page_texts)
    kind = classify_pdf_kind(mean_density, cfg.text_density_threshold)

    page_images: list[str] = []
    if kind == PdfKind.SCANNED:
        page_images = pages_to_base64(pdf_path, cfg.scan_image_resolution)

    state = DocumentState(
        document_id=document_id or _document_id_from_path(pdf_path),
        source_path=str(pdf_path.resolve()),
        pdf_kind=kind,
        page_count=len(pages),
        page_texts=page_texts,
        full_text="\n\n".join(page_texts),
        char_density_per_page=densities,
        mean_char_density=mean_density,
        page_images_base64=page_images,
    )
    return append_audit(
        state,
        (
            f"ingest: kind={kind.value}, pages={len(pages)}, "
            f"mean_density={mean_density:.2f}, "
            f"threshold={cfg.text_density_threshold}, "
            f"images={len(page_images)}"
        ),
    )
