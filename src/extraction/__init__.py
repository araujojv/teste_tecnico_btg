"""Extraction package: ingest + native/OCR extract + factory."""

from extraction.extract import extract_native
from extraction.factory import extract_fields
from extraction.ingest import ingest_pdf
from extraction.ocr import extract_ocr

__all__ = ["ingest_pdf", "extract_native", "extract_ocr", "extract_fields"]
