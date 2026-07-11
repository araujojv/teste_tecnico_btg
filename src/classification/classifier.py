"""Event type classifier: interface + LLM implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from classification.prompts import (
    CLASSIFICATION_SYSTEM,
    build_classification_user_prompt,
)
from classification.schemas import ClassificationLLMOutput
from config.settings import Settings, get_settings
from llm.openai_provider import get_llm_provider
from llm.provider import LLMProvider
from pipeline.state import DocumentState, append_audit
from schemas.records import CorporateEventRecord


class EventClassifier(ABC):
    """Interface: classify event type from document state."""

    @abstractmethod
    def classify(self, state: DocumentState) -> DocumentState:
        ...


class LLMEventClassifier(EventClassifier):
    """LLM classifier using CLASSIFICATION_MODEL via LLMProvider.parse."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or get_llm_provider(self._settings)

    def classify(self, state: DocumentState) -> DocumentState:
        if not state.page_texts and not state.full_text:
            raise ValueError(
                "classify requires ingested text (page_texts or full_text)"
            )

        page_texts = state.page_texts or [state.full_text]
        messages = [
            {"role": "system", "content": CLASSIFICATION_SYSTEM},
            {
                "role": "user",
                "content": build_classification_user_prompt(page_texts),
            },
        ]
        result = self._provider.parse(
            messages,
            ClassificationLLMOutput,
            model=self._settings.classification_model,
        )

        base_record = state.record or CorporateEventRecord()
        record = base_record.model_copy(
            update={
                "tipo_evento": result.tipo_evento,
                "tipo_declarado_no_titulo": result.tipo_declarado_no_titulo,
                "divergencia_titulo_conteudo": result.divergencia_titulo_conteudo,
            }
        )

        updated = state.model_copy(
            update={
                "record": record,
                "classification_raw": result.model_dump(mode="json"),
            }
        )
        evidencias_preview = " | ".join(result.evidencias_do_documento[:5])
        return append_audit(
            updated,
            (
                f"classify: model={self._settings.classification_model}, "
                f"tipo_evento={result.tipo_evento.value}, "
                f"divergencia={result.divergencia_titulo_conteudo}, "
                f"raciocinio={result.raciocinio}; "
                f"evidencias={evidencias_preview}"
            ),
        )


def get_event_classifier(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> EventClassifier:
    cfg = settings or get_settings()
    return LLMEventClassifier(provider=provider, settings=cfg)
