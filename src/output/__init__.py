"""Output package: final JSON records + exceptions report."""

from output.exceptions_report import build_exceptions_report, write_exceptions_report
from output.record_builder import (
    PIPELINE_VERSION,
    build_document_output,
    write_document_json,
)

__all__ = [
    "PIPELINE_VERSION",
    "build_document_output",
    "write_document_json",
    "build_exceptions_report",
    "write_exceptions_report",
]
