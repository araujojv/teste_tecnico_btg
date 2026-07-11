"""LLM integration: full pipeline on doc 01 (auto_approve) and doc 08 (human_review)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.settings import get_settings
from pipeline.orchestrator import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOC_01 = PROJECT_ROOT / "documents" / "01_energetica_vale_tiete_dividendo.pdf"
DOC_08 = PROJECT_ROOT / "documents" / "08_construtora_horizonte_bonificacao.pdf"


def _run(path: Path):
    if not path.is_file():
        pytest.skip(f"missing {path.name}")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    try:
        return run_pipeline(path, get_settings())
    except Exception as exc:  # noqa: BLE001
        message = str(exc).casefold()
        if "billing_not_active" in message or "insufficient_quota" in message:
            pytest.skip(f"OpenAI account unavailable: {exc}")
        raise


@pytest.mark.llm
def test_pipeline_doc01_auto_approve() -> None:
    state = _run(DOC_01)
    assert state.record is not None
    assert state.route_decision == "auto_approve"
    golden = next(r for r in state.validation_results if r.rule == "golden_records")
    assert golden.status.value == "pass"


@pytest.mark.llm
def test_pipeline_doc08_human_review_golden() -> None:
    state = _run(DOC_08)
    assert state.record is not None
    assert state.route_decision == "human_review"
    assert any("golden_records" in reason for reason in state.route_reasons)
    golden = next(r for r in state.validation_results if r.rule == "golden_records")
    assert golden.status.value == "fail"
