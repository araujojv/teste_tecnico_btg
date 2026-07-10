"""Pipeline orchestrator - stub."""

from __future__ import annotations

from pipeline.state import DocumentState


def run_pipeline(state: DocumentState) -> DocumentState:
    """Chains the steps. Implemented in later steps."""
    raise NotImplementedError
