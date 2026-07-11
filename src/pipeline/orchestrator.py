"""Pipeline orchestrator: chains ingest -> extract -> classify -> validate -> score -> route."""

from __future__ import annotations

from pathlib import Path

from classification.classifier import get_event_classifier
from config.settings import Settings, get_settings
from extraction.factory import extract_fields
from extraction.ingest import ingest_pdf
from llm.openai_provider import get_llm_provider
from pipeline.state import DocumentState
from pipeline.steps.route import route
from pipeline.steps.score import score
from pipeline.steps.validate import validate
from repositories.golden_records import GoldenRecordsRepository


def run_pipeline(
    path: Path | str,
    settings: Settings | None = None,
    *,
    skip_llm: bool = False,
    repository: GoldenRecordsRepository | None = None,
) -> DocumentState:
    """
    Full pipeline for a single PDF.
    skip_llm=True only runs ingest (for tests that inject a synthetic record).
    """
    cfg = settings or get_settings()
    state = ingest_pdf(path, cfg)

    if skip_llm:
        return state

    provider = get_llm_provider(cfg)
    state = extract_fields(state, provider=provider, settings=cfg)
    classifier = get_event_classifier(settings=cfg, provider=provider)
    state = classifier.classify(state)

    state = validate(state, repository=repository)
    state = score(state)
    state = route(state)
    return state
