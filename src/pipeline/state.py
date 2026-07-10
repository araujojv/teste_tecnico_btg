"""DocumentState - stub (implemented in later steps)."""

from __future__ import annotations

from pydantic import BaseModel


class DocumentState(BaseModel):
    """Document state in the pipeline. Expanded in later steps."""

    document_id: str
    source_path: str
    audit_trail: list[str] = []
