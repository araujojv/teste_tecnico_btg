"""Classify step - thin wrapper over LLMEventClassifier."""

from __future__ import annotations

from classification.classifier import get_event_classifier
from config.settings import get_settings
from llm.openai_provider import get_llm_provider
from pipeline.state import DocumentState


def classify(state: DocumentState) -> DocumentState:
    """(DocumentState) -> DocumentState: classify event type from content."""
    settings = get_settings()
    classifier = get_event_classifier(
        settings=settings,
        provider=get_llm_provider(settings),
    )
    return classifier.classify(state)
