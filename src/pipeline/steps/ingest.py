"""Ingest step - thin wrapper over extraction.ingest."""

from __future__ import annotations

from pathlib import Path

from config.settings import get_settings
from extraction.ingest import ingest_pdf
from pipeline.state import DocumentState


def ingest(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: fill text/kind/images from source_path."""
    settings = get_settings()
    ingested = ingest_pdf(
        Path(state.source_path),
        settings,
        document_id=state.document_id,
    )
    # Preserve any pre-existing audit entries from upstream.
    if state.audit_trail:
        return ingested.model_copy(
            update={"audit_trail": [*state.audit_trail, *ingested.audit_trail]}
        )
    return ingested
